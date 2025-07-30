#!/bin/bash

# KataGo诊断脚本
# 检查KataGo版本和支持的命令

echo "🔍 KataGo诊断工具"
echo "=================="

# 检查KataGo可执行文件
KATAGO_BIN="/app/bin/katago"
if [ ! -f "$KATAGO_BIN" ]; then
    echo "❌ KataGo可执行文件不存在: $KATAGO_BIN"
    exit 1
fi

echo "✅ 找到KataGo可执行文件: $KATAGO_BIN"

# 检查版本
echo ""
echo "📋 KataGo版本信息:"
$KATAGO_BIN version 2>/dev/null || echo "⚠️  无法获取版本信息"

# 检查支持的命令
echo ""
echo "📋 支持的命令:"
$KATAGO_BIN help 2>/dev/null || echo "⚠️  无法获取帮助信息"

# 检查模型文件
echo ""
echo "📋 检查模型文件:"
MODEL_FILE="/app/models/model.bin.gz"
if [ -f "$MODEL_FILE" ]; then
    SIZE=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
    echo "✅ 模型文件存在: $MODEL_FILE (大小: $SIZE)"
else
    echo "❌ 模型文件不存在: $MODEL_FILE"
    echo "📁 /app/models 目录内容:"
    ls -la /app/models/ 2>/dev/null || echo "目录不存在"
fi

# 检查配置文件
echo ""
echo "📋 检查配置文件:"
CONFIG_FILE="/app/configs/katago_http.cfg"
if [ -f "$CONFIG_FILE" ]; then
    echo "✅ 配置文件存在: $CONFIG_FILE"
    echo "📄 配置文件内容预览:"
    head -20 "$CONFIG_FILE"
else
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "📁 /app/configs 目录内容:"
    ls -la /app/configs/ 2>/dev/null || echo "目录不存在"
fi

# 测试KataGo analysis命令（不启动HTTP）
echo ""
echo "📋 测试KataGo analysis命令（5秒超时）:"
timeout 5s $KATAGO_BIN analysis -config "$CONFIG_FILE" -model "$MODEL_FILE" -quit-without-waiting 2>&1 | head -10

# 检查是否支持http命令
echo ""
echo "📋 检查HTTP命令支持:"
if $KATAGO_BIN help 2>/dev/null | grep -q "http"; then
    echo "✅ 支持http命令"
else
    echo "❌ 不支持http命令，此版本可能不支持HTTP服务器模式"
    echo "💡 建议使用analysis命令配合外部HTTP包装器"
fi

# 系统信息
echo ""
echo "📋 系统信息:"
echo "操作系统: $(uname -a)"
echo "CPU核心数: $(nproc)"
echo "内存使用: $(free -h | head -2)"

# GPU信息
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "📋 GPU信息:"
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader,nounits
else
    echo ""
    echo "⚠️  未检测到NVIDIA GPU"
fi

echo ""
echo "🏁 诊断完成"