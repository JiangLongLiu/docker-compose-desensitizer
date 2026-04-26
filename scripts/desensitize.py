#!/usr/bin/env python3
"""Docker Compose 文件脱敏工具 - 自动扫描并脱敏 docker-compose.yml 中的硬编码敏感信息"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from ruamel.yaml import YAML
except ImportError:
    print("错误: 需要安装 ruamel.yaml 库。请运行: pip install ruamel.yaml")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认敏感词正则表达式
DEFAULT_KEYWORDS = r'(?i)(password|secret|token|api_key|auth|credential|private_key|access_key|connstr|db_pass)'

class DockerComposeDesensitizer:
    """Docker Compose 文件脱敏器类"""
    
    def __init__(self, file_path: str, output_path: Optional[str] = None, 
                 dry_run: bool = False, keywords: str = DEFAULT_KEYWORDS,
                 backup: bool = False, report_json: Optional[str] = None):
        self.file_path = Path(file_path)
        self.output_path = Path(output_path) if output_path else self.file_path
        self.dry_run = dry_run
        self.keywords_pattern = re.compile(keywords)
        self.backup = backup
        self.report_json = report_json
        self.changes = []
        
        # 验证输入文件
        if not self.file_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.file_path}")
            
        # 初始化 YAML 解析器
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 1024
        self.yaml.explicit_start = True
        self.yaml.default_flow_style = False
    
    def load_yaml(self) -> Dict[str, Any]:
        """加载 YAML 文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = self.yaml.load(f)
            logger.info(f"成功加载文件: {self.file_path}")
            return data
        except Exception as e:
            logger.error(f"加载 YAML 文件失败: {e}")
            raise
    
    def is_sensitive_key(self, key: str) -> bool:
        """检查键名是否匹配敏感词模式"""
        return bool(self.keywords_pattern.search(key))
    
    def is_safe_to_replace(self, value: Any, key: str) -> bool:
        """检查值是否安全替换"""
        # 跳过空值
        if value is None:
            return False
            
        # 跳过已经是环境变量格式的
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            return False
            
        # 跳过明显的非凭据值
        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val in ['true', 'false', 'yes', 'no', 'on', 'off', 
                           'nginx', 'apache', 'mysql', 'postgres', 'redis',
                           'localhost', '127.0.0.1', '0.0.0.0']:
                return False
                
        # 跳过非字符串类型（除了可能是密码的数字）
        if not isinstance(value, (str, int, float)):
            return False
            
        # 检查键名是否匹配敏感词
        if self.is_sensitive_key(key):
            return True
            
        # 额外检查：对于包含 URL 格式的字符串，检查其中是否包含密码
        if isinstance(value, str) and ('://' in value):
            # 检查是否是常见的数据库/缓存连接字符串格式
            url_patterns = [
                r'postgresql://', r'postgres://', r'mysql://', r'mariadb://',
                r'redis://', r'mongodb://', r'amqp://', r'ftp://', r'sftp://'
            ]
            for pattern in url_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    # 检查 URL 中是否包含密码（格式通常为 protocol://user:password@host 或 protocol://:password@host）
                    if re.search(r'://[^:@]*:[^@]+@', value):
                        return True
                        
        return False
    
    def replace_with_env_var(self, key: str, original_value: Any) -> str:
        """将值替换为环境变量格式"""
        env_var_name = key.upper()
        return f"${{{env_var_name}}}"
    
    def process_environment_dict(self, env_dict: Dict[str, Any], parent_key: str = "environment") -> Dict[str, Any]:
        """处理字典格式的 environment 字段"""
        result = {}
        for key, value in env_dict.items():
            if self.is_safe_to_replace(value, key):
                new_value = self.replace_with_env_var(key, value)
                self.changes.append({
                    'path': f"{parent_key}.{key}",
                    'original': str(value)[:20] + "..." if len(str(value)) > 20 else str(value),
                    'replacement': new_value,
                    'status': 'replaced'
                })
                result[key] = new_value
            else:
                result[key] = value
        return result
    
    def process_environment_list(self, env_list: List[str], parent_key: str = "environment") -> List[str]:
        """处理列表格式的 environment 字段"""
        result = []
        for item in env_list:
            if '=' in item:
                key, value = item.split('=', 1)
                if self.is_safe_to_replace(value, key):
                    new_value = self.replace_with_env_var(key, value)
                    self.changes.append({
                        'path': f"{parent_key}.{key}",
                        'original': str(value)[:20] + "..." if len(str(value)) > 20 else str(value),
                        'replacement': new_value,
                        'status': 'replaced'
                    })
                    result.append(f"{key}={new_value}")
                else:
                    result.append(item)
            else:
                result.append(item)
        return result
    
    def process_service(self, service_data: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """处理单个服务的数据"""
        result = {}
        for key, value in service_data.items():
            if key == 'environment':
                if isinstance(value, dict):
                    result[key] = self.process_environment_dict(value, f"services.{service_name}.environment")
                elif isinstance(value, list):
                    result[key] = self.process_environment_list(value, f"services.{service_name}.environment")
                else:
                    result[key] = value
            elif self.is_safe_to_replace(value, key):
                # 检查是否是包含密码的 URL
                if isinstance(value, str) and '://' in value and re.search(r'://[^:]+:[^@]+@', value):
                    # 对于包含密码的 URL，将整个 URL 替换为环境变量
                    new_value = self.replace_with_env_var(key, value)
                    self.changes.append({
                        'path': f"services.{service_name}.{key}",
                        'original': str(value)[:20] + "..." if len(str(value)) > 20 else str(value),
                        'replacement': new_value,
                        'status': 'replaced'
                    })
                    result[key] = new_value
                else:
                    new_value = self.replace_with_env_var(key, value)
                    self.changes.append({
                        'path': f"services.{service_name}.{key}",
                        'original': str(value)[:20] + "..." if len(str(value)) > 20 else str(value),
                        'replacement': new_value,
                        'status': 'replaced'
                    })
                    result[key] = new_value
            else:
                result[key] = value
        return result
    
    def process_yaml(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理整个 YAML 数据"""
        result = {}
        for key, value in data.items():
            if key == 'services' and isinstance(value, dict):
                processed_services = {}
                for service_name, service_data in value.items():
                    if isinstance(service_data, dict):
                        processed_services[service_name] = self.process_service(service_data, service_name)
                    else:
                        processed_services[service_name] = service_data
                result[key] = processed_services
            else:
                result[key] = value
        return result
    
    def validate_yaml(self, data: Dict[str, Any]) -> bool:
        """验证 YAML 数据有效性"""
        try:
            # 尝试将数据转换回字符串以验证格式
            import io
            string_stream = io.StringIO()
            self.yaml.dump(data, string_stream)
            logger.info("YAML 格式验证通过")
            return True
        except Exception as e:
            logger.error(f"YAML 格式验证失败: {e}")
            return False
    
    def save_yaml(self, data: Dict[str, Any]) -> bool:
        """保存 YAML 文件"""
        try:
            if self.dry_run:
                logger.info("Dry run 模式：不会实际写入文件")
                # 在 dry-run 模式下，打印到标准输出
                import io
                string_stream = io.StringIO()
                self.yaml.dump(data, string_stream)
                print("\n=== Dry Run 输出 ===")
                print(string_stream.getvalue())
                print("==================")
                return True
            
            # 如果输出路径就是原文件路径，需要先备份原文件
            if self.output_path == self.file_path:
                # 生成带完整时间戳的备份文件名 (格式: YYYYMMddHHmmss)
                from datetime import datetime
                timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
                backup_path = self.file_path.parent / f"{self.file_path.name}.backup-{timestamp_str}.txt"
                
                # 重命名原文件为备份文件
                shutil.copy2(self.file_path, backup_path)
                logger.info(f"已备份原文件到: {backup_path}")
            
            # 写入脱敏后的文件
            with open(self.output_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)
            
            logger.info(f"成功保存文件: {self.output_path}")
            
            # 自动生成 .env 文件
            self.generate_env_file()
            
            return True
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return False
    
    def generate_env_file(self) -> None:
        """生成 .env 文件"""
        try:
            if not self.changes:
                logger.info("没有需要生成 .env 文件的变更")
                return
            
            # 确定 .env 文件路径（与 docker-compose.yml 同一目录）
            env_file_path = self.file_path.parent / '.env'
            
            # 从变更中提取环境变量
            env_vars = {}
            for change in self.changes:
                env_var_name = change['replacement'].strip('${}')
                original_value = change['original']
                
                # 如果原值被截断，需要从原始 YAML 中获取完整值
                if original_value.endswith('...'):
                    # 从原始文件重新读取完整值
                    full_value = self.get_original_value(change['path'])
                    if full_value:
                        original_value = full_value
                
                env_vars[env_var_name] = original_value
            
            # 生成 .env 文件内容
            env_content = []
            env_content.append("# Docker Compose 环境变量配置文件")
            env_content.append(f"# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            env_content.append("# 注意：此文件包含敏感信息，请勿提交到版本控制系统")
            env_content.append("")
            
            # 按字母顺序排序环境变量
            for key in sorted(env_vars.keys()):
                env_content.append(f"{key}={env_vars[key]}")
            
            # 写入 .env 文件
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content) + '\n')
            
            logger.info(f"已生成 .env 文件: {env_file_path}")
            logger.info(f"包含 {len(env_vars)} 个环境变量")
            
            # 自动将 .env 添加到 .gitignore（如果是 Git 项目）
            self.add_to_gitignore(env_file_path)
            
        except Exception as e:
            logger.error(f"生成 .env 文件失败: {e}")
    
    def get_original_value(self, path: str) -> Optional[str]:
        """从原始 YAML 文件中获取完整的原始值"""
        try:
            # 查找最新的备份文件
            backup_files = list(self.file_path.parent.glob(f"{self.file_path.name}.backup-*.txt"))
            if not backup_files:
                return None
            
            # 按文件名排序获取最新的备份（时间戳格式保证排序正确）
            backup_path = sorted(backup_files)[-1]
            
            # 加载备份文件
            with open(backup_path, 'r', encoding='utf-8') as f:
                original_data = self.yaml.load(f)
            
            # 解析路径并获取值
            # 路径格式: services.web.environment.DB_PASSWORD
            parts = path.split('.')
            current = original_data
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            
            return str(current)
            
        except Exception as e:
            logger.warning(f"获取原始值失败 {path}: {e}")
            return None
    
    def find_git_root(self, start_path: Path) -> Optional[Path]:
        """向上查找 Git 仓库根目录"""
        current = start_path.resolve()
        
        # 最多向上查找 20 层目录
        for _ in range(20):
            git_dir = current / '.git'
            if git_dir.exists():
                return current
            
            parent = current.parent
            if parent == current:  # 已到达根目录
                break
            current = parent
        
        return None
    
    def add_to_gitignore(self, env_file_path: Path) -> None:
        """将 .env 文件添加到 .gitignore"""
        try:
            # 查找 Git 仓库根目录
            git_root = self.find_git_root(env_file_path.parent)
            
            if not git_root:
                logger.info("未检测到 Git 仓库，跳过 .gitignore 配置")
                return
            
            logger.info(f"检测到 Git 仓库: {git_root}")
            
            gitignore_path = git_root / '.gitignore'
            
            # 读取现有的 .gitignore
            existing_entries = set()
            if gitignore_path.exists():
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_entries = set(line.strip() for line in f.readlines())
            
            # 检查是否已存在
            if '.env' in existing_entries:
                logger.info(".env 已在 .gitignore 中，无需重复添加")
                return
            
            # 添加 .env 到 .gitignore
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                # 添加空行（如果文件不为空且最后一行不是空行）
                if existing_entries:
                    f.write('\n')
                
                f.write('# Docker Compose 环境变量文件 - 包含敏感信息\n')
                f.write('.env\n')
                f.write('.env.*\n')  # 忽略所有 .env.* 文件
                f.write('!.env.example\n')  # 但保留 .env.example\n')
            
            logger.info(f"已将 .env 添加到 .gitignore: {gitignore_path}")
            logger.info(f"Git 仓库根目录: {git_root}")
            
        except Exception as e:
            logger.warning(f"添加到 .gitignore 失败: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成变更报告"""
        report = {
            'file': str(self.file_path),
            'timestamp': str(__import__('datetime').datetime.now()),
            'total_changes': len(self.changes),
            'changes': self.changes
        }
        return report
    
    def print_report(self) -> None:
        """打印变更报告"""
        if not self.changes:
            print("未检测到需要脱敏的敏感信息。")
            return
            
        print("\n=== 脱敏变更报告 ===")
        print(f"文件: {self.file_path}")
        print(f"总变更数: {len(self.changes)}")
        print("-" * 50)
        
        # 表格化输出
        print(f"{'路径':<30} {'原值':<20} {'替换为':<20} {'状态':<10}")
        print("-" * 80)
        
        for change in self.changes:
            original = change['original']
            if len(original) > 18:
                original = original[:15] + "..."
                
            print(f"{change['path']:<30} {original:<20} {change['replacement']:<20} {change['status']:<10}")
        
        print("=" * 50)
    
    def save_json_report(self) -> None:
        """保存 JSON 格式报告"""
        if self.report_json:
            report = self.generate_report()
            try:
                with open(self.report_json, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"JSON 报告已保存到: {self.report_json}")
            except Exception as e:
                logger.error(f"保存 JSON 报告失败: {e}")
    
    def run(self) -> int:
        """执行脱敏流程"""
        try:
            logger.info(f"开始处理文件: {self.file_path}")
            
            # 加载 YAML
            data = self.load_yaml()
            
            # 处理 YAML 数据
            processed_data = self.process_yaml(data)
            
            # 验证 YAML 格式
            if not self.validate_yaml(processed_data):
                logger.error("YAML 格式验证失败，操作终止")
                return 1
            
            # 保存处理后的 YAML
            if not self.save_yaml(processed_data):
                logger.error("保存文件失败")
                return 1
            
            # 使用 docker compose config 验证文件
            if not self.dry_run:
                self.validate_with_docker_compose()
            
            # 生成并打印报告
            self.print_report()
            self.save_json_report()
            
            logger.info("脱敏处理完成")
            return 0
            
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return 1
    
    def validate_with_docker_compose(self) -> bool:
        """使用 docker compose config 验证文件格式"""
        try:
            import subprocess
            
            # 确定要验证的文件路径
            file_to_validate = self.output_path
            
            logger.info(f"使用 docker compose 验证文件: {file_to_validate}")
            
            # 执行 docker compose config --quiet
            result = subprocess.run(
                ['docker', 'compose', '-f', str(file_to_validate), 'config', '--quiet'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ Docker Compose 格式验证通过")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                logger.warning(f"⚠️ Docker Compose 格式验证失败: {error_msg}")
                logger.warning("文件可能包含语法错误或不兼容的配置")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Docker Compose 验证超时")
            return False
        except FileNotFoundError:
            logger.info("ℹ️ 未找到 docker compose 命令，跳过验证（可选）")
            return True  # 不阻止流程
        except Exception as e:
            logger.warning(f"⚠️ Docker Compose 验证失败: {e}")
            return True  # 不阻止流程

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Docker Compose 文件脱敏工具 - 自动扫描并脱敏 docker-compose.yml 中的硬编码敏感信息'
    )
    
    parser.add_argument(
        '--file',
        required=True,
        help='目标 docker-compose.yml 路径'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='输出路径（默认原地覆盖）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅打印差异，不写文件'
    )
    
    parser.add_argument(
        '--keywords',
        default=DEFAULT_KEYWORDS,
        help=f'敏感词正则字符串，默认: {DEFAULT_KEYWORDS}'
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        help='修改前自动备份为 .bak'
    )
    
    parser.add_argument(
        '--report-json',
        default=None,
        help='导出结构化变更报告为 JSON 文件'
    )
    
    args = parser.parse_args()
    
    # 创建脱敏器实例
    desensitizer = DockerComposeDesensitizer(
        file_path=args.file,
        output_path=args.output,
        dry_run=args.dry_run,
        keywords=args.keywords,
        backup=args.backup,
        report_json=args.report_json
    )
    
    # 执行脱敏流程
    exit_code = desensitizer.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()