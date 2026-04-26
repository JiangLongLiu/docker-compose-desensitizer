# Docker Compose 脱敏工具使用示例

## 示例 1: 基本脱敏

### 原始 docker-compose.yml

```yaml
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - DB_PASSWORD=mysecretpassword123
      - API_KEY=sk-1234567890abcdef
  
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: mysecretpassword123
      POSTGRES_USER: admin
```

### 执行脱敏

```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --backup \
  --generate-env
```

### 脱敏后

```yaml
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
      - API_KEY=${API_KEY}
  
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: admin
```

### 生成的 .env

```env
DB_PASSWORD=mysecretpassword123
API_KEY=sk-1234567890abcdef
POSTGRES_PASSWORD=mysecretpassword123
```

## 示例 2: 包含 URL 连接字符串

### 原始文件

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      DATABASE_URL: postgresql://admin:password789@db:5432/myapp
      REDIS_URL: redis://:redispass123@redis:6379
      AUTH_SECRET: myauthsecretkey
```

### 脱敏后

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      AUTH_SECRET: ${AUTH_SECRET}
```

### 生成的 .env

```env
DATABASE_URL=postgresql://admin:password789@db:5432/myapp
REDIS_URL=redis://:redispass123@redis:6379
AUTH_SECRET=myauthsecretkey
```

## 示例 3: Dry-run 预览

```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --dry-run
```

输出预览结果，不修改任何文件。

## 示例 4: 生成 JSON 报告

```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --report-json report.json
```

生成的 report.json 包含详细的脱敏记录。

## 示例 5: 自定义敏感词

```bash
python ~/.qoder/skills/docker-compose-desensitizer/scripts/desensitize.py \
  --file docker-compose.yml \
  --keywords "(?i)(password|secret|token|api_key|connection_string)"
```
