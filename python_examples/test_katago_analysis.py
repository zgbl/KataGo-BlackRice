#!/usr/bin/env python3
"""
简单的KataGo分析测试脚本
直接与Docker容器中的KataGo分析引擎交互
"""

import json
import subprocess
import time

def test_katago_analysis():
    """测试KataGo分析引擎"""
    
    # 示例SGF内容 - 一个简单的开局
    test_moves = [
        ["B", "D4"],   # 黑棋小目
        ["W", "Q16"],  # 白棋星位
        ["B", "P4"],   # 黑棋小目
        ["W", "D16"]   # 白棋星位
    ]
    
    # 构建分析查询
    query = {
        "id": "test_analysis_1",
        "moves": test_moves,
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [len(test_moves)],  # 分析最后一手
        "maxVisits": 1000,
        "includeOwnership": True,
        "includePolicy": True,
        "includeMovesOwnership": False
    }
    
    print("=== KataGo 分析引擎测试 ===")
    print(f"测试局面: {test_moves}")
    print(f"发送查询: {json.dumps(query, indent=2)}")
    print("\n正在连接Docker容器...")
    
    try:
        # 使用docker exec连接到正在运行的容器
        cmd = [
            "docker", "exec", "-i", "katago-analysis",
            "/bin/bash", "-c", 
            "echo '{}' | katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz".format(
                json.dumps(query).replace("'", "\\'")
            )
        ]
        
        print("执行命令:", " ".join(cmd))
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"错误: {result.stderr}")
            return
            
        # 解析结果
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if line.strip() and line.startswith('{'):
                try:
                    analysis_result = json.loads(line)
                    print("\n=== 分析结果 ===")
                    print(f"查询ID: {analysis_result['id']}")
                    
                    if 'moveInfos' in analysis_result:
                        print("\n前5个最佳着法:")
                        for i, move_info in enumerate(analysis_result['moveInfos'][:5]):
                            move = move_info.get('move', 'pass')
                            winrate = move_info.get('winrate', 0)
                            visits = move_info.get('visits', 0)
                            prior = move_info.get('prior', 0)
                            print(f"  {i+1}. {move:>4} - 胜率: {winrate:.3f}, 访问: {visits:>4}, 先验: {prior:.3f}")
                    
                    if 'rootInfo' in analysis_result:
                        root_info = analysis_result['rootInfo']
                        print(f"\n根节点信息:")
                        print(f"  总访问次数: {root_info.get('visits', 0)}")
                        print(f"  胜率: {root_info.get('winrate', 0):.3f}")
                        print(f"  得分: {root_info.get('scoreMean', 0):.1f}")
                        
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"原始输出: {line}")
        
        print("未找到有效的JSON分析结果")
        print(f"完整输出:\n{result.stdout}")
        
    except subprocess.TimeoutExpired:
        print("分析超时")
    except Exception as e:
        print(f"执行错误: {e}")

def test_simple_position():
    """测试一个更简单的局面"""
    print("\n=== 测试空棋盘分析 ===")
    
    query = {
        "id": "empty_board",
        "moves": [],
        "rules": "tromp-taylor", 
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 500
    }
    
    try:
        # 直接通过stdin发送到容器
        cmd = ["docker", "exec", "-i", "katago-analysis", "katago", "analysis", 
               "-config", "/app/configs/analysis_example.cfg", 
               "-model", "/app/models/model.bin.gz"]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 发送查询
        query_json = json.dumps(query)
        print(f"发送查询: {query_json}")
        
        stdout, stderr = process.communicate(input=query_json + "\n", timeout=30)
        
        if stderr:
            print(f"错误输出: {stderr}")
            
        print(f"标准输出: {stdout}")
        
        # 解析结果
        for line in stdout.split('\n'):
            if line.strip() and line.startswith('{'):
                try:
                    result = json.loads(line)
                    print("\n=== 空棋盘分析结果 ===")
                    if 'moveInfos' in result and result['moveInfos']:
                        best_move = result['moveInfos'][0]
                        print(f"推荐开局: {best_move.get('move', 'pass')}")
                        print(f"胜率: {best_move.get('winrate', 0):.3f}")
                    break
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    # 首先测试简单局面
    test_simple_position()
    
    # 然后测试复杂局面
    test_katago_analysis()