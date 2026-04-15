# Opendataagent Deploy

## 在线部署

```bash
cd opendataagent/deploy
cp .env.example .env
docker compose up -d --build
```

默认端口：

- Web: `18080`
- Server: `18900`
- MySQL: `13306`

## 离线部署包

在可联网且容器运行时可用的机器上生成：

```bash
bash opendataagent/scripts/create-offline-package.sh
```

默认输出：

- `output/releases/opendataagent/opendataagent-deployment-<tag>.tar.gz`

离线包内容包括：

- `opendataagent-server` 镜像
- `opendataagent-web` 镜像
- `mysql:8.0` 镜像
- `shared-skills/` 快照
- 离线镜像加载和启动脚本

## 安装离线包

```bash
tar -xzf opendataagent-deployment-<tag>.tar.gz
cd opendataagent-deployment
bash scripts/load-package-and-start.sh --package .
```

或一步到位：

```bash
bash opendataagent/scripts/load-package-and-start.sh \
  --package opendataagent-deployment-<tag>.tar.gz
```
