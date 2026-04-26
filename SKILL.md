---
name: docker-compose-desensitizer
description: Automatically scan and sanitize hardcoded sensitive information in docker-compose.yml files by replacing passwords, API keys, and connection strings with ${ENV_VAR} format. Generates corresponding .env files for secure configuration management. Use when working with docker-compose files containing sensitive configuration, or when the user mentions sanitizing, desensitizing, or securing docker-compose configurations.
---

# Docker Compose 文件脱敏工具

自动扫描并脱敏 docker-compose.yml 文件中的硬编码敏感信息，生成安全的配置文件和对应的 .env 环境变量文件。

## 快速开始

### 基本用法

```bash
# 脱敏 docker-compose.yml 文件（自动备份原文件）
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py --file docker-compose.yml

# 预览脱敏效果（不修改文件）
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py --file docker-compose.yml --dry-run

# 指定输出路径（不修改原文件）
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py --file docker-compose.yml --output docker-compose-safe.yml
```

### 完整参数说明

- `--file`: 目标 docker-compose.yml 路径（必填）
- `--output`: 输出路径（默认原地覆盖，原文件自动备份）
- `--dry-run`: 仅打印差异，不写文件
- `--keywords`: 敏感词正则字符串（默认已优化）
- `--backup`: 保留参数（兼容性，现已默认备份）
- `--report-json`: 导出结构化变更报告为 JSON 文件

## 核心功能

### 1. 自动备份机制

当原地覆盖文件时（不指定 --output），自动备份原文件：
- 备份文件名格式：`docker-compose.yml.backup-YYYYMMddHHmmss.txt`
- 包含完整的时间戳（年月日时分秒），确保每次脱敏都有唯一备份
- 确保原始文件安全可追溯

### 2. 智能敏感信息识别

自动识别以下类型的敏感信息：
- 密码字段（PASSWORD, PWD 等）
- 密钥和令牌（SECRET, TOKEN, API_KEY 等）
- 凭据信息（CREDENTIAL, AUTH 等）
- 包含密码的 URL 连接字符串（DATABASE_URL, REDIS_URL 等）

### 3. URL 密码处理

特别处理包含密码的连接字符串：
```yaml
# 原始
DATABASE_URL: postgresql://admin:password123@db:5432/myapp
REDIS_URL: redis://:redispass@redis:6379

# 脱敏后
DATABASE_URL: ${DATABASE_URL}
REDIS_URL: ${REDIS_URL}
```

### 4. 格式保留

- 100% 保留原始缩进、注释、引号风格
- 保持多行块语法（| / >）
- 保留别名引用（& / *）
- 不修改布尔值、端口、镜像名等非敏感配置

### 5. 自动生成 .env 文件

脱敏后自动生成 .env 文件，包含所有敏感信息的完整值：
- 与 docker-compose.yml 同一目录
- 包含完整的原始敏感值（不会被截断）
- 按字母顺序排序，方便查找
- 带有生成时间和安全提示注释

### 6. 自动配置 .gitignore

如果是 Git 项目，自动将 .env 文件添加到 .gitignore：
- 智能查找 Git 仓库根目录（最多向上 20 层）
- 自动添加 .env、.env.* 到忽略列表
- 保留 .env.example 不被忽略
- 避免重复添加
- 确保敏感信息不会被提交到版本控制

### 7. Docker Compose 格式验证

脱敏后自动使用 `docker compose config --quiet` 验证文件格式：
- 确保脱敏后的文件可以被 Docker Compose 正确解析
- 检测语法错误和不兼容的配置
- 验证失败时给出警告信息
- 不阻止脱敏流程（验证失败仅警告）

```env
# Docker Compose 环境变量配置文件
# 生成时间: 2026-04-26 21:16:59
# 注意：此文件包含敏感信息，请勿提交到版本控制系统

API_KEY=sk-1234567890abcdef
AUTH_SECRET=myauthsecretkey
DATABASE_URL=postgresql://admin:password789@db:5432/myapp
DB_PASSWORD=mysecretpassword123
POSTGRES_PASSWORD=mysecretpassword123
REDIS_PASSWORD=redispass123
REDIS_URL=redis://:redispass123@redis:6379
SECRET_TOKEN=supersecrettoken456
```

## 工作流程

### 步骤 1: 分析文件（预览）

```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run
```

### 步骤 2: 执行脱敏（自动备份）

```bash
# 直接脱敏（原文件自动备份为 docker-compose.yml.backup-YYYY-MM-DD.txt）
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml

# 或指定输出路径（不修改原文件）
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --output docker-compose-safe.yml
```

### 步骤 3: 验证结果

```bash
# 查看脱敏报告
cat desensitize-report.json

# 检查备份文件
ls *.backup-*.txt

# 检查自动生成的 .env 文件
cat .env
```

### 步骤 4: 验证 .gitignore 配置

工具会自动将 .env 添加到 .gitignore（如果是 Git 项目）：
```bash
# 检查 .gitignore 是否包含 .env
cat .gitignore | grep "\.env"

# 如果没有，手动添加
echo ".env" >> .gitignore
```

## 示例

### 示例 1: 原地脱敏（自动备份）

**执行命令：**
```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml
```

**生成的文件：**
- `docker-compose.yml` - 脱敏后的文件（覆盖原文件）
- `docker-compose.yml.backup-20260426211800.txt` - 原始文件备份（包含完整时间戳）
- `.env` - 自动生成的环境变量文件（包含所有敏感值）

### 示例 2: 指定输出路径

**执行命令：**
```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --output docker-compose-safe.yml
```

**生成的文件：**
- `docker-compose.yml` - 原始文件保持不变
- `docker-compose-safe.yml` - 脱敏后的文件
- `.env` - 自动生成的环境变量文件（包含所有敏感值）

### 示例 3: 输入文件 (docker-compose.yml)

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

### 脱敏后输出

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

### 生成的 .env 文件

```env
POSTGRES_PASSWORD=mysecretpassword123
DATABASE_URL=postgresql://admin:password123@db:5432/myapp
API_KEY=sk-1234567890
```

## 安全最佳实践

### 1. 版本控制

- ✅ 提交脱敏后的 docker-compose.yml
- ❌ 绝不提交 .env 文件
- ✅ 在 .gitignore 中添加 .env

### 2. 环境隔离

- 开发、测试、生产环境使用不同的 .env 文件
- 使用 `.env.development`、`.env.production` 等命名
- 在文档中说明需要的环境变量

### 3. 密钥管理

- 生产环境考虑使用 Docker Secrets 或 HashiCorp Vault
- 定期轮换敏感凭据
- 限制 .env 文件的访问权限

## 依赖安装

```bash
pip install ruamel.yaml
```

## 集成到 CI/CD

### Pre-commit 钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docker-compose-desensitize
        name: Check docker-compose.yml for hardcoded secrets
        entry: python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py
        args: [--file, docker-compose.yml, --dry-run, --fail-on-find]
        language: system
        files: docker-compose\.yml$
        pass_filenames: false
```

### CI 检查

```bash
# 在 CI 流程中添加检查
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run \
  --check-only
```

## 故障排除

### 问题 1: ruamel.yaml 未安装

```bash
pip install ruamel.yaml
```

### 问题 2: YAML 格式错误

工具会自动验证 YAML 格式。如果验证失败，检查：
- 缩进是否一致（建议使用 2 空格）
- 特殊字符是否正确转义
- 引号是否配对

### 问题 3: 环境变量未生效

确保：
- .env 文件与 docker-compose.yml 在同一目录
- 环境变量名称匹配
- Docker Compose 版本支持环境变量替换

## 附加资源

- [Docker Compose 环境变量文档](https://docs.docker.com/compose/environment-variables/)
- [Docker Secrets 最佳实践](https://docs.docker.com/compose/use-secrets/)
- [12-Factor App 配置原则](https://12factor.net/config)
