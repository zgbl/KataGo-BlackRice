#!/usr/bin/env python3
"""
交互式SGF分析测试
允许用户输入SGF内容或选择预设局面进行分析
"""

import json
import subprocess
import re

def parse_sgf_moves(sgf_content):
    """从SGF内容中解析出着法列表"""
    moves = []
    
    # 简单的SGF解析 - 查找 ;B[xx] 和 ;W[xx] 模式
    pattern = r';([BW])\[([a-s]{2}|)\]'
    matches = re.findall(pattern, sgf_content)
    
    for color, pos in matches:
        if pos:  # 非空着法
            # 将SGF坐标转换为KataGo格式
            if len(pos) == 2:
                col = chr(ord('A') + ord(pos[0]) - ord('a'))
                if col >= 'I':  # SGF中没有I，需要跳过
                    col = chr(ord(col) + 1)
                row = str(19 - (ord(pos[1]) - ord('a')))
                move_pos = col + row
            else:
                move_pos = "pass"
        else:
            move_pos = "pass"
            
        moves.append([color, move_pos])
    
    return moves

def analyze_with_katago(moves, max_visits=1000):
    """使用KataGo分析局面"""
    query = {
        "id": f"sgf_analysis_{len(moves)}",
        "moves": moves,
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [len(moves)] if moves else [0],
        "maxVisits": max_visits,
        "includeOwnership": True,
        "includePolicy": True
    }
    
    try:
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
        
        query_json = json.dumps(query)
        stdout, stderr = process.communicate(input=query_json + "\n", timeout=60)
        
        if stderr:
            print(f"警告: {stderr}")
        
        # 解析结果
        for line in stdout.split('\n'):
            if line.strip() and line.startswith('{'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        return None
        
    except Exception as e:
        print(f"分析失败: {e}")
        return None

def display_analysis_result(result, moves):
    """显示分析结果"""
    if not result:
        print("未获得分析结果")
        return
    
    print(f"\n=== 分析结果 (查询ID: {result['id']}) ===")
    print(f"分析局面: {len(moves)} 手棋")
    
    if moves:
        print("最后几手:")
        for i, (color, pos) in enumerate(moves[-5:]):
            print(f"  {len(moves)-4+i}. {color} {pos}")
    
    if 'moveInfos' in result and result['moveInfos']:
        print(f"\n推荐着法 (前5个):")
        for i, move_info in enumerate(result['moveInfos'][:5]):
            move = move_info.get('move', 'pass')
            winrate = move_info.get('winrate', 0)
            visits = move_info.get('visits', 0)
            score = move_info.get('scoreMean', 0)
            print(f"  {i+1}. {move:>4} - 胜率: {winrate:.3f}, 访问: {visits:>4}, 得分: {score:>+5.1f}")
    
    if 'rootInfo' in result:
        root = result['rootInfo']
        print(f"\n局面评估:")
        print(f"  当前胜率: {root.get('winrate', 0):.3f}")
        print(f"  预期得分: {root.get('scoreMean', 0):+.1f}")
        print(f"  总访问数: {root.get('visits', 0)}")

def main():
    """主函数"""
    print("=== KataGo SGF 分析测试工具 ===")
    print("选择测试方式:")
    print("1. 预设局面测试")
    print("2. 输入SGF内容")
    print("3. 输入着法序列")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        # 预设局面
        print("\n选择预设局面:")
        print("1. 空棋盘")
        print("2. 简单开局 (星-小目-星-小目)")
        print("3. 复杂中盘")
        
        preset = input("请选择 (1-3): ").strip()
        
        if preset == "1":
            moves = []
        elif preset == "2":
            moves = [["B", "D4"], ["W", "Q16"], ["B", "P4"], ["W", "D16"]]
        elif preset == "3":
            moves = [
                ["B", "D4"], ["W", "Q16"], ["B", "P4"], ["W", "D16"],
                ["B", "F3"], ["W", "Q4"], ["B", "C6"], ["W", "R14"],
                ["B", "Q6"], ["W", "O3"]
            ]
        else:
            print("无效选择")
            return
            
    elif choice == "2":
        # SGF内容输入
        print("\n请输入SGF内容 (例如: ;B[pd];W[dp];B[pp];W[dd]):")
        sgf_content = input().strip()
        
        if not sgf_content:
            print("未输入SGF内容")
            return
            
        moves = parse_sgf_moves(sgf_content)
        print(f"解析出 {len(moves)} 手棋: {moves}")
        
    elif choice == "3":
        # 手动输入着法
        print("\n请输入着法序列，格式: B D4, W Q16, B P4 (输入空行结束):")
        moves = []
        
        while True:
            line = input().strip()
            if not line:
                break
                
            try:
                parts = line.split()
                if len(parts) >= 2:
                    color = parts[0].upper()
                    pos = parts[1].upper()
                    if color in ['B', 'W']:
                        moves.append([color, pos])
                        print(f"添加: {color} {pos}")
            except:
                print(f"无效格式: {line}")
                
    else:
        print("无效选择")
        return
    
    # 执行分析
    print(f"\n开始分析 {len(moves)} 手棋...")
    result = analyze_with_katago(moves)
    
    # 显示结果
    display_analysis_result(result, moves)

if __name__ == "__main__":
    main()