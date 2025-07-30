#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP服务连接测试脚本
测试HTTP API的连接性和基本功能

使用方法:
    python test_connection.py [--host HOST] [--port PORT] [--timeout TIMEOUT]
"""

import argparse
import json
import requests
import time
import sys
from typing import Dict, Any, Optional


class KataGoHTTPTester:
    """KataGo HTTP服务测试器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        print("🏥 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ 健康检查通过")
                try:
                    data = response.json()
                    print(f"📊 服务状态: {json.dumps(data, indent=2)}")
                except:
                    print(f"📊 服务响应: {response.text}")
                return True
            else:
                print(f"❌ 健康检查失败: HTTP {response.status_code}")
                print(f"📄 响应内容: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 健康检查连接失败: {e}")
            return False
    
    def test_basic_analysis(self) -> bool:
        """测试基本分析功能"""
        print("🧠 测试基本分析功能...")
        
        # 基本分析请求
        analysis_request = {
            "id": "test_analysis_1",
            "moves": [],  # 空棋盘
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [0],
            "maxVisits": 100
        }
        
        try:
            print(f"📤 发送分析请求: {json.dumps(analysis_request, indent=2)}")
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ 分析请求成功")
                try:
                    data = response.json()
                    print(f"📊 分析结果: {json.dumps(data, indent=2)[:500]}...")
                    
                    # 验证响应格式
                    if "id" in data and data["id"] == analysis_request["id"]:
                        print("✅ 响应ID匹配")
                    if "moveInfos" in data:
                        print(f"✅ 找到 {len(data['moveInfos'])} 个移动信息")
                    if "rootInfo" in data:
                        print("✅ 找到根节点信息")
                        
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ 响应JSON解析失败: {e}")
                    print(f"📄 原始响应: {response.text[:500]}...")
                    return False
            else:
                print(f"❌ 分析请求失败: HTTP {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 分析请求连接失败: {e}")
            return False
    
    def test_complex_analysis(self) -> bool:
        """测试复杂分析功能"""
        print("🎯 测试复杂分析功能...")
        
        # 包含一些移动的分析请求
        analysis_request = {
            "id": "test_analysis_2",
            "moves": [
                ["B", "D4"],  # 黑棋下在D4
                ["W", "Q16"], # 白棋下在Q16
                ["B", "Q4"],  # 黑棋下在Q4
                ["W", "D16"]  # 白棋下在D16
            ],
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [0, 1, 2, 3, 4],
            "maxVisits": 200,
            "includeOwnership": True,
            "includePVVisits": True
        }
        
        try:
            print(f"📤 发送复杂分析请求...")
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ 复杂分析请求成功")
                try:
                    data = response.json()
                    
                    # 验证响应内容
                    if "turnInfos" in data:
                        print(f"✅ 找到 {len(data['turnInfos'])} 个回合信息")
                        
                        for i, turn_info in enumerate(data["turnInfos"]):
                            if "moveInfos" in turn_info:
                                print(f"  回合 {i}: {len(turn_info['moveInfos'])} 个候选移动")
                            if "rootInfo" in turn_info:
                                root_info = turn_info["rootInfo"]
                                if "winrate" in root_info:
                                    print(f"  回合 {i}: 胜率 {root_info['winrate']:.3f}")
                    
                    return True
                except json.JSONDecodeError as e:
                    print(f"❌ 复杂分析响应JSON解析失败: {e}")
                    return False
            else:
                print(f"❌ 复杂分析请求失败: HTTP {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 复杂分析请求连接失败: {e}")
            return False
    
    def test_performance(self) -> bool:
        """测试性能"""
        print("⚡ 测试性能...")
        
        # 简单的性能测试
        analysis_request = {
            "id": "perf_test",
            "moves": [],
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [0],
            "maxVisits": 50
        }
        
        num_requests = 5
        times = []
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/analyze",
                    json=analysis_request,
                    headers={"Content-Type": "application/json"}
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    request_time = end_time - start_time
                    times.append(request_time)
                    print(f"  请求 {i+1}: {request_time:.3f}s")
                else:
                    print(f"  请求 {i+1}: 失败 (HTTP {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"  请求 {i+1}: 连接失败 ({e})")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"📊 性能统计:")
            print(f"  平均响应时间: {avg_time:.3f}s")
            print(f"  最快响应时间: {min_time:.3f}s")
            print(f"  最慢响应时间: {max_time:.3f}s")
            print(f"  成功请求数: {len(times)}/{num_requests}")
            
            return len(times) > 0
        else:
            print("❌ 所有性能测试请求都失败了")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print(f"🚀 开始测试KataGo HTTP服务")
        print(f"🌐 目标地址: {self.base_url}")
        print(f"⏱️  超时时间: {self.timeout}s")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("基本分析", self.test_basic_analysis),
            ("复杂分析", self.test_complex_analysis),
            ("性能测试", self.test_performance)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 运行测试: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} 通过")
                else:
                    print(f"❌ {test_name} 失败")
            except Exception as e:
                print(f"💥 {test_name} 异常: {e}")
            
            print("-" * 30)
        
        print(f"\n📊 测试总结:")
        print(f"✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {total - passed}/{total}")
        print(f"📈 成功率: {passed/total*100:.1f}%")
        
        if passed == total:
            print("🎉 所有测试都通过了！")
            return True
        else:
            print("⚠️  部分测试失败，请检查服务状态")
            return False


def main():
    parser = argparse.ArgumentParser(description="KataGo HTTP服务连接测试")
    parser.add_argument("--host", default="localhost", help="服务器地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间 (默认: 30s)")
    
    args = parser.parse_args()
    
    tester = KataGoHTTPTester(args.host, args.port, args.timeout)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 测试过程中发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()