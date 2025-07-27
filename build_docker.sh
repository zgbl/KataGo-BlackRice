#!/bin/bash

set -e

echo "=== KataGo Docker 构建脚本 ==="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker Desktop for Mac"
    echo "下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: docker-compose 未安装"
    exit 1
fi

# 设置构建参数
USE_BACKEND=${USE_BACKEND:-EIGEN}
USE_TCMALLOC=${USE_TCMALLOC:-1}
USE_AVX2=${USE_AVX2:-0}
BUILD_DISTRIBUTED=${BUILD_DISTRIBUTED:-0}

echo "构建参数:"
echo "  USE_BACKEND: $USE_BACKEND"
echo "  USE_TCMALLOC: $USE_TCMALLOC"
echo "  USE_AVX2: $USE_AVX2"
echo "  BUILD_DISTRIBUTED: $BUILD_DISTRIBUTED"

# 创建必要的目录
mkdir -p models logs analysis_logs configs python_examples

echo "开始构建 KataGo Docker 镜像..."

# 构建镜像
docker-compose build \
    --build-arg USE_BACKEND=$USE_BACKEND \
    --build-arg USE_TCMALLOC=$USE_TCMALLOC \
    --build-arg USE_AVX2=$USE_AVX2 \
    --build-arg BUILD_DISTRIBUTED=$BUILD_DISTRIBUTED

echo "构建完成！"

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

echo ""
echo "=== 使用说明 ==="
echo ""
echo "1. 启动分析引擎:"
echo "   docker-compose up katago-analysis"
echo ""
echo "2. 启动GTP引擎:"
echo "   docker-compose up katago-gtp"
echo ""
echo "3. 启动开发环境:"
echo "   docker-compose up -d katago-dev"
echo "   docker-compose exec katago-dev /bin/bash"
echo ""
echo "4. 运行Python示例:"
echo "   docker-compose run --rm katago-dev /app/run_example.sh"
echo ""