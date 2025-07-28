#!/usr/bin/env python3
"""
修复版本的交互式SGF分析工具
正确解析SGF格式并与KataGo Docker容器交互
"""

import json
import subprocess
import re
import sys
import time

def send_analysis_to_docker(query_data, container_name="katago-analysis"):
    """向Docker容器发送分析请求"""
    try:
        query_json = json.dumps(query_data)
        
        cmd = [
            "docker", "exec", "-i", container_name,
            "/bin/bash", "-c", 
            f"echo '{query_json}' | katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return None, f"执行错误: {result.stderr}"
            
        # 查找JSON响应
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line and line.startswith('{'):
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
    """解析SGF内容中的着法 - 修复版本"""
    moves = []
    
    # 清理SGF内容
    sgf_content = re.sub(r'\s+', ' ', sgf_content.strip())
    print(f"清理后的SGF内容: {sgf_content[:200]}...")
    
    # 更精确的SGF解析正则表达式
    # 匹配 ;B[xx] 或 ;W[xx] 格式，包括空着法
    move_pattern = r';([BW])\[([a-t]*)\]'
    matches = re.findall(move_pattern, sgf_content, re.IGNORECASE)
    
    print(f"找到 {len(matches)} 个着法匹配项")
    
    for i, (color, pos) in enumerate(matches):
        color = color.upper()
        pos = pos.lower().strip()
        
        print(f"处理第{i+1}个着法: {color}[{pos}]")
        
        if pos and len(pos) == 2:  # 正常着法
            try:
                # SGF坐标转换为KataGo坐标
                col_sgf = pos[0]  # a-s
                row_sgf = pos[1]  # a-s
                
                # 检查坐标范围
                if col_sgf < 'a' or col_sgf > 's' or row_sgf < 'a' or row_sgf > 's':
                    print(f"  跳过无效坐标: {pos}")
                    continue
                
                # 转换列坐标 (a-s -> A-T, 跳过I)
                col_index = ord(col_sgf) - ord('a')  # 0-18
                if col_index >= 8:  # i及之后的字母
                    col_katago = chr(ord('A') + col_index + 1)  # 跳过I
                else:
                    col_katago = chr(ord('A') + col_index)
                
                # 转换行坐标 (SGF的a=19行, s=1行)
                row_index = ord(row_sgf) - ord('a')  # 0-18
                row_katago = str(19 - row_index)
                
                katago_pos = col_katago + row_katago
                moves.append([color, katago_pos])
                print(f"  转换成功: {color} {pos} -> {katago_pos}")
                
            except Exception as e:
                print(f"  转换失败 {pos}: {e}")
                continue
                
        elif not pos:  # 空着法
            moves.append([color, "pass"])
            print(f"  空着法: {color} pass")
        else:
            print(f"  跳过格式错误的着法: {pos}")
    
    return moves

def display_analysis_result(result):
    """显示分析结果"""
    if not result:
        return
        
    print(f"\n📊 分析结果 (ID: {result['id']})")
    print("-" * 50)
    
    if 'moveInfos' in result and result['moveInfos']:
        print("推荐着法 (前5个):")
        for i, move_info in enumerate(result['moveInfos'][:5]):
            move = move_info['move']
            winrate = move_info['winrate']
            visits = move_info['visits']
            
            # 计算分数差
            score_lead = move_info.get('scoreLead', 0)
            
            print(f"  {i+1}. {move:>4} - 胜率: {winrate:6.1%} - 访问: {visits:>6} - 分差: {score_lead:+.1f}")
    
    # 显示整体评估
    if 'rootInfo' in result:
        root = result['rootInfo']
        print(f"\n当前局面评估:")
        print(f"  胜率: {root.get('winrate', 0):.1%}")
        print(f"  分差: {root.get('scoreLead', 0):+.1f}")
        print(f"  总访问: {root.get('visits', 0)}")

def test_sgf_parsing():
    """测试SGF解析功能"""
    test_sgf = """(;FF[4]
CA[UTF-8]
GM[1]
DT[2024-03-13]
;B[pp]
;W[dd]
;B[qd]
;W[dp]
;B[od]
;W[qq])"""
    
    print("=== 测试SGF解析 ===")
    print(f"测试SGF: {test_sgf}")
    moves = parse_sgf_moves(test_sgf)
    print(f"解析结果: {moves}")
    return moves

def main():
    """主函数"""
    print("🔍 KataGo 交互式SGF分析工具 (修复版)")
    print("=" * 50)
    
    # 检查Docker容器
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-analysis", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if "katago-analysis" not in result.stdout:
            print("❌ Docker容器 katago-analysis 未运行")
            print("请先运行: docker-compose up katago-analysis")
            return
        else:
            print("✅ Docker容器运行正常")
    except:
        print("❌ 无法检查Docker状态")
        return
    
    while True:
        print("\n请选择分析方式:")
        print("1. 测试SGF解析")
        print("2. 输入SGF内容")
        print("3. 预设局面测试")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-3): ").strip()
        
        if choice == "0":
            print("再见!")
            break
            
        elif choice == "1":
            # 测试SGF解析
            moves = test_sgf_parsing()
            
        elif choice == "2":
            # SGF内容
            print("\n请输入SGF内容:")
            print("提示: 可以直接粘贴完整的SGF文件内容")
            
            # 支持多行输入
            print("输入SGF内容 (输入空行结束):")
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
            print(f"\n✅ 解析到 {len(moves)} 手棋:")
            for i, move in enumerate(moves[:10]):  # 只显示前10手
                print(f"  {i+1}. {move[0]} {move[1]}")
            if len(moves) > 10:
                print(f"  ... 还有 {len(moves)-10} 手")
                
        elif choice == "3":
            # 预设局面
            moves = [["B", "Q4"], ["W", "D4"], ["B", "P16"], ["W", "Q16"]]
            print(f"使用预设局面: {moves}")
            
        else:
            print("无效选择")
            continue
        
        # 执行分析
        if 'moves' in locals() and moves:
            print(f"\n🔄 正在分析局面... (共{len(moves)}手)")
            
            query = {
                "id": f"sgf_analysis_{int(time.time())}",
                "moves": moves,
                "rules": "tromp-taylor",
                "komi": 7.5,
                "boardXSize": 19,
                "boardYSize": 19,
                "analyzeTurns": [len(moves)],
                "maxVisits": 500,  # 减少访问次数以加快分析
                "includeOwnership": True,
                "includePolicy": True,
                "includeMovesOwnership": False
            }
            
            result, error = send_analysis_to_docker(query)
            
            if result:
                display_analysis_result(result)
            else:
                print(f"❌ 分析失败: {error}")
        elif 'moves' in locals() and not moves:
            print("⚠️  没有解析到有效着法，请检查SGF格式")

if __name__ == "__main__":
    main()