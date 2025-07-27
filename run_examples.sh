#!/bin/bash

set -e

echo "=== KataGo Docker 使用示例 ==="

# 检查模型文件
if [ ! -f "models/model.bin.gz" ]; then
    echo "错误: 未找到模型文件 models/model.bin.gz"
    echo "请先下载并放置模型文件"
    exit 1
fi

echo "选择运行模式:"
echo "1. 分析引擎模式 (JSON API)"
echo "2. GTP引擎模式"
echo "3. Python示例"
echo "4. 交互式开发环境"
echo "5. 基准测试"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "启动分析引擎..."
        echo "使用 Ctrl+C 停止"
        docker-compose up katago-analysis
        ;;
    2)
        echo "启动GTP引擎..."
        echo "使用 Ctrl+C 停止"
        docker-compose up katago-gtp
        ;;
    3)
        echo "运行Python示例..."
        docker-compose run --rm katago-dev /app/run_example.sh
        ;;
    4)
        echo "启动交互式开发环境..."
        docker-compose run --rm katago-dev /bin/bash
        ;;
    5)
        echo "运行基准测试..."
        docker-compose run --rm katago-dev katago benchmark -model /app/models/model.bin.gz
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac