# Custom Scripts Directory

这个目录包含了我们为KataGo项目开发的自定义脚本和配置文件。

## 目录结构

- `docker/` - Docker相关的构建和管理脚本
- `configs/` - 自定义配置文件
- `tests/` - 测试脚本
- `utils/` - 实用工具脚本

## 文件说明

### Docker脚本
- `build_docker.ps1` - Windows PowerShell Docker构建脚本
- `build_docker.sh` - Linux/Mac Docker构建脚本
- `docker-compose-gpu-fix.yml` - GPU修复版本的Docker Compose配置
- `start_katago_gpu_fix.ps1` - GPU修复版本的启动脚本
- `start_analysis.sh` - 分析模式启动脚本
- `setup_configs.sh` - 配置文件设置脚本

### 测试脚本
- `test_cuda_12_9.py` - CUDA 12.9测试脚本
- `test_gpu_direct.py` - GPU直接测试脚本
- `test_katago.py` - KataGo功能测试脚本
- `test_http_connection.py` - HTTP连接测试脚本

### 配置文件
- `katago_http.cfg` - KataGo HTTP服务配置文件

这些文件与KataGo原项目文件分离，便于管理和维护。