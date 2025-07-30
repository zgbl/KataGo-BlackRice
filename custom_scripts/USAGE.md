# 使用说明

## 快速开始

### 1. 构建Docker镜像

**Windows用户：**
```powershell
.\custom_scripts\docker\build_docker.ps1
```

**Linux/Mac用户：**
```bash
./custom_scripts/docker/build_docker.sh
```

### 2. 启动KataGo服务

**使用标准Docker Compose：**
```bash
docker-compose up -d katago-gpu  # GPU版本
docker-compose up -d katago-cpu  # CPU版本
```

**使用GPU修复版本：**
```powershell
# 从项目根目录运行
.\custom_scripts\docker\start_katago_gpu_fix.ps1

# 或者进入docker目录运行
cd custom_scripts\docker
.\start_katago_gpu_fix.ps1
```

### 3. 运行测试

**CUDA测试：**
```bash
# 从项目根目录运行
python custom_scripts/tests/test_cuda_12_9.py

# 或者进入tests目录运行
cd custom_scripts/tests
python test_cuda_12_9.py
```

**GPU直接测试：**
```bash
# 从项目根目录运行
python custom_scripts/tests/test_gpu_direct.py

# 或者进入tests目录运行
cd custom_scripts/tests
python test_gpu_direct.py
```

**KataGo功能测试：**
```bash
# 从项目根目录运行
python custom_scripts/tests/test_katago.py

# 或者进入tests目录运行
cd custom_scripts/tests
python test_katago.py
```

**HTTP连接测试：**
```bash
# 从项目根目录运行
python custom_scripts/tests/test_http_connection.py

# 或者进入tests目录运行
cd custom_scripts/tests
python test_http_connection.py
```

## 配置文件

- `custom_scripts/configs/katago_http.cfg` - KataGo HTTP服务配置

## 目录结构说明

```
custom_scripts/
├── README.md           # 总体说明
├── USAGE.md           # 使用说明（本文件）
├── docker/            # Docker相关脚本
│   ├── build_docker.ps1
│   ├── build_docker.sh
│   ├── docker-compose-gpu-fix.yml
│   ├── setup_configs.sh
│   ├── start_analysis.sh
│   └── start_katago_gpu_fix.ps1
├── configs/           # 自定义配置文件
│   └── katago_http.cfg
└── tests/             # 测试脚本
    ├── test_cuda_12_9.py
    ├── test_gpu_direct.py
    └── test_katago.py
```

## 注意事项

1. 所有自定义脚本现在都在 `custom_scripts/` 目录下
2. 原项目文件保持不变，便于后续更新和维护
3. Docker Compose配置已更新，会自动使用新的配置文件路径
4. 如需修改配置，请编辑 `custom_scripts/configs/` 下的文件