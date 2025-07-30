# KataGo GPU 启动修复脚本

Write-Host "=== KataGo GPU 启动修复脚本 ===" -ForegroundColor Blue

# 1. 停止现有容器
Write-Host "`n1. 清理现有容器..." -ForegroundColor Yellow
docker-compose down 2>$null
docker container prune -f 2>$null

# 2. 尝试不同的启动方法
Write-Host "`n2. 尝试直接 Docker 运行（绕过 docker-compose）..." -ForegroundColor Yellow

# 检查镜像是否存在
$image = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "katago-blackrice-katago-gpu"
if ($image) {
    Write-Host "找到镜像: $image" -ForegroundColor Green
    
    # 尝试直接运行，不使用 deploy 配置
    Write-Host "尝试启动容器..." -ForegroundColor Cyan
    
    $containerId = docker run -d `
        --name katago-gpu-direct `
        --gpus all `
        -v "${PWD}/../../models:/app/models:ro" `
        -v "${PWD}/../../logs:/app/logs" `
        -v "${PWD}/../../analysis_logs:/app/analysis_logs" `
        -v "${PWD}/../../custom_scripts/configs:/app/configs/custom:ro" `
        -e TZ=Asia/Shanghai `
        -e NVIDIA_VISIBLE_DEVICES=all `
        -e NVIDIA_DRIVER_CAPABILITIES=compute,utility `
        --restart unless-stopped `
        katago-blackrice-katago-gpu:latest `
        /app/start_analysis.sh 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 容器启动成功! Container ID: $containerId" -ForegroundColor Green
        
        # 等待几秒钟让容器初始化
        Write-Host "等待容器初始化..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # 检查容器状态
        $status = docker ps --filter "name=katago-gpu-direct" --format "table {{.Names}}\t{{.Status}}"
        Write-Host "容器状态:" -ForegroundColor Cyan
        Write-Host $status
        
        # 显示日志
        Write-Host "`n容器日志:" -ForegroundColor Cyan
        docker logs katago-gpu-direct
        
        Write-Host "`n使用以下命令查看实时日志:" -ForegroundColor Yellow
        Write-Host "docker logs -f katago-gpu-direct" -ForegroundColor White
        
        Write-Host "`n使用以下命令停止容器:" -ForegroundColor Yellow
        Write-Host "docker stop katago-gpu-direct && docker rm katago-gpu-direct" -ForegroundColor White
        
    } else {
        Write-Host "✗ 容器启动失败: $containerId" -ForegroundColor Red
        
        # 尝试备选方案
        Write-Host "`n尝试备选方案: 使用 --privileged 模式..." -ForegroundColor Yellow
        
        $containerId2 = docker run -d `
            --name katago-gpu-privileged `
            --privileged `
            --gpus all `
            -v "${PWD}/models:/app/models:ro" `
            -v "${PWD}/logs:/app/logs" `
            -v "${PWD}/analysis_logs:/app/analysis_logs" `
            -v "${PWD}/configs:/app/configs/custom:ro" `
            -e TZ=Asia/Shanghai `
            -e NVIDIA_VISIBLE_DEVICES=all `
            -e NVIDIA_DRIVER_CAPABILITIES=compute,utility `
            katago-blackrice-katago-gpu:latest `
            /app/start_analysis.sh 2>&1
            
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 特权模式启动成功! Container ID: $containerId2" -ForegroundColor Green
            Start-Sleep -Seconds 5
            docker logs katago-gpu-privileged
        } else {
            Write-Host "✗ 特权模式也失败了: $containerId2" -ForegroundColor Red
            
            # 最后的尝试：CPU 模式测试
            Write-Host "`n最后尝试: 启动 CPU 版本验证基本功能..." -ForegroundColor Yellow
            docker run -d --name katago-cpu-test `
                -v "${PWD}/models:/app/models:ro" `
                -v "${PWD}/logs:/app/logs" `
                -v "${PWD}/analysis_logs:/app/analysis_logs" `
                katago-blackrice-katago-cpu:latest `
                /app/start_analysis.sh 2>&1
                
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ CPU 版本可以正常启动，问题确实是 GPU 相关" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "✗ 未找到 katago-blackrice-katago-gpu 镜像" -ForegroundColor Red
    Write-Host "请先运行: docker-compose build katago-gpu" -ForegroundColor Yellow
}

Write-Host "`n=== 修复脚本完成 ===" -ForegroundColor Blue