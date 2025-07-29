# KataGo Docker 使用指南

本项目提供了跨平台的 Docker 配置，支持 Windows GPU、Mac 和 Linux 等多种环境。

## 支持的配置

### 1. CPU 版本（通用）
- **适用平台**: Mac、Windows、Linux
- **服务名**: `katago-cpu`, `katago-gtp-cpu`
- **后端**: EIGEN（纯CPU计算）
- **特点**: 兼容性最好，无需GPU驱动

### 2. NVIDIA GPU 版本
- **适用平台**: Windows（带NVIDIA GPU）、Linux（带NVIDIA GPU）
- **服务名**: `katago-gpu`, `katago-gtp-gpu`
- **后端**: CUDA
- **特点**: 性能最佳，需要NVIDIA GPU和驱动

### 3. OpenCL 版本
- **适用平台**: 支持OpenCL的系统（AMD GPU、Intel GPU等）
- **服务名**: `katago-opencl`
- **后端**: OpenCL
- **特点**: 支持多种GPU厂商

### 4. 开发环境
- **服务名**: `katago-dev`
- **特点**: 可通过环境变量切换后端，包含开发工具

## 快速开始

### 在 Mac 上使用（CPU版本）
```bash
# 构建并启动CPU版本
docker-compose up -d katago-cpu

# 查看日志
docker-compose logs -f katago-cpu
```

### 在 Windows 上使用（GPU版本）

#### 前置要求
1. 安装 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. 确保 Docker Desktop 启用 WSL2 后端
3. 安装最新的 NVIDIA 驱动程序

#### 验证GPU支持
```bash
# 测试GPU访问
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

#### 启动GPU版本
```bash
# 构建并启动GPU版本
docker-compose up -d katago-gpu

# 查看日志
docker-compose logs -f katago-gpu
```

### 使用开发环境
```bash
# 使用CPU后端
KATAGO_BACKEND=EIGEN docker-compose up -d katago-dev

# 使用CUDA后端（需要GPU支持）
KATAGO_BACKEND=CUDA docker-compose up -d katago-dev

# 进入开发容器
docker-compose exec katago-dev /bin/bash
```

## 配置文件说明

### 目录结构
```
.
├── models/          # 模型文件目录
├── configs/         # 配置文件目录
├── logs/           # 日志目录
├── analysis_logs/  # 分析日志目录
└── python_examples/ # Python示例目录
```

### 模型文件
请确保在 `models/` 目录中放置相应的模型文件：
- `katago-*.bin.gz` - 神经网络模型
- 配置文件会自动检测可用的模型

### GPU配置
对于GPU版本，可以在配置文件中设置：
```
# 对于CUDA后端
cudaDeviceToUse = 0

# 对于TensorRT后端
trtDeviceToUse = 0
```

## 性能对比

| 后端 | 平台 | 相对性能 | 内存使用 |
|------|------|----------|----------|
| EIGEN | 通用 | 1x | 低 |
| OpenCL | GPU | 3-8x | 中 |
| CUDA | NVIDIA GPU | 10-50x | 高 |

## 故障排除

### Windows GPU 问题
1. **GPU不可见**
   ```bash
   # 检查NVIDIA Container Toolkit
   docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
   ```

2. **WSL2问题**
   - 确保Docker Desktop使用WSL2后端
   - 更新WSL2到最新版本

3. **驱动问题**
   - 安装最新的NVIDIA驱动
   - 确保驱动版本支持CUDA 11.8+

### Mac 兼容性
1. **AVX2支持**
   - 现代Intel Mac支持AVX2
   - Apple Silicon Mac使用Rosetta2时可能需要调整

2. **内存限制**
   - 调整Docker Desktop的内存限制
   - 推荐至少8GB内存

### 通用问题
1. **构建失败**
   ```bash
   # 清理并重新构建
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

2. **模型文件缺失**
   - 确保models目录包含有效的模型文件
   - 检查文件权限

## 自定义配置

### 环境变量
- `KATAGO_BACKEND`: 设置后端类型（EIGEN/OPENCL/CUDA）
- `TZ`: 时区设置
- `NVIDIA_VISIBLE_DEVICES`: 指定可见的GPU设备

### 构建参数
- `USE_BACKEND`: 编译时后端选择
- `USE_TCMALLOC`: 启用TCMalloc内存分配器
- `USE_AVX2`: 启用AVX2指令集优化
- `BUILD_DISTRIBUTED`: 启用分布式训练支持

## 更多信息

- [KataGo官方文档](https://github.com/lightvector/KataGo)
- [Docker GPU支持](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)