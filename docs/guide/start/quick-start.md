# 快速开始

## 环境要求

- **操作系统**: Linux / macOS / Windows
- **JDK**: 8 或更高版本
- **Maven**: 3.6+
- **Node.js**: 20.19.0+（建议使用仓库根目录 `.nvmrc`）
- **MySQL**: 8.0+
- **DolphinScheduler**: 3.2.0+ (可选,用于任务调度)

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/MingkeVan/opendataworks.git
cd opendataworks
```

### 2. 准备数据库

由于项目集成了 Flyway，您只需创建数据库和用户，无需手动导入表结构。

> **💡 Docker 部署提示**: 如果使用 Docker Compose 部署（见下方"Docker 部署"章节），数据库和用户会自动创建，**无需手动执行以下步骤**。

```bash
# 登录 MySQL
mysql -u root -p

# 执行以下 SQL 创建数据库和用户
CREATE DATABASE opendataworks DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'opendataworks'@'%' IDENTIFIED BY 'opendataworks123';
GRANT ALL PRIVILEGES ON opendataworks.* TO 'opendataworks'@'%';
FLUSH PRIVILEGES;

EXIT;
```

> **注意**: 具体的表结构和初始化数据将在后端服务首次启动时自动通过 Flyway 迁移。

### 3. 启动 DolphinScheduler (可选)

如果需要任务调度功能,请先安装并启动 DolphinScheduler。
参考官方文档: https://dolphinscheduler.apache.org/zh-cn/docs/3.2.0/guide/installation/standalone

### 4. 启动后端服务

```bash
# 在仓库根目录执行

# 修改配置文件 (如需修改数据库密码)
# vim backend/src/main/resources/application.yml

# 编译并启动 backend 模块
mvn -f pom.xml -pl backend -am clean install
mvn -f pom.xml -pl backend -am spring-boot:run
```

- 服务启动后，Flyway 会自动执行迁移脚本 (`src/main/resources/db/migration/`)。
- 服务默认运行在 `http://localhost:8080`。

### 5. 启动前端应用

```bash
cd frontend

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use || nvm install

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

- 应用将运行在 `http://localhost:3000`。
- 当前默认开启匿名访问，本地开发默认无需登录。

### 6. 访问应用

打开浏览器访问: `http://localhost:3000`

## Docker 部署

使用 Docker Compose 部署时，数据库和用户会自动初始化，无需手动创建。

### 开发环境快速启动

如果希望一次性在本机拉起完整环境（前端 + 后端 + DataAgent Backend + Redis + MySQL + Portal MCP），可使用开发环境 Compose：

```bash
# 1. 准备配置
cp deploy/.env.example deploy/.env

# 2. 拉取最新镜像
docker compose -f deploy/docker-compose.dev.yml pull

# 3. 启动服务
docker compose -f deploy/docker-compose.dev.yml up -d

# 访问
# 前端: http://localhost:8081
# 后端: http://localhost:8080/api
# DataAgent Backend: http://localhost:8900
# Portal MCP: http://localhost:8801/mcp
# MySQL: 127.0.0.1:3316
```

**数据库自动初始化说明**：
- MySQL 容器首次启动时，会自动执行 `deploy/database/mysql/` 目录下的初始化脚本
- 数据库 `opendataworks` / `dataagent` 与用户 `opendataworks` / `dataagent` 会自动创建，字符集为 `utf8mb4`
- 表结构由后端服务的 Flyway 自动创建（首次启动时）
- 数据保存在 Docker volume 中，重启容器不会丢失数据，也不会重复执行初始化脚本

### 生产环境/离线部署

请参考 [部署文档](../../../deploy/README.md) 获取详细的生产环境部署和离线包制作指南。
