#!/bin/bash

# KataGo HTTP服务停止脚本
# 使用方法: ./stop_http_server.sh [instance_id]

set -e

# 默认配置
DEFAULT_INSTANCE_ID=1
CONTAINER_NAME="katago-http-server"
PID_DIR="/tmp/katago"

# 参数处理
INSTANCE_ID=${1:-$DEFAULT_INSTANCE_ID}
PID_FILE="$PID_DIR/katago-http-$INSTANCE_ID.pid"

echo "🛑 停止KataGo HTTP服务..."
echo "📊 实例ID: $INSTANCE_ID"
echo "📁 PID文件: $PID_FILE"

# 停止Docker容器方式
stop_docker_container() {
    echo "🐳 尝试停止Docker容器: $CONTAINER_NAME"
    
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo "📋 找到运行中的容器，正在停止..."
        docker stop "$CONTAINER_NAME" || true
        
        # 等待容器停止
        echo "⏳ 等待容器完全停止..."
        docker wait "$CONTAINER_NAME" 2>/dev/null || true
        
        echo "✅ 容器已停止"
    else
        echo "ℹ️  容器 $CONTAINER_NAME 未运行"
    fi
    
    # 可选：删除容器
    if docker ps -a -q -f name="$CONTAINER_NAME" | grep -q .; then
        read -p "🗑️  是否删除容器? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker rm "$CONTAINER_NAME" || true
            echo "✅ 容器已删除"
        fi
    fi
}

# 停止进程方式
stop_process() {
    if [ ! -f "$PID_FILE" ]; then
        echo "ℹ️  PID文件不存在: $PID_FILE"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if [ -z "$PID" ]; then
        echo "❌ PID文件为空"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo "📋 找到进程ID: $PID"
    
    # 检查进程是否存在
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "ℹ️  进程 $PID 不存在，清理PID文件"
        rm -f "$PID_FILE"
        return 1
    fi
    
    # 获取进程信息
    echo "📊 进程信息:"
    ps -p "$PID" -o pid,ppid,cmd --no-headers 2>/dev/null || echo "无法获取进程信息"
    
    # 优雅停止
    echo "🔄 发送TERM信号..."
    kill -TERM "$PID"
    
    # 等待进程退出
    echo "⏳ 等待进程优雅退出..."
    for i in {1..30}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "✅ 进程已优雅退出"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo
    
    # 强制停止
    if kill -0 "$PID" 2>/dev/null; then
        echo "⚠️  进程未响应TERM信号，发送KILL信号..."
        kill -KILL "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "❌ 无法停止进程 $PID"
            return 1
        else
            echo "✅ 进程已强制停止"
            rm -f "$PID_FILE"
            return 0
        fi
    fi
}

# 查找并停止所有相关进程
stop_all_processes() {
    echo "🔍 查找所有KataGo HTTP进程..."
    
    # 查找katago进程
    KATAGO_PIDS=$(pgrep -f "katago.*analysis" 2>/dev/null || true)
    
    if [ -n "$KATAGO_PIDS" ]; then
        echo "📋 找到KataGo进程: $KATAGO_PIDS"
        for pid in $KATAGO_PIDS; do
            echo "🔄 停止进程 $pid"
            kill -TERM "$pid" 2>/dev/null || true
        done
        
        # 等待进程退出
        sleep 5
        
        # 检查是否还有进程运行
        REMAINING_PIDS=$(pgrep -f "katago.*analysis" 2>/dev/null || true)
        if [ -n "$REMAINING_PIDS" ]; then
            echo "⚠️  强制停止剩余进程: $REMAINING_PIDS"
            for pid in $REMAINING_PIDS; do
                kill -KILL "$pid" 2>/dev/null || true
            done
        fi
        
        echo "✅ 所有KataGo进程已停止"
    else
        echo "ℹ️  未找到运行中的KataGo进程"
    fi
    
    # 清理所有PID文件
    if [ -d "$PID_DIR" ]; then
        echo "🧹 清理PID文件..."
        rm -f "$PID_DIR"/katago-http-*.pid
    fi
}

# 主逻辑
case "${2:-process}" in
    "docker")
        stop_docker_container
        ;;
    "all")
        stop_all_processes
        ;;
    "process"|*)
        if ! stop_process; then
            echo "🔍 尝试查找并停止所有相关进程..."
            stop_all_processes
        fi
        ;;
esac

# 检查端口占用
echo "🔍 检查端口占用情况..."
for port in 8080 8081; do
    if netstat -tlnp 2>/dev/null | grep ":$port " >/dev/null; then
        echo "⚠️  端口 $port 仍被占用:"
        netstat -tlnp 2>/dev/null | grep ":$port " || true
    else
        echo "✅ 端口 $port 已释放"
    fi
done

echo "🏁 停止操作完成"
echo ""
echo "💡 使用方法:"
echo "   ./stop_http_server.sh [instance_id] [method]"
echo "   method: process (默认) | docker | all"
echo "   例如: ./stop_http_server.sh 1 docker"