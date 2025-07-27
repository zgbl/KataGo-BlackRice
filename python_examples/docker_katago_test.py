#!/usr/bin/env python3
"""
直接与Docker容器中运行的KataGo分析引擎进行交互的测试脚本
"""

import json
import subprocess
import time
import sys

def send_query_to_docker(query_data, container_name="katago-analysis", timeout=60):
    """
    向Docker容器中的KataGo发送查询
    """
    try:
        # 将查询转换为JSON字符串
        query_json = json.dumps(query_data)
        print(f"发送查询: {query_json}")
        
        # 构建docker exec命令
        cmd = [
            "docker", "exec", "-i", container_name,
            "/bin/bash", "-c",
            f"echo '{query_json}' | katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz"
        ]
        
        print("正在连接Docker容器...")
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            print(f"命令执行失败: {result.stderr}")
            return None
            
        # 解析结果
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            line = line.strip()
            if line and line.startswith('{'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
                    
        print("未找到有效的JSON响应")
        print(f"原始输出: {result.stdout}")
        return None
        
    except subprocess.TimeoutExpired:
        print(f"查询超时 ({timeout}秒)")
        return None
    except Exception as e:
        print(f"查询失败: {e}")
        return None

def test_empty_board():
    """测试空棋盘分析"""
    print("\n=== 测试空棋盘分析 ===")
    
    query = {
        "id": "empty_board_test",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 100  # 减少访问次数以加快测试
    }
    
    result = send_query_to_docker(query, timeout=30)
    
    if result:
        print("✅ 空棋盘分析成功!")
        print(f"查询ID: {result['id']}")
        if 'moveInfos' in result and result['moveInfos']:
            best_move = result['moveInfos'][0]
            print(f"推荐着法: {best_move['move']}")
            print(f"胜率: {best_move['winrate']:.3f}")
            print(f"访问次数: {best_move['visits']}")
        return True
    else:
        print("❌ 空棋盘分析失败")
        return False

def test_position_analysis():
    """测试局面分析"""
    print("\n=== 测试局面分析 ===")
    
    # 测试一个简单的开局
    moves = [["B", "D4"], ["W", "Q16"]]
    
    query = {
        "id": "position_test",
        "moves": moves,
        "rules": "tromp-taylor", 
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [len(moves)],
        "maxVisits": 200,
        "includeOwnership": True,
        "includePolicy": True
    }
    
    result = send_query_to_docker(query, timeout=45)
    
    if result:
        print("✅ 局面分析成功!")
        print(f"当前局面: {moves}")
        print(f"查询ID: {result['id']}")
        
        if 'moveInfos' in result and result['moveInfos']:
            print("前3个推荐着法:")
            for i, move_info in enumerate(result['moveInfos'][:3]):
                print(f"  {i+1}. {move_info['move']} - 胜率: {move_info['winrate']:.3f}, 访问: {move_info['visits']}")
        return True
    else:
        print("❌ 局面分析失败")
        return False

def check_docker_container():
    """检查Docker容器状态"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-analysis", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "katago-analysis" in result.stdout:
            print("✅ Docker容器 katago-analysis 正在运行")
            return True
        else:
            print("❌ Docker容器 katago-analysis 未运行")
            print("请先运行: docker-compose up katago-analysis")
            return False
            
    except Exception as e:
        print(f"检查Docker容器失败: {e}")
        return False

def main():
    """主测试函数"""
    print("KataGo Docker 分析引擎测试")
    print("=" * 40)
    
    # 检查Docker容器状态
    if not check_docker_container():
        sys.exit(1)
    
    # 运行测试
    tests_passed = 0
    total_tests = 2
    
    if test_empty_board():
        tests_passed += 1
        
    if test_position_analysis():
        tests_passed += 1
    
    # 输出测试结果
    print("\n" + "=" * 40)
    print(f"测试完成: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过! KataGo分析引擎工作正常")
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main()