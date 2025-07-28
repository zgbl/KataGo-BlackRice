#!/usr/bin/env python3
"""
工作版本的SGF分析工具 - 基于成功的诊断结果优化
"""

import json
import subprocess
import re
import time

def send_analysis_to_docker(query_data, container_name="katago-analysis"):
    """向Docker容器发送分析请求 - 优化版本"""
    try:
        query_json = json.dumps(query_data)
        
        # 使用成功的命令格式
        cmd = [
            "docker", "exec", "-i", container_name,
            "sh", "-c", 
            f"echo '{query_json}' | timeout 60 katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
        
        if result.returncode != 0:
            return None, f"执行错误: {result.stderr}"
            
        # 查找JSON响应
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line and line.startswith('{') and '"id"' in line:
                try:
                    return json.loads(line), None
                except json.JSONDecodeError:
                    continue
                    
        return None, "未找到有效响应"
        
    except subprocess.TimeoutExpired:
        return None, "分析超时"
    except Exception as e:
        return None, f"错误: {e}"

def parse_sgf_moves(sgf_content):
    """解析SGF内容中的着法"""
    moves = []
    
    # 清理SGF内容
    sgf_content = re.sub(r'\s+', ' ', sgf_content.strip())
    
    # SGF解析正则表达式
    move_pattern = r';([BW])\[([a-t]*)\]'
    matches = re.findall(move_pattern, sgf_content, re.IGNORECASE)
    
    print(f"找到 {len(matches)} 个着法")
    
    for i, (color, pos) in enumerate(matches):
        color = color.upper()
        pos = pos.lower().strip()
        
        if pos and len(pos) == 2:  # 正常着法
            try:
                col_sgf = pos[0]  # a-s
                row_sgf = pos[1]  # a-s
                
                # 检查坐标范围
                if col_sgf < 'a' or col_sgf > 's' or row_sgf < 'a' or row_sgf > 's':
                    continue
                
                # 转换坐标
                col_index = ord(col_sgf) - ord('a')  # 0-18
                if col_index >= 8:  # i及之后的字母
                    col_katago = chr(ord('A') + col_index + 1)  # 跳过I
                else:
                    col_katago = chr(ord('A') + col_index)
                
                row_index = ord(row_sgf) - ord('a')  # 0-18
                row_katago = str(19 - row_index)
                
                katago_pos = col_katago + row_katago
                moves.append([color, katago_pos])
                
                # 只显示前几手和最后几手
                if i < 5 or i >= len(matches) - 3:
                    print(f"  {i+1}. {color} {pos} -> {katago_pos}")
                elif i == 5:
                    print(f"  ... (省略中间着法)")
                
            except Exception as e:
                continue
                
        elif not pos:  # 空着法
            moves.append([color, "pass"])
    
    return moves

def display_analysis_result(result):
    """显示分析结果"""
    if not result:
        return
        
    print(f"\n📊 分析结果 (ID: {result['id']})")
    print("-" * 60)
    
    if 'moveInfos' in result and result['moveInfos']:
        print("推荐着法:")
        for i, move_info in enumerate(result['moveInfos'][:5]):
            move = move_info['move']
            winrate = move_info['winrate']
            visits = move_info['visits']
            score_lead = move_info.get('scoreLead', 0)
            
            # 显示主要变化
            pv = move_info.get('pv', [])[:5]  # 前5手变化
            pv_str = ' '.join(pv) if pv else ""
            
            print(f"  {i+1}. {move:>4} - 胜率: {winrate:6.1%} - 访问: {visits:>4} - 分差: {score_lead:+.1f}")
            if pv_str:
                print(f"      变化: {pv_str}")
    
    # 显示整体评估
    if 'rootInfo' in result:
        root = result['rootInfo']
        print(f"\n当前局面评估:")
        print(f"  胜率: {root.get('winrate', 0):.1%}")
        print(f"  分差: {root.get('scoreLead', 0):+.1f}")
        print(f"  总访问: {root.get('visits', 0)}")

def main():
    """主函数"""
    print("🔍 KataGo SGF分析工具 (工作版)")
    print("=" * 50)
    
    # 检查Docker容器
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-analysis", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if "katago-analysis" not in result.stdout:
            print("❌ Docker容器 katago-analysis 未运行")
            return
        else:
            print("✅ Docker容器运行正常")
    except:
        print("❌ 无法检查Docker状态")
        return
    
    while True:
        print("\n请选择:")
        print("1. 分析SGF内容")
        print("2. 快速测试 (空棋盘)")
        print("3. 预设局面测试")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "0":
            print("再见!")
            break
            
        elif choice == "1":
            # SGF内容分析
            print("\n请输入SGF内容 (输入空行结束):")
            sgf_lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                sgf_lines.append(line)
            
            sgf_content = '\n'.join(sgf_lines)
            
            if not sgf_content.strip():
                print("SGF内容不能为空")
                continue
                
            moves = parse_sgf_moves(sgf_content)
            print(f"\n✅ 解析到 {len(moves)} 手棋")
            
        elif choice == "2":
            # 快速测试
            moves = []
            print("使用空棋盘进行快速测试")
            
        elif choice == "3":
            # 预设局面
            presets = {
                "1": ("星小目开局", [["B", "Q4"], ["W", "D4"], ["B", "P16"], ["W", "Q16"]]),
                "2": ("中国流", [["B", "Q4"], ["W", "D4"], ["B", "P16"], ["W", "Q16"], ["B", "R14"]]),
                "3": ("复杂中盘", [["B", "Q4"], ["W", "D4"], ["B", "P16"], ["W", "Q16"], ["B", "R14"], ["W", "C6"], ["B", "F3"], ["W", "Q10"]])
            }
            
            print("\n预设局面:")
            for key, (name, _) in presets.items():
                print(f"  {key}. {name}")
                
            preset_choice = input("\n请选择: ").strip()
            if preset_choice in presets:
                name, moves = presets[preset_choice]
                print(f"使用预设局面: {name}")
            else:
                print("无效选择")
                continue
                
        else:
            print("无效选择")
            continue
        
        # 执行分析
        if 'moves' in locals():
            print(f"\n🔄 正在分析局面... (共{len(moves)}手)")
            
            # 根据局面复杂度调整访问次数
            if len(moves) == 0:
                max_visits = 100  # 空棋盘
            elif len(moves) <= 10:
                max_visits = 200  # 开局
            else:
                max_visits = 300  # 中盘
            
            query = {
                "id": f"sgf_analysis_{int(time.time())}",
                "moves": moves,
                "rules": "tromp-taylor",
                "komi": 7.5,
                "boardXSize": 19,
                "boardYSize": 19,
                "analyzeTurns": [len(moves)],
                "maxVisits": max_visits,
                "includeOwnership": True,
                "includePolicy": True,
                "includeMovesOwnership": False
            }
            
            start_time = time.time()
            result, error = send_analysis_to_docker(query)
            end_time = time.time()
            
            if result:
                print(f"✅ 分析完成 (耗时: {end_time - start_time:.1f}秒)")
                display_analysis_result(result)
            else:
                print(f"❌ 分析失败: {error}")

if __name__ == "__main__":
    main()