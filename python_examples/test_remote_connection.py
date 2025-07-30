#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试远程连接功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from step_by_step_claude_gpu import CONNECTION_CONFIG, configure_connection, check_connection, analyze_position

def test_connection():
    """测试连接功能"""
    print("🧪 测试连接功能")
    
    # 测试本地模式
    print("\n1. 测试本地Docker模式:")
    CONNECTION_CONFIG['use_remote'] = False
    if check_connection():
        print("✅ 本地Docker连接成功")
    else:
        print("❌ 本地Docker连接失败")
    
    # 测试远程模式
    print("\n2. 测试远程模式:")
    CONNECTION_CONFIG['use_remote'] = True
    CONNECTION_CONFIG['remote_host'] = 'localhost'
    CONNECTION_CONFIG['remote_port'] = 8080
    if check_connection():
        print("✅ 远程连接成功")
    else:
        print("❌ 远程连接失败（这是正常的，因为容器没有HTTP API）")
    
    print("\n✅ 连接测试完成")

def test_simple_analysis():
    """测试简单分析"""
    print("\n🧪 测试简单分析功能")
    
    # 使用本地模式
    CONNECTION_CONFIG['use_remote'] = False
    
    # 简单的两手棋
    moves = [['B', 'dp'], ['W', 'pd']]
    
    print("分析第1手: B dp")
    result = analyze_position(moves, 1, debug=True)
    if result.get('error'):
        print(f"❌ 分析失败: {result['error']}")
    else:
        print(f"✅ 分析成功: 胜率={result.get('winrate', 0):.1f}%, visits={result.get('visits', 0)}")

if __name__ == "__main__":
    test_connection()
    test_simple_analysis()