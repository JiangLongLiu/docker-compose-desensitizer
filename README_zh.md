# Docker Compose 脱敏工具

🔒 自动扫描并脱敏 docker-compose.yml 文件中的硬编码敏感信息

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 功能特性

- 🔍 **智能检测**：自动识别密码、API 密钥、令牌和连接字符串
- 🛡️ **URL 密码处理**：特殊处理数据库 URL（DATABASE_URL、REDIS_URL 等）
- 📝 **格式保留**：100% 保留原始 YAML 格式、注释和缩进
- 🔐 **自动生成 .env**：自动生成包含所有敏感值的 .env 文件
- 🔄 **自动备份**：覆盖文件前创建带时间戳的备份
- ✅ **格式验证**：脱敏后使用 `docker compose config` 验证格式
- 📊 **详细报告**：生成所有变更的 JSON 报告
- 🚫 **Git 集成**：在 Git 仓库中自动将 .env 添加到 .gitignore

## 🚀 快速开始

### 安装

```bash
# 安装依赖
pip install ruamel.yaml

# 或安装所有依赖
pip install -r requirements.txt
```

### 基本使用

```bash
# 脱敏 docker-compose.yml（自动备份原文件）
python scripts/desensitize.py --file docker-compose.yml

# 预览变更而不修改文件
python scripts/desensitize.py --file docker-compose.yml --dry-run

# 指定输出文件
python scripts/desensitize.py --file docker-compose.yml --output docker-compose-safe.yml
```

### 完整参数说明

```
--file         docker-compose.yml 文件路径（必需）
--output       输出路径（默认：覆盖原文件并创建备份）
--dry-run      预览变更而不写入文件
--keywords     自定义敏感关键词的正则表达式模式
--backup       创建备份（覆盖时默认为 true）
--report-json  导出详细报告为 JSON 文件
```

## 📖 使用示例

### 示例 1：基本脱敏

**输入 (docker-compose.yml)：**
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

**输出 (docker-compose.yml)：**
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

**生成的 (.env)：**
```env
# Docker Compose 环境变量配置
# 生成时间: 2026-04-26 21:00:00
# 警告：此文件包含敏感信息。请勿提交到版本控制系统！

API_KEY=sk-1234567890
DATABASE_URL=postgresql://admin:password123@db:5432/myapp
POSTGRES_PASSWORD=mysecretpassword123
```

### 示例 2：干运行模式

```bash
python scripts/desensitize.py --file docker-compose.yml --dry-run
```

预览所有变更而不修改任何文件。

### 示例 3：生成报告

```bash
python scripts/desensitize.py --file docker-compose.yml --report-json report.json
```

生成所有变更的详细 JSON 报告。

## 🔧 高级用法

### 自定义敏感关键词

```bash
python scripts/desensitize.py \
  --file docker-compose.yml \
  --keywords "(?i)(password|secret|token|api_key|connection_string)"
```

### 集成到 Pre-commit

添加到 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: local
    hooks:
      - id: docker-compose-desensitizer
        name: 检查 docker-compose.yml 中的敏感信息
        entry: python scripts/desensitize.py
        args: [--file, docker-compose.yml, --dry-run]
        language: system
        files: docker-compose\.yml$
```

### CI/CD 集成

```bash
# 在 CI 中检查硬编码的敏感信息
python scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run \
  --check-only
```

## 📁 项目结构

```
docker-compose-desensitizer/
├── scripts/
│   └── desensitize.py      # 主脱敏脚本
├── requirements.txt        # Python 依赖
├── README.md              # 英文文档
├── README_zh.md           # 中文文档（本文件）
├── LICENSE                # MIT 许可证
└── examples/              # 示例文件
    ├── docker-compose.yml
    └── .env.example
```

## 🛡️ 安全最佳实践

### 1. 版本控制

- ✅ 提交脱敏后的 docker-compose.yml
- ❌ 永远不要提交 .env 文件
- ✅ 将 .env 添加到 .gitignore（在 Git 仓库中自动完成）

### 2. 环境隔离

- 为不同环境使用不同的 .env 文件
- 命名规范：`.env.development`、`.env.production` 等
- 记录所需的环境变量

### 3. 密钥管理

- 生产环境使用 Docker Secrets 或 HashiCorp Vault
- 定期轮换敏感凭据
- 限制 .env 文件的访问权限

## 🔍 工作原理

1. **解析 YAML**：使用 ruamel.yaml 加载 docker-compose.yml
2. **检测敏感信息**：扫描敏感关键词和 URL 模式
3. **替换值**：替换为 `${ENV_VAR}` 格式
4. **备份原文件**：创建带时间戳的备份（如果覆盖）
5. **生成 .env**：创建包含所有敏感值的 .env 文件
6. **验证格式**：运行 `docker compose config --quiet`
7. **更新 .gitignore**：将 .env 添加到 .gitignore（如果是 Git 仓库）
8. **生成报告**：创建详细的变更报告

## 📋 系统要求

- Python 3.8+
- ruamel.yaml >= 0.17.0
- Docker Compose（用于验证，可选）

## 🤝 贡献指南

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m '添加一些很棒的功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ruamel.yaml](https://yaml.readthedocs.io/) 提供 YAML 解析
- Docker Compose 团队提供配置验证功能

## 📞 支持

- 🐛 [报告问题](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)
- 💡 [功能请求](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)

## ⭐ 支持我们

如果这个项目对您有帮助，请给它一个星标！🌟

---

由 [JiangLongLiu](https://github.com/JiangLongLiu) 用 ❤️ 制作
