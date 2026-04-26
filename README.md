# Docker Compose Desensitizer / Docker Compose 脱敏工具

🔒 Automatically scan and sanitize hardcoded sensitive information in docker-compose.yml files  
🔒 自动扫描并脱敏 docker-compose.yml 文件中的硬编码敏感信息

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features / 功能特性

- 🔍 **Smart Detection / 智能检测**: Automatically identifies passwords, API keys, tokens, and connection strings / 自动识别密码、API 密钥、令牌和连接字符串
- 🛡️ **URL Password Handling / URL 密码处理**: Special handling for database URLs (DATABASE_URL, REDIS_URL, etc.) / 特殊处理数据库 URL（DATABASE_URL、REDIS_URL 等）
- 📝 **Format Preservation / 格式保留**: 100% preserves original YAML format, comments, and indentation / 100% 保留原始 YAML 格式、注释和缩进
- 🔐 **Auto .env Generation / 自动生成 .env**: Automatically generates .env files with all sensitive values / 自动生成包含所有敏感值的 .env 文件
- 🔄 **Auto Backup / 自动备份**: Creates timestamped backups before overwriting files / 覆盖文件前创建带时间戳的备份
- ✅ **Format Validation / 格式验证**: Validates with `docker compose config` after sanitization / 脱敏后使用 `docker compose config` 验证格式
- 📊 **Detailed Reports / 详细报告**: Generates JSON reports of all changes / 生成所有变更的 JSON 报告
- 🚫 **Git Integration / Git 集成**: Automatically adds .env to .gitignore in Git repositories / 在 Git 仓库中自动将 .env 添加到 .gitignore

## 🚀 Quick Start / 快速开始

### Installation / 安装

```bash
# Install dependency / 安装依赖
pip install ruamel.yaml

# Or install all dependencies / 或安装所有依赖
pip install -r requirements.txt
```

### Basic Usage / 基本使用

```bash
# Sanitize docker-compose.yml (auto-backup original file) / 脱敏 docker-compose.yml（自动备份原文件）
python scripts/desensitize.py --file docker-compose.yml

# Preview changes without modifying files / 预览变更而不修改文件
python scripts/desensitize.py --file docker-compose.yml --dry-run

# Specify output file / 指定输出文件
python scripts/desensitize.py --file docker-compose.yml --output docker-compose-safe.yml
```

### Complete Parameters / 完整参数说明

```
--file         Path to docker-compose.yml (required) / docker-compose.yml 文件路径（必需）
--output       Output path (default: overwrite original with backup) / 输出路径（默认：覆盖原文件并创建备份）
--dry-run      Preview changes without writing files / 预览变更而不写入文件
--keywords     Custom regex pattern for sensitive keywords / 自定义敏感关键词的正则表达式模式
--backup       Create backup (default: true when overwriting) / 创建备份（覆盖时默认为 true）
--report-json  Export detailed report as JSON file / 导出详细报告为 JSON 文件
```

## 📖 Examples / 使用示例

### Example 1: Basic Sanitization / 示例 1：基本脱敏

**Input (docker-compose.yml) / 输入：**
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: mysecretpassword123
      POSTGRES_USER: admin
  
  app:
    image: myapp:latest
    environment:
      DATABASE_URL: postgresql://admin:password123@db:5432/myapp
      API_KEY: sk-1234567890
```

**Output (docker-compose.yml) / 输出：**
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: admin
  
  app:
    image: myapp:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      API_KEY: ${API_KEY}
```

**Generated (.env) / 生成的 .env 文件：**
```env
# Docker Compose Environment Variables / Docker Compose 环境变量配置
# Generated: 2026-04-26 21:00:00 / 生成时间
# WARNING: This file contains sensitive information. DO NOT commit to version control! / 警告：此文件包含敏感信息。请勿提交到版本控制系统！

API_KEY=sk-1234567890
DATABASE_URL=postgresql://admin:password123@db:5432/myapp
POSTGRES_PASSWORD=mysecretpassword123
```

### Example 2: Dry Run Mode / 示例 2：干运行模式

```bash
python scripts/desensitize.py --file docker-compose.yml --dry-run
```

Preview all changes without modifying any files. / 预览所有变更而不修改任何文件。

### Example 3: Generate Report / 示例 3：生成报告

```bash
python scripts/desensitize.py --file docker-compose.yml --report-json report.json
```

Generates a detailed JSON report of all changes. / 生成所有变更的详细 JSON 报告。

## 🔧 Advanced Usage / 高级用法

### Custom Sensitive Keywords / 自定义敏感关键词

```bash
python scripts/desensitize.py \
  --file docker-compose.yml \
  --keywords "(?i)(password|secret|token|api_key|connection_string)"
```

### Integration with Pre-commit / 集成到 Pre-commit

Add to `.pre-commit-config.yaml` / 添加到 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: local
    hooks:
      - id: docker-compose-desensitizer
        name: Check docker-compose.yml for secrets / 检查 docker-compose.yml 中的敏感信息
        entry: python scripts/desensitize.py
        args: [--file, docker-compose.yml, --dry-run]
        language: system
        files: docker-compose\.yml$
```

### CI/CD Integration / CI/CD 集成

```bash
# Check for hardcoded secrets in CI / 在 CI 中检查硬编码的敏感信息
python scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run \
  --check-only
```

## 📁 Project Structure / 项目结构

```
docker-compose-desensitizer/
├── scripts/
│   └── desensitize.py      # Main sanitization script / 主脱敏脚本
├── requirements.txt        # Python dependencies / Python 依赖
├── README.md              # This file / 本文件
├── LICENSE                # MIT License / MIT 许可证
└── examples/              # Example files / 示例文件
    ├── docker-compose.yml
    └── .env.example
```

## 🛡️ Security Best Practices / 安全最佳实践

### 1. Version Control / 版本控制

- ✅ Commit sanitized docker-compose.yml / 提交脱敏后的 docker-compose.yml
- ❌ NEVER commit .env files / 永远不要提交 .env 文件
- ✅ Add .env to .gitignore (automatic in Git repos) / 将 .env 添加到 .gitignore（在 Git 仓库中自动完成）

### 2. Environment Isolation / 环境隔离

- Use different .env files for different environments / 为不同环境使用不同的 .env 文件
- Name them: `.env.development`, `.env.production`, etc. / 命名规范：`.env.development`、`.env.production` 等
- Document required environment variables / 记录所需的环境变量

### 3. Secret Management / 密钥管理

- Use Docker Secrets or HashiCorp Vault for production / 生产环境使用 Docker Secrets 或 HashiCorp Vault
- Rotate sensitive credentials regularly / 定期轮换敏感凭据
- Limit .env file access permissions / 限制 .env 文件的访问权限

## 🔍 How It Works / 工作原理

1. **Parse YAML / 解析 YAML**: Load docker-compose.yml with ruamel.yaml / 使用 ruamel.yaml 加载 docker-compose.yml
2. **Detect Secrets / 检测敏感信息**: Scan for sensitive keywords and URL patterns / 扫描敏感关键词和 URL 模式
3. **Replace Values / 替换值**: Substitute with `${ENV_VAR}` format / 替换为 `${ENV_VAR}` 格式
4. **Backup Original / 备份原文件**: Create timestamped backup (if overwriting) / 创建带时间戳的备份（如果覆盖）
5. **Generate .env / 生成 .env**: Create .env file with all sensitive values / 创建包含所有敏感值的 .env 文件
6. **Validate / 验证格式**: Run `docker compose config --quiet` / 运行 `docker compose config --quiet`
7. **Update .gitignore / 更新 .gitignore**: Add .env to .gitignore (if Git repo) / 将 .env 添加到 .gitignore（如果是 Git 仓库）
8. **Generate Report / 生成报告**: Create detailed change report / 创建详细的变更报告

## 📋 Requirements / 系统要求

- Python 3.8+
- ruamel.yaml >= 0.17.0
- Docker Compose (for validation, optional) / 用于验证，可选

## 🤝 Contributing / 贡献指南

Contributions are welcome! Please feel free to submit a Pull Request. / 欢迎贡献！请随时提交 Pull Request。

1. Fork the repository / Fork 本仓库
2. Create your feature branch (`git checkout -b feature/AmazingFeature`) / 创建您的功能分支
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`) / 提交您的更改
4. Push to the branch (`git push origin feature/AmazingFeature`) / 推送到分支
5. Open a Pull Request / 开启 Pull Request

## 📝 License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. / 本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 Acknowledgments / 致谢

- [ruamel.yaml](https://yaml.readthedocs.io/) for YAML parsing / 提供 YAML 解析
- Docker Compose team for the configuration validation / 提供配置验证功能

## 📞 Support / 支持

- 🐛 [Report Issues / 报告问题](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)
- 💡 [Feature Requests / 功能请求](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)

## ⭐ Show Your Support / 支持我们

If this project helped you, please give it a star! 🌟 / 如果这个项目对您有帮助，请给它一个星标！🌟

---

Made with ❤️ by [JiangLongLiu](https://github.com/JiangLongLiu) / 由 [JiangLongLiu](https://github.com/JiangLongLiu) 用 ❤️ 制作
