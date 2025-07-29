#!/usr/bin/env python3
"""
简化版KataGo测试 - 用于诊断Docker通信问题
"""

import json
import subprocess
import time

def test_docker_connection():
    """测试Docker容器连接"""
    print("=== 测试Docker容器连接 ===")
    
    try:
        # 1. 检查容器是否运行
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-gpu"],
            capture_output=True, text=True, timeout=10
        )
        print(f"容器状态检查: {result.stdout.strip()}")
        
        # 2. 测试容器内部命令
        result = subprocess.run(
            ["docker", "exec", "katago-gpu", "ls", "/app"],
            capture_output=True, text=True, timeout=10
        )
        print(f"容器内部文件: {result.stdout.strip()}")
        
        # 3. 测试KataGo可执行文件
        result = subprocess.run(
            ["docker", "exec", "katago-gpu", "which", "katago"],
            capture_output=True, text=True, timeout=10
        )
        print(f"KataGo路径: {result.stdout.strip()}")
        
        # 4. 测试KataGo版本
        result = subprocess.run(
            ["docker", "exec", "katago-gpu", "katago", "version"],
            capture_output=True, text=True, timeout=15
        )
        print(f"KataGo版本: {result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"连接测试失败: {e}")
        return False

def test_simple_analysis():
    """测试最简单的分析"""
    print("\n=== 测试简单分析 ===")
    
    # 最简单的查询
    query = {
        "id": "simple_test",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 50  # 很少的访问次数
    }
    
    query_json = json.dumps(query)
    print(f"发送查询: {query_json}")
    
    try:
        # 使用更简单的命令格式
        cmd = [
            "docker", "exec", "-i", "katago-gpu",
            "sh", "-c", 
            f"echo '{query_json}' | timeout 30 katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz"
        ]
        
        print("执行命令...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        print(f"返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"错误输出: {result.stderr}")
        
        if result.returncode == 0:
            # 查找JSON响应
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        print(f"✅ 分析成功! ID: {response.get('id')}")
                        if 'moveInfos' in response and response['moveInfos']:
                            best_move = response['moveInfos'][0]
                            print(f"推荐着法: {best_move['move']}")
                            print(f"胜率: {best_move['winrate']:.3f}")
                        return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ 分析失败")
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ 命令超时")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return False

def test_direct_katago():
    """直接测试KataGo命令"""
    print("\n=== 直接测试KataGo ===")
    
    try:
        # 直接在容器中运行KataGo help
        result = subprocess.run(
            ["docker", "exec", "katago-gpu", "katago", "help"],
            capture_output=True, text=True, timeout=10
        )
        
        print(f"KataGo help输出: {result.stdout[:500]}...")
        
        # 测试分析模式帮助
        result = subprocess.run(
            ["docker", "exec", "katago-analysis", "katago", "analysis", "-help"],
            capture_output=True, text=True, timeout=10
        )
        
        print(f"分析模式帮助: {result.stdout[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"直接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 KataGo Docker 诊断工具")
    print("=" * 40)
    
    # 运行所有测试
    tests = [
        ("Docker连接", test_docker_connection),
        ("直接KataGo", test_direct_katago),
        ("简单分析", test_simple_analysis)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            print(f"{'✅' if success else '❌'} {test_name}: {'通过' if success else '失败'}")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {e}")
        
        time.sleep(1)  # 短暂暂停
    
    print(f"\n{'='*40}")
    print("诊断完成")

if __name__ == "__main__":
    main()