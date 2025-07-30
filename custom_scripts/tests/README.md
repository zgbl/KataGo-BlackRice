# Test Scripts

这个目录包含各种测试脚本。

## 文件列表

- `test_cuda_12_9.py` - CUDA 12.9测试脚本
- `test_gpu_direct.py` - GPU直接测试脚本
- `test_katago.py` - KataGo功能测试脚本
- `test_http_connection.py` - HTTP连接测试脚本

## 使用说明

### CUDA测试
```bash
python test_cuda_12_9.py
```
测试CUDA 12.9的兼容性和GPU功能。

### GPU直接测试
```bash
python test_gpu_direct.py
```
直接测试GPU硬件和驱动。

### KataGo功能测试
```bash
python test_katago.py
```
测试KataGo分析引擎的基本功能。

### HTTP连接测试
```bash
python test_http_connection.py
```
测试KataGo HTTP服务的连接和分析请求。