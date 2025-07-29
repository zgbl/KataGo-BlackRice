#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo GPU 直接测试脚本
绕过 docker-compose 问题，直接使用 docker run 测试 GPU 功能
"""

import subprocess
import json
import sys
import os

def run_docker_command(cmd, timeout=30):
    """运行 Docker 命令"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def test_gpu_container():
    """测试 GPU 容器启动"""
    print("🔧 测试 KataGo GPU 容器...")
    
    # 停止并删除现有容器
    print("清理现有容器...")
    subprocess.run("docker stop katago-gpu-test 2>nul", shell=True)
    subprocess.run("docker rm katago-gpu-test 2>nul", shell=True)
    
    # 获取当前目录的绝对路径
    current_dir = os.path.abspath(".")
    models_dir = os.path.join(current_dir, "models")
    logs_dir = os.path.join(current_dir, "logs")
    analysis_logs_dir = os.path.join(current_dir, "analysis_logs")
    configs_dir = os.path.join(current_dir, "configs")
    
    # 构建 Docker 运行命令
    docker_cmd = f"""
    docker run -d \
        --name katago-gpu-test \
        --gpus all \
        -v "{models_dir}:/app/models:ro" \
        -v "{logs_dir}:/app/logs" \
        -v "{analysis_logs_dir}:/app/analysis_logs" \
        -v "{configs_dir}:/app/configs/custom:ro" \
        -e TZ=Asia/Shanghai \
        -e NVIDIA_VISIBLE_DEVICES=all \
        -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
        -p 8080:8080 \
        katago-blackrice-katago-gpu:latest \
        /app/start_analysis.sh
    """.replace('\n', ' ').strip()
    
    print(f"执行命令: {docker_cmd}")
    
    # 尝试启动容器
    returncode, stdout, stderr = run_docker_command(docker_cmd, timeout=60)
    
    if returncode == 0:
        container_id = stdout.strip()
        print(f"✅ GPU 容器启动成功! Container ID: {container_id[:12]}")
        
        # 等待容器初始化
        print("等待容器初始化...")
        import time
        time.sleep(5)
        
        # 检查容器状态
        status_cmd = "docker ps --filter name=katago-gpu-test --format 'table {{.Names}}\t{{.Status}}'"
        returncode, stdout, stderr = run_docker_command(status_cmd)
        print(f"容器状态: {stdout}")
        
        # 测试分析功能
        test_analysis()
        
        return True
    else:
        print(f"❌ GPU 容器启动失败!")
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        return False

def test_analysis():
    """测试分析功能"""
    print("\n🧪 测试 KataGo 分析功能...")
    
    # 简单的分析查询
    query = {
        "id": "test_gpu",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 100
    }
    
    query_json = json.dumps(query)
    
    # 发送查询到容器
    analysis_cmd = f'echo \'{query_json}\' | docker exec -i katago-gpu-test /usr/local/bin/katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz'
    
    print(f"发送分析查询: {query['id']}")
    returncode, stdout, stderr = run_docker_command(analysis_cmd, timeout=60)
    
    if returncode == 0 and stdout.strip():
        try:
            result = json.loads(stdout.strip())
            if 'moveInfos' in result and len(result['moveInfos']) > 0:
                move_info = result['moveInfos'][0]
                winrate = move_info.get('winrate', 0)
                visits = move_info.get('visits', 0)
                print(f"✅ GPU 分析成功!")
                print(f"   胜率: {winrate:.3f}")
                print(f"   访问次数: {visits}")
                print(f"   推荐着法: {move_info.get('move', 'N/A')}")
                return True
            else:
                print(f"❌ 分析结果格式异常: {result}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"原始输出: {stdout}")
    else:
        print(f"❌ 分析失败!")
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
    
    return False

def cleanup():
    """清理测试容器"""
    print("\n🧹 清理测试容器...")
    subprocess.run("docker stop katago-gpu-test 2>nul", shell=True)
    subprocess.run("docker rm katago-gpu-test 2>nul", shell=True)
    print("清理完成")

def main():
    """主函数"""
    print("=== KataGo GPU 直接测试 ===")
    print("此脚本绕过 docker-compose 问题，直接测试 GPU 功能\n")
    
    try:
        # 检查 GPU 镜像是否存在
        check_cmd = "docker images katago-blackrice-katago-gpu:latest --format 'table {{.Repository}}\t{{.Tag}}'"
        returncode, stdout, stderr = run_docker_command(check_cmd)
        
        if "katago-blackrice-katago-gpu" not in stdout:
            print("❌ GPU 镜像不存在，请先构建镜像:")
            print("   docker-compose build katago-gpu")
            return False
        
        print("✅ GPU 镜像已存在")
        
        # 测试 GPU 容器
        success = test_gpu_container()
        
        if success:
            print("\n🎉 GPU 测试完全成功!")
            print("\n📋 使用说明:")
            print("1. GPU 容器可以正常启动和运行")
            print("2. 可以使用以下命令连接到容器:")
            print("   docker exec -it katago-gpu-test /bin/bash")
            print("3. 容器将在后台持续运行，可用于分析")
            print("4. 要停止容器: docker stop katago-gpu-test")
        else:
            print("\n❌ GPU 测试失败")
            print("\n💡 建议:")
            print("1. 检查 NVIDIA 驱动是否正确安装")
            print("2. 确认 Docker Desktop 已启用 GPU 支持")
            print("3. 尝试重启 Docker Desktop")
            print("4. 使用 CPU 版本作为替代方案")
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    finally:
        # 询问是否清理
        try:
            choice = input("\n是否清理测试容器? (y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                cleanup()
            else:
                print("保留测试容器，可手动清理")
        except:
            pass

if __name__ == "__main__":
    main()