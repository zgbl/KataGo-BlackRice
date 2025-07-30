#!/bin/bash

echo "=== 设置KataGo配置文件 ==="

# 创建配置目录
mkdir -p ../../configs

# 复制并修改分析引擎配置
cp ../../cpp/tests/data/configs/analysis_example.cfg ../../configs/analysis_docker.cfg

# 修改配置以适应Docker环境
cat >> ../../configs/analysis_docker.cfg << 'EOF'

# Docker环境特定配置
logDir = /app/analysis_logs
maxVisits = 1000
numAnalysisThreads = 4
numSearchThreadsPerAnalysisThread = 4
nnMaxBatchSize = 32
nnCacheSizePowerOfTwo = 20
EOF

echo "配置文件已创建: ../../configs/analysis_docker.cfg"

# 创建开发用的配置文件
cat > ../../configs/analysis_dev.cfg << 'EOF'
# 开发环境配置 - 更快的响应时间
logDir = /app/analysis_logs
maxVisits = 500
numAnalysisThreads = 2
numSearchThreadsPerAnalysisThread = 8
nnMaxBatchSize = 16
nnCacheSizePowerOfTwo = 18
reportAnalysisWinratesAs = BLACK
EOF

echo "开发配置文件已创建: ../../configs/analysis_dev.cfg"