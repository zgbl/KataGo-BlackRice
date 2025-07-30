#!/bin/bash

# KataGo HTTP Analysis Server 启动脚本

echo "=== 启动 KataGo HTTP Analysis Server ==="

# 检查必要文件
if [ ! -f "/app/models/model.bin.gz" ]; then
    echo "❌ 错误: 模型文件不存在 /app/models/model.bin.gz"
    exit 1
fi

if [ ! -f "/app/configs/custom/katago_http.cfg" ]; then
    echo "❌ 错误: HTTP配置文件不存在 /app/configs/custom/katago_http.cfg"
    exit 1
fi

# 创建日志目录
mkdir -p /app/analysis_logs

echo "✅ 配置文件: /app/configs/custom/katago_http.cfg"
echo "✅ 模型文件: /app/models/model.bin.gz"
echo "✅ 日志目录: /app/analysis_logs"
echo "🌐 HTTP服务将在端口 8080 启动"
echo "📡 允许来自所有IP的连接"

# 启动KataGo HTTP服务
echo "正在启动 KataGo HTTP Analysis Server..."
exec katago analysis \
    -config /app/configs/custom/katago_http.cfg \
    -model /app/models/model.bin.gz