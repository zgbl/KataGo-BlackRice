#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试KataGo HTTP连接
"""

import requests
import json
import time

def test_http_connection():
    """测试HTTP连接"""
    url = "http://localhost:8080"
    
    print(f"🧪 测试连接到 {url}")
    
    try:
        # 简单的GET请求测试
        response = requests.get(url, timeout=5)
        print(f"✅ HTTP连接成功: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 连接被拒绝 - 服务器可能没有运行HTTP服务")
        return False
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

def test_katago_analysis_post():
    """测试KataGo分析POST请求"""
    url = "http://localhost:8080/analyze"
    
    # 简单的分析请求
    data = {
        "id": "test",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 100
    }
    
    print(f"🧪 测试POST请求到 {url}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"✅ POST请求成功: {response.status_code}")
        if response.text:
            print(f"响应内容: {response.text[:200]}...")
        return True
    except Exception as e:
        print(f"❌ POST请求失败: {e}")
        return False

if __name__ == "__main__":
    print("=== KataGo HTTP连接测试 ===")
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    # 测试基本连接
    if test_http_connection():
        # 测试分析请求
        test_katago_analysis_post()
    
    print("\n=== 测试完成 ===")