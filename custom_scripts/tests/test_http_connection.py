#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP连接测试脚本
测试KataGo HTTP服务是否正常工作
"""

import requests
import json
import time
import sys

def test_http_connection(host="localhost", port=8080):
    """测试HTTP连接"""
    url = f"http://{host}:{port}"
    print(f"🔗 测试HTTP连接: {url}")
    
    try:
        # 简单的连接测试
        response = requests.get(url, timeout=5)
        print(f"✓ HTTP连接成功，状态码: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 连接超时: {url}")
        return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

def test_katago_analysis_post(host="localhost", port=8080):
    """测试KataGo分析POST请求"""
    url = f"http://{host}:{port}/analyze"
    print(f"\n🎯 测试KataGo分析请求: {url}")
    
    # 构造分析请求
    query = {
        "id": "test_http",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 100
    }
    
    try:
        print(f"发送请求: {json.dumps(query, indent=2)}")
        
        response = requests.post(
            url, 
            json=query,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✓ 分析成功!")
                print(f"响应数据: {json.dumps(result, indent=2)[:500]}...")
                return True
            except json.JSONDecodeError:
                print(f"❌ 响应不是有效的JSON")
                print(f"响应内容: {response.text[:200]}...")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求错误: {e}")
        return False

def check_container_status():
    """检查容器状态"""
    import subprocess
    
    print("\n📋 检查KataGo容器状态...")
    
    try:
        # 检查容器是否运行
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("容器状态:")
            print(result.stdout)
            return True
        else:
            print(f"❌ 无法获取容器状态: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 检查容器状态失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 KataGo HTTP连接测试")
    print("=" * 50)
    
    # 检查容器状态
    check_container_status()
    
    # 等待服务启动
    print("\n⏳ 等待服务启动...")
    time.sleep(3)
    
    # 测试基本连接
    connection_ok = test_http_connection()
    
    if connection_ok:
        # 测试分析请求
        analysis_ok = test_katago_analysis_post()
        
        if analysis_ok:
            print("\n🎉 所有HTTP测试通过! KataGo HTTP服务正常工作.")
            return True
        else:
            print("\n⚠️ HTTP连接正常，但分析请求失败.")
            return False
    else:
        print("\n❌ HTTP连接失败. 请检查:")
        print("   1. KataGo容器是否正在运行")
        print("   2. 端口8080是否正确映射")
        print("   3. KataGo是否以HTTP模式启动")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)