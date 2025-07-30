# KataGo HTTP服务

这是KataGo的HTTP REST API服务模块，提供基于Web的围棋分析服务。

## 项目结构

```
http_server/
├── configs/                     # HTTP服务配置文件
│   ├── katago_http.cfg         # KataGo HTTP服务配置
│   └── nginx.conf              # 反向代理配置（可选）
├── docker/                     # Docker相关文件
│   ├── Dockerfile.http         # HTTP服务专用Docker文件
│   ├── docker-compose.yml      # HTTP服务compose配置
│   └── docker-compose.prod.yml # 生产环境配置
├── scripts/                    # 脚本文件
│   ├── start_http_server.sh    # 启动HTTP服务脚本
│   ├── stop_http_server.sh     # 停止HTTP服务脚本
│   ├── test_connection.py      # 连接测试脚本
│   └── health_check.py         # 健康检查脚本
├── examples/                   # 客户端示例
│   ├── simple_client.py        # 简单客户端示例
│   ├── batch_analysis.py       # 批量分析示例
│   └── remote_client.py        # 远程客户端示例
├── logs/                       # HTTP服务日志
├── .env.example               # 环境变量示例
└── README.md                  # 本文件
```

## 快速开始

### 1. 启动HTTP服务

```bash
cd http_server/scripts
./start_http_server.sh
```

### 2. 测试连接

```bash
python scripts/test_connection.py
```

### 3. 使用客户端示例

```bash
python examples/simple_client.py
```

## API文档

### 分析请求

**POST** `/analyze`

请求体示例：
```json
{
  "id": "analysis_1",
  "moves": [],
  "rules": "tromp-taylor",
  "komi": 7.5,
  "boardXSize": 19,
  "boardYSize": 19,
  "analyzeTurns": [0],
  "maxVisits": 1000
}
```

### 健康检查

**GET** `/health`

返回服务状态信息。

## 配置说明

主要配置文件位于 `configs/katago_http.cfg`，包含：
- HTTP服务器端口和地址设置
- 分析引擎参数
- 日志配置
- 性能优化参数

## 部署说明

### 开发环境
使用 `docker/docker-compose.yml`

### 生产环境
使用 `docker/docker-compose.prod.yml`，包含：
- Nginx反向代理
- 负载均衡
- SSL/TLS支持
- 监控和日志收集