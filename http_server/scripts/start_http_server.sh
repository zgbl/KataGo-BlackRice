#!/bin/bash

# KataGo HTTP服务启动脚本（修正版）
# 使用方法: ./start_http_server.sh [port]

set -e
# ========== 关键修复：添加 PATH 设置 ==========
export PATH="/app/bin:$PATH"

# 默认配置
DEFAULT_PORT=8080
CONTAINER_NAME="katago-http-server"
CONFIG_FILE="/app/configs/custom/katago_http.cfg"
MODEL_FILE="/app/models/model.bin.gz"
LOG_DIR="/app/analysis_logs"

# 参数处理
PORT=${1:-$DEFAULT_PORT}
INSTANCE_ID=${INSTANCE_ID:-1}

echo "🚀 启动KataGo HTTP服务..."
echo "📊 实例ID: $INSTANCE_ID"
echo "🌐 端口: $PORT"
echo "📁 配置文件: $CONFIG_FILE"
echo "🧠 模型文件: $MODEL_FILE"
echo "📝 日志目录: $LOG_DIR"

# 检查必要文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$MODEL_FILE" ]; then
    echo "❌ 错误: 模型文件不存在: $MODEL_FILE"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查GPU可用性
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 GPU信息:"
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits
else
    echo "⚠️  警告: 未检测到NVIDIA GPU或nvidia-smi命令"
fi

# 设置环境变量
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES:-all}
export NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:-compute,utility}

# 启动KataGo HTTP服务
echo "🔄 启动KataGo HTTP分析引擎..."

# 构建启动命令 - 关键修改：使用http命令而不是analysis
#KATAGO_CMD="katago http -config $CONFIG_FILE -model $MODEL_FILE -port $PORT"
KATAGO_CMD="katago analysis -config $CONFIG_FILE -model $MODEL_FILE"

echo "📋 执行命令: $KATAGO_CMD"

# 创建PID文件目录
PID_DIR="/tmp/katago"
mkdir -p "$PID_DIR"
PID_FILE="$PID_DIR/katago-http-$INSTANCE_ID.pid"

# 信号处理函数
cleanup() {
    echo "\n🛑 收到停止信号，正在关闭服务..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "📋 停止进程 $PID"
            kill -TERM "$PID"
            # 等待进程优雅退出
            for i in {1..30}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # 如果进程仍在运行，强制杀死
            if kill -0 "$PID" 2>/dev/null; then
                echo "⚠️  强制停止进程 $PID"
                kill -KILL "$PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    echo "✅ 服务已停止"
    exit 0
}

# 注册信号处理
trap cleanup SIGTERM SIGINT

# 启动服务并记录PID
echo "🎯 启动HTTP分析服务..."
$KATAGO_CMD &
KATAGO_PID=$!
echo $KATAGO_PID > "$PID_FILE"

echo "✅ KataGo HTTP服务已启动"
echo "🆔 进程ID: $KATAGO_PID"
echo "🌐 服务地址: http://0.0.0.0:$PORT"
echo "📊 健康检查: curl http://localhost:$PORT/status"
echo "📝 日志文件: $LOG_DIR/"
echo "🔧 配置文件: $CONFIG_FILE"
echo ""
echo "💡 使用 Ctrl+C 停止服务"
echo "💡 使用 docker logs $CONTAINER_NAME 查看日志"
echo "💡 测试命令: curl -X POST http://localhost:$PORT/query -d '{\"board\":\"19\",\"moves\":[],\"rules\":\"chinese\"}'"

# 等待进程结束
wait $KATAGO_PID
echo "🏁 KataGo HTTP服务已退出"
rm -f "$PID_FILE"