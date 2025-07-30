#!/bin/bash

# KataGo Docker 构建脚本
# 支持多平台构建：Mac、Windows、Linux
# 支持多后端：CPU(EIGEN)、NVIDIA GPU(CUDA)、OpenCL

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== KataGo Docker 多平台构建脚本 ===${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker:"
    echo "  macOS: brew install --cask docker"
    echo "  Windows: 下载 Docker Desktop for Windows"
    echo "  Linux: 使用包管理器安装 docker"
    echo "  或访问: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: docker-compose 未安装${NC}"
    echo "请先安装 docker-compose:"
    echo "  macOS: brew install docker-compose"
    echo "  Windows: Docker Desktop 自带"
    echo "  Linux: 使用包管理器安装 docker-compose"
    echo "  或访问: https://docs.docker.com/compose/install/"
    exit 1
fi

# 平台检测
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
fi

echo -e "${BLUE}检测到操作系统: ${OS_TYPE}${NC}"

# GPU检测函数
check_nvidia_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            echo -e "${GREEN}检测到 NVIDIA GPU${NC}"
            nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1
            return 0
        fi
    fi
    return 1
}

# 后端选择
echo -e "${YELLOW}选择计算后端:${NC}"
echo "1) CPU (EIGEN) - 兼容所有平台"
echo "2) NVIDIA GPU (CUDA) - 需要NVIDIA GPU"
echo "3) OpenCL - 支持多种GPU"
echo "4) 自动检测"

read -p "请选择 [1-4]: " backend_choice

case $backend_choice in
    1)
        USE_BACKEND="EIGEN"
        echo -e "${GREEN}选择了 CPU 后端${NC}"
        ;;
    2)
        USE_BACKEND="CUDA"
        echo -e "${GREEN}选择了 NVIDIA GPU 后端${NC}"
        if ! check_nvidia_gpu; then
            echo -e "${YELLOW}警告: 未检测到可用的 NVIDIA GPU${NC}"
        fi
        ;;
    3)
        USE_BACKEND="OPENCL"
        echo -e "${GREEN}选择了 OpenCL 后端${NC}"
        ;;
    4)
        echo -e "${BLUE}自动检测最佳后端...${NC}"
        if check_nvidia_gpu; then
            USE_BACKEND="CUDA"
            echo -e "${GREEN}自动选择: NVIDIA GPU (CUDA)${NC}"
        else
            USE_BACKEND="EIGEN"
            echo -e "${GREEN}自动选择: CPU (EIGEN)${NC}"
        fi
        ;;
    *)
        echo -e "${YELLOW}无效选择，使用默认 CPU 后端${NC}"
        USE_BACKEND="EIGEN"
        ;;
esac

# 构建参数设置
USE_TCMALLOC=1          # 使用 TCMalloc 内存分配器
USE_AVX2=1              # 现代CPU都支持AVX2
BUILD_DISTRIBUTED=0     # 分布式训练支持

# Mac特殊处理
if [[ "$OS_TYPE" == "mac" ]]; then
    # 检查是否为Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        echo -e "${YELLOW}检测到 Apple Silicon，可能需要特殊配置${NC}"
        USE_AVX2=0  # Apple Silicon不支持AVX2
    fi
fi

echo -e "${BLUE}构建参数:${NC}"
echo "  平台: $OS_TYPE"
echo "  USE_BACKEND: $USE_BACKEND"
echo "  USE_TCMALLOC: $USE_TCMALLOC"
echo "  USE_AVX2: $USE_AVX2"
echo "  BUILD_DISTRIBUTED: $BUILD_DISTRIBUTED"
echo

# 创建必要的目录
mkdir -p models logs analysis_logs configs python_examples

# 构建 Docker 镜像
echo -e "${BLUE}开始构建 Docker 镜像...${NC}"

export USE_BACKEND
export USE_TCMALLOC
export USE_AVX2
export BUILD_DISTRIBUTED

# 根据后端选择构建相应的服务
case $USE_BACKEND in
    "EIGEN")
        echo -e "${BLUE}构建 CPU 版本...${NC}"
        docker-compose build katago-cpu katago-gtp-cpu
        ;;
    "CUDA")
        echo -e "${BLUE}构建 GPU 版本...${NC}"
        docker-compose build katago-gpu katago-gtp-gpu
        ;;
    "OPENCL")
        echo -e "${BLUE}构建 OpenCL 版本...${NC}"
        docker-compose build katago-opencl
        ;;
    *)
        echo -e "${BLUE}构建所有版本...${NC}"
        docker-compose build
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker 镜像构建成功!${NC}"
else
    echo -e "${RED}✗ Docker 镜像构建失败!${NC}"
    exit 1
fi

# 检查是否有模型文件
if [ ! -f "models/model.bin.gz" ]; then
    echo ""
    echo "⚠️  注意: 未找到模型文件"
    echo "请下载KataGo模型文件并放置到 models/ 目录："
    echo ""
    echo "1. 访问 https://katagotraining.org/ 下载模型"
    echo "2. 将模型文件重命名为 model.bin.gz"
    echo "3. 放置到 $(pwd)/models/ 目录"
    echo ""
    echo "示例命令:"
    echo "  cd models"
    echo "  wget https://media.katagotraining.org/uploaded/networks/models/kata1-b40c256-s11840935168-d2898845681.bin.gz"
    echo "  mv kata1-b40c256-s11840935168-d2898845681.bin.gz model.bin.gz"
else
    echo ""
    echo "✅ 找到模型文件: models/model.bin.gz"
fi

echo -e "${GREEN}=== 构建完成 ===${NC}"
echo
echo -e "${BLUE}使用方法:${NC}"
echo

# 根据构建的后端提供相应的使用说明
case $USE_BACKEND in
    "EIGEN")
        echo -e "${YELLOW}CPU 版本使用方法:${NC}"
        echo "   # 启动分析引擎"
        echo "   docker-compose up -d katago-cpu"
        echo "   docker-compose logs -f katago-cpu"
        echo
        echo "   # 启动 GTP 引擎"
        echo "   docker-compose up -d katago-gtp-cpu"
        echo "   docker-compose logs -f katago-gtp-cpu"
        ;;
    "CUDA")
        echo -e "${YELLOW}GPU 版本使用方法:${NC}"
        echo "   # 启动分析引擎"
        echo "   docker-compose up -d katago-gpu"
        echo "   docker-compose logs -f katago-gpu"
        echo
        echo "   # 启动 GTP 引擎"
        echo "   docker-compose up -d katago-gtp-gpu"
        echo "   docker-compose logs -f katago-gtp-gpu"
        echo
        if [[ "$OS_TYPE" == "windows" ]]; then
            echo -e "${BLUE}Windows GPU 注意事项:${NC}"
            echo "- 确保已安装 NVIDIA Container Toolkit"
            echo "- 确保 Docker Desktop 使用 WSL2 后端"
            echo "- 测试GPU访问: docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi"
            echo
        fi
        ;;
    "OPENCL")
        echo -e "${YELLOW}OpenCL 版本使用方法:${NC}"
        echo "   # 启动分析引擎"
        echo "   docker-compose up -d katago-opencl"
        echo "   docker-compose logs -f katago-opencl"
        ;;
esac

echo -e "${YELLOW}开发环境:${NC}"
echo "   # 启动开发环境"
echo "   KATAGO_BACKEND=$USE_BACKEND docker-compose up -d katago-dev"
echo "   docker-compose exec katago-dev /bin/bash"
echo
echo -e "${YELLOW}Python 示例:${NC}"
echo "   docker-compose exec katago-dev python3 /app/python_examples/example.py"
echo
echo -e "${BLUE}重要提醒:${NC}"
echo "- 请确保 models/ 目录包含有效的模型文件"
echo "- 日志文件将保存在 logs/ 和 analysis_logs/ 目录中"
echo "- 可以通过修改 configs/ 目录中的配置文件来自定义设置"
echo "- 详细使用说明请查看 DOCKER_USAGE.md 文件"
echo
echo -e "${GREEN}平台兼容性:${NC}"
echo "- CPU版本: 兼容 Mac、Windows、Linux"
echo "- GPU版本: 兼容 Windows + NVIDIA GPU、Linux + NVIDIA GPU"
echo "- OpenCL版本: 兼容支持OpenCL的系统"