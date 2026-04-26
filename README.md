# Docker Compose Desensitizer

🔒 Automatically scan and sanitize hardcoded sensitive information in docker-compose.yml files

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[[English](README.md)] [[中文](README_zh.md)]

## ✨ Features

- 🔍 **Smart Detection**: Automatically identifies passwords, API keys, tokens, and connection strings
- 🛡️ **URL Password Handling**: Special handling for database URLs (DATABASE_URL, REDIS_URL, etc.)
- 📝 **Format Preservation**: 100% preserves original YAML format, comments, and indentation
- 🔐 **Auto .env Generation**: Automatically generates .env files with all sensitive values
- 🔄 **Auto Backup**: Creates timestamped backups before overwriting files
- ✅ **Format Validation**: Validates with `docker compose config` after sanitization
- 📊 **Detailed Reports**: Generates JSON reports of all changes
- 🚫 **Git Integration**: Automatically adds .env to .gitignore in Git repositories

## 🚀 Quick Start

### Installation

```bash
# Install dependency
pip install ruamel.yaml

# Or install all dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Sanitize docker-compose.yml (auto-backup original file)
python scripts/desensitize.py --file docker-compose.yml

# Preview changes without modifying files
python scripts/desensitize.py --file docker-compose.yml --dry-run

# Specify output file
python scripts/desensitize.py --file docker-compose.yml --output docker-compose-safe.yml
```

### Complete Parameters

```
--file         Path to docker-compose.yml (required)
--output       Output path (default: overwrite original with backup)
--dry-run      Preview changes without writing files
--keywords     Custom regex pattern for sensitive keywords
--backup       Create backup (default: true when overwriting)
--report-json  Export detailed report as JSON file
```

## 📖 Examples

### Example 1: Basic Sanitization

**Input (docker-compose.yml):**
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

**Output (docker-compose.yml):**
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

**Generated (.env):**
```env
# Docker Compose Environment Variables
# Generated: 2026-04-26 21:00:00
# WARNING: This file contains sensitive information. DO NOT commit to version control!

API_KEY=sk-1234567890
DATABASE_URL=postgresql://admin:password123@db:5432/myapp
POSTGRES_PASSWORD=mysecretpassword123
```

### Example 2: Dry Run Mode

```bash
python scripts/desensitize.py --file docker-compose.yml --dry-run
```

Preview all changes without modifying any files.

### Example 3: Generate Report

```bash
python scripts/desensitize.py --file docker-compose.yml --report-json report.json
```

Generates a detailed JSON report of all changes.

## 🔧 Advanced Usage

### Custom Sensitive Keywords

```bash
python scripts/desensitize.py \
  --file docker-compose.yml \
  --keywords "(?i)(password|secret|token|api_key|connection_string)"
```

### Integration with Pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: docker-compose-desensitizer
        name: Check docker-compose.yml for secrets
        entry: python scripts/desensitize.py
        args: [--file, docker-compose.yml, --dry-run]
        language: system
        files: docker-compose\.yml$
```

### CI/CD Integration

```bash
# Check for hardcoded secrets in CI
python scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run \
  --check-only
```

## 📁 Project Structure

```
docker-compose-desensitizer/
├── scripts/
│   └── desensitize.py      # Main sanitization script
├── requirements.txt        # Python dependencies
├── README.md              # English documentation
├── README_zh.md           # Chinese documentation
├── LICENSE                # MIT License
└── examples/              # Example files
    ├── docker-compose.yml
    └── .env.example
```

## 🛡️ Security Best Practices

### 1. Version Control

- ✅ Commit sanitized docker-compose.yml
- ❌ NEVER commit .env files
- ✅ Add .env to .gitignore (automatic in Git repos)

### 2. Environment Isolation

- Use different .env files for different environments
- Name them: `.env.development`, `.env.production`, etc.
- Document required environment variables

### 3. Secret Management

- Use Docker Secrets or HashiCorp Vault for production
- Rotate sensitive credentials regularly
- Limit .env file access permissions

## 🔍 How It Works

1. **Parse YAML**: Load docker-compose.yml with ruamel.yaml
2. **Detect Secrets**: Scan for sensitive keywords and URL patterns
3. **Replace Values**: Substitute with `${ENV_VAR}` format
4. **Backup Original**: Create timestamped backup (if overwriting)
5. **Generate .env**: Create .env file with all sensitive values
6. **Validate**: Run `docker compose config --quiet`
7. **Update .gitignore**: Add .env to .gitignore (if Git repo)
8. **Generate Report**: Create detailed change report

## 📋 Requirements

- Python 3.8+
- ruamel.yaml >= 0.17.0
- Docker Compose (for validation, optional)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ruamel.yaml](https://yaml.readthedocs.io/) for YAML parsing
- Docker Compose team for the configuration validation

## 📞 Support

- 🐛 [Report Issues](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)
- 💡 [Feature Requests](https://github.com/JiangLongLiu/docker-compose-desensitizer/issues)

## ⭐ Show Your Support

If this project helped you, please give it a star! 🌟

---

Made with ❤️ by [JiangLongLiu](https://github.com/JiangLongLiu)
