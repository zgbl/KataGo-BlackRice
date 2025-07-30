#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CUDA 12.9 快速测试脚本
使用官方NVIDIA CUDA镜像测试GPU兼容性
"""

import subprocess
import sys
import time

def run_command(cmd, timeout=30):
    """运行命令"""
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

def test_cuda_versions():
    """测试不同CUDA版本的兼容性"""
    print("🔧 测试CUDA 12.9兼容性...\n")
    
    # 测试的CUDA镜像版本
    cuda_images = [
        "nvidia/cuda:12.9.1-base-ubuntu22.04",
        "nvidia/cuda:12.9.1-runtime-ubuntu22.04",
        "nvidia/cuda:12.9.1-devel-ubuntu22.04"
    ]
    
    successful_images = []
    
    for image in cuda_images:
        print(f"📦 测试镜像: {image}")
        
        # 清理可能存在的容器
        subprocess.run(f"docker stop cuda-test 2>nul", shell=True)
        subprocess.run(f"docker rm cuda-test 2>nul", shell=True)
        
        # 测试GPU访问
        test_cmd = f"docker run --rm --name cuda-test --gpus all {image} nvidia-smi"
        
        print(f"   执行: {test_cmd}")
        returncode, stdout, stderr = run_command(test_cmd, timeout=60)
        
        if returncode == 0:
            print(f"   ✅ 成功! GPU信息:")
            # 提取GPU信息
            lines = stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line:
                    print(f"      {line.strip()}")
                elif 'Driver Version' in line:
                    print(f"      {line.strip()}")
            successful_images.append(image)
            print()
        else:
            print(f"   ❌ 失败: {stderr.strip()}")
            print()
    
    return successful_images

def test_cuda_compilation():
    """测试CUDA编译环境"""
    print("🔨 测试CUDA编译环境...\n")
    
    # 使用devel镜像测试编译
    devel_image = "nvidia/cuda:12.9.1-devel-ubuntu22.04"
    
    # 清理容器
    subprocess.run(f"docker stop cuda-compile-test 2>nul", shell=True)
    subprocess.run(f"docker rm cuda-compile-test 2>nul", shell=True)
    
    # 创建简单的CUDA测试程序
    cuda_test_code = '''
#include <cuda_runtime.h>
#include <iostream>

int main() {
    int deviceCount;
    cudaGetDeviceCount(&deviceCount);
    std::cout << "CUDA Devices: " << deviceCount << std::endl;
    
    if (deviceCount > 0) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, 0);
        std::cout << "Device 0: " << prop.name << std::endl;
        std::cout << "Compute Capability: " << prop.major << "." << prop.minor << std::endl;
    }
    
    return 0;
}
'''
    
    # 创建测试容器并编译
    compile_cmd = f'''
docker run -d --name cuda-compile-test --gpus all {devel_image} sleep 300
'''.strip()
    
    print(f"启动编译容器...")
    returncode, stdout, stderr = run_command(compile_cmd)
    
    if returncode != 0:
        print(f"❌ 无法启动编译容器: {stderr}")
        return False
    
    # 等待容器启动
    time.sleep(2)
    
    # 创建测试文件
    create_file_cmd = f'echo \'{cuda_test_code}\' | docker exec -i cuda-compile-test tee /tmp/test.cu'
    returncode, stdout, stderr = run_command(create_file_cmd)
    
    if returncode != 0:
        print(f"❌ 无法创建测试文件: {stderr}")
        return False
    
    # 编译测试
    compile_test_cmd = "docker exec cuda-compile-test nvcc /tmp/test.cu -o /tmp/test"
    print(f"编译CUDA程序...")
    returncode, stdout, stderr = run_command(compile_test_cmd, timeout=60)
    
    if returncode == 0:
        print(f"✅ CUDA编译成功!")
        
        # 运行测试程序
        run_test_cmd = "docker exec cuda-compile-test /tmp/test"
        returncode, stdout, stderr = run_command(run_test_cmd)
        
        if returncode == 0:
            print(f"✅ CUDA程序运行成功!")
            print(f"输出: {stdout.strip()}")
            return True
        else:
            print(f"❌ CUDA程序运行失败: {stderr}")
    else:
        print(f"❌ CUDA编译失败: {stderr}")
    
    # 清理
    subprocess.run(f"docker stop cuda-compile-test 2>nul", shell=True)
    subprocess.run(f"docker rm cuda-compile-test 2>nul", shell=True)
    
    return False

def main():
    """主函数"""
    print("=== CUDA 12.9 兼容性测试 ===")
    print("测试您的系统是否支持CUDA 12.9\n")
    
    try:
        # 测试基础GPU访问
        successful_images = test_cuda_versions()
        
        if successful_images:
            print(f"🎉 成功的镜像: {len(successful_images)}/{3}")
            for img in successful_images:
                print(f"   ✅ {img}")
            print()
            
            # 如果devel镜像可用，测试编译
            if "nvidia/cuda:12.9.1-devel-ubuntu22.04" in successful_images:
                compile_success = test_cuda_compilation()
                
                if compile_success:
                    print("\n🎉 CUDA 12.9 完全兼容!")
                    print("\n📋 建议:")
                    print("1. 您的系统支持CUDA 12.9")
                    print("2. 可以安全地使用CUDA 12.9镜像构建KataGo")
                    print("3. 推荐使用: nvidia/cuda:12.9.1-devel-ubuntu22.04")
                else:
                    print("\n⚠️  CUDA运行时可用，但编译环境有问题")
                    print("建议使用runtime镜像而不是从源码编译")
            else:
                print("\n⚠️  CUDA 12.9 devel镜像不可用")
                print("建议降级到CUDA 11.8或使用预编译版本")
        else:
            print("❌ 没有CUDA 12.9镜像可以正常工作")
            print("\n💡 建议:")
            print("1. 检查NVIDIA驱动版本是否支持CUDA 12.9")
            print("2. 考虑降级到CUDA 11.8")
            print("3. 更新NVIDIA驱动到最新版本")
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    finally:
        # 清理所有测试容器
        print("\n🧹 清理测试容器...")
        subprocess.run("docker stop cuda-test cuda-compile-test 2>nul", shell=True)
        subprocess.run("docker rm cuda-test cuda-compile-test 2>nul", shell=True)
        print("清理完成")

if __name__ == "__main__":
    main()