#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步分析完整棋谱 - GPU版本
每步3秒分析，显示playout数量和详细信息
支持本地Docker和远程IP访问
"""

import json
import subprocess
import time
import sys
import os
import re
import requests

# 连接配置
CONNECTION_CONFIG = {
    'use_remote': False,        # 是否使用远程IP访问
    'remote_host': 'localhost', # 远程主机IP
    'remote_port': 8080,        # 远程端口
    'container_name': 'katago-gpu'  # 本地容器名称
}

# 分析设置 - 3秒一步
ANALYSIS_SETTINGS = {
    'max_visits': 300,      # 访问次数
    'max_time': 3.0,        # 3秒一步
    'timeout': 20           # 超时时间
}

# 兼容性：保持原有变量名
CONTAINER_NAME = CONNECTION_CONFIG['container_name']

def check_connection():
    """检查连接状态（本地容器或远程服务）"""
    if CONNECTION_CONFIG['use_remote']:
        return check_remote_katago()
    else:
        return check_gpu_container()

def check_remote_katago():
    """检查远程KataGo服务状态"""
    try:
        url = f"http://{CONNECTION_CONFIG['remote_host']}:{CONNECTION_CONFIG['remote_port']}/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 远程KataGo服务连接成功: {CONNECTION_CONFIG['remote_host']}:{CONNECTION_CONFIG['remote_port']}")
            return True
        else:
            print(f"❌ 远程KataGo服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到远程KataGo服务 {CONNECTION_CONFIG['remote_host']}:{CONNECTION_CONFIG['remote_port']} - {e}")
        return False

def check_gpu_container():
    """检查GPU容器状态"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and CONTAINER_NAME in result.stdout:
            print(f"✅ GPU容器状态: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ GPU容器 '{CONTAINER_NAME}' 未运行")
            print("请先启动: docker-compose up -d katago-gpu")
            return False
            
    except Exception as e:
        print(f"❌ 检查容器状态失败: {e}")
        return False

def convert_to_gtp_coordinate(alpha_alpha_coord):
    """
    Converts a two-character alpha-alpha coordinate (e.g., "dp") to GTP (e.g., "D16").
    Assumes a 19x19 board. Skips 'i' for column characters (standard Go notation).
    """
    if not isinstance(alpha_alpha_coord, str) or len(alpha_alpha_coord) != 2:
        # Handle cases like "pass" or other non-standard inputs
        if alpha_alpha_coord.lower() == "pass" or alpha_alpha_coord.lower() == "tt":
            return "pass"
        return alpha_alpha_coord # Return as is if not a standard two-char string

    lower_coord = alpha_alpha_coord.lower()
    
    col_char = lower_coord[0]
    row_char = lower_coord[1]

    # Convert column character to GTP column letter (A-H, J-T)
    # 'a' (index 0) maps to 'A', 'b' (index 1) to 'B', ..., 'h' (index 7) to 'H'
    # 'j' (index 9) maps to 'J', ..., 's' (index 18) to 'S'
    if 'a' <= col_char <= 'h':
        gtp_col = chr(ord('A') + (ord(col_char) - ord('a')))
    elif 'j' <= col_char <= 's':
        gtp_col = chr(ord('A') + (ord(col_char) - ord('a') - 1)) # -1 because 'i' is skipped
    else:
        print(f"⚠️ 警告: 无法识别的列字符 '{col_char}'，返回原始坐标")
        return alpha_alpha_coord # Return original if column is out of expected range

    # Convert row character to GTP row number (1-19)
    # 'a' is row 1, 's' is row 19 (bottom to top for GTP)
    gtp_row = (ord(row_char) - ord('a')) + 1
    
    if not (1 <= gtp_row <= 19):
        print(f"⚠️ 警告: 无法识别的行字符 '{row_char}'，返回原始坐标")
        return alpha_alpha_coord # Return original if row is out of expected range

    return f"{gtp_col}{gtp_row}"


def analyze_position(moves, move_number, debug=False):
    """分析指定手数后的局面"""
    if CONNECTION_CONFIG['use_remote']:
        return analyze_position_remote(moves, move_number, debug)
    else:
        return analyze_position_local(moves, move_number, debug)

def analyze_position_remote(moves, move_number, debug=False):
    """通过HTTP API分析位置"""
    try:
        # Convert all moves to GTP coordinate format before sending to KataGo
        converted_moves = []
        for player, location in moves:
            converted_location = convert_to_gtp_coordinate(location)
            converted_moves.append([player, converted_location])

        # 构建查询
        query = {
            "id": f"move_{move_number}",
            "moves": converted_moves[:move_number],
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [move_number],
            "includeOwnership": False,
            "includePolicy": True,
            "maxVisits": ANALYSIS_SETTINGS['max_visits'],
            "maxTime": ANALYSIS_SETTINGS['max_time']
        }

        if debug:
            print(f"   调试: 远程查询 {json.dumps(query)}")

        url = f"http://{CONNECTION_CONFIG['remote_host']}:{CONNECTION_CONFIG['remote_port']}/analyze"
        response = requests.post(
            url,
            json=query,
            timeout=ANALYSIS_SETTINGS['timeout']
        )

        if response.status_code == 200:
            analysis_data = response.json()
            if debug:
                visits = analysis_data.get('rootInfo', {}).get('visits', 0)
                winrate = analysis_data.get('rootInfo', {}).get('winrate', 0) * 100
                print(f"   调试: 远程分析成功 - visits: {visits}, winrate: {winrate:.1f}%")
            
            return parse_analysis_result(analysis_data, move_number)
        else:
            return {'error': f"❌ 远程分析失败: HTTP {response.status_code}", 'raw_output': response.text}

    except requests.exceptions.RequestException as e:
        return {'error': f"❌ 远程连接失败: {e}", 'raw_output': str(e)}
    except Exception as e:
        return {'error': f"❌ 远程分析异常: {e}", 'raw_output': str(e)}

def analyze_position_local(moves, move_number, debug=False):
    """通过本地Docker容器分析位置"""
    try:
        # Convert all moves to GTP coordinate format before sending to KataGo
        converted_moves = []
        for player, location in moves:
            converted_location = convert_to_gtp_coordinate(location)
            converted_moves.append([player, converted_location])

        # 构建查询
        query = {
            "id": f"move_{move_number}",
            "moves": converted_moves[:move_number],
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [move_number],
            "includeOwnership": False,
            "includePolicy": True
        }

        query_json = json.dumps(query)
        if debug:
            print(f"   调试: 本地查询 {query_json}")

        # 构建KataGo临时配置文件
        temp_config_content = f"""logDir = analysis_logs
maxVisits = {ANALYSIS_SETTINGS['max_visits']}
maxTime = {ANALYSIS_SETTINGS['max_time']}
nnCacheSizePowerOfTwo = 20
nnMaxBatchSize = 32
nnMutexPoolSizePowerOfTwo = 16
nnRandomize = true
numAnalysisThreads = 2
numSearchThreads = 16
"""
        if debug:
            print(f"   调试: 使用临时配置 maxVisits={ANALYSIS_SETTINGS['max_visits']}, maxTime={ANALYSIS_SETTINGS['max_time']}")

        escaped_config = temp_config_content.replace('\n', '\\n').replace("'", "'\"'\"'")
        command = [
            "docker", "exec", "-i", CONTAINER_NAME,
            "sh", "-c",
            f"printf '{escaped_config}' > /tmp/temp_analysis.cfg && "
            f"timeout {ANALYSIS_SETTINGS['timeout'] - 5} katago analysis -config /tmp/temp_analysis.cfg -model /app/models/model.bin.gz 2>&1"
        ]

        if debug:
            print(f"   调试: 执行命令: {' '.join(command)}")

        result = subprocess.run(
            command,
            input=query_json,
            capture_output=True,
            text=True,
            timeout=ANALYSIS_SETTINGS['timeout']
        )

        if debug:
            print("---START STDERR---")
            print(result.stderr[:500] + ("..." if len(result.stderr) > 500 else ""))
            print("---END STDERR---")

        # 解析KataGo的JSON响应
        analysis_data = None
        output_lines = result.stdout.splitlines() + result.stderr.splitlines()
        
        for line in output_lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    analysis_data = json.loads(line)
                    if debug:
                        visits = analysis_data.get('rootInfo', {}).get('visits', 0)
                        winrate = analysis_data.get('rootInfo', {}).get('winrate', 0) * 100
                        print(f"   调试: 本地分析成功 - visits: {visits}, winrate: {winrate:.1f}%")
                    break
                except json.JSONDecodeError:
                    continue

        if analysis_data:
            return parse_analysis_result(analysis_data, move_number)
        else:
            return {'error': "❌ 未能从KataGo获取有效分析数据。", 'raw_output': result.stdout + result.stderr}

    except subprocess.TimeoutExpired as e:
        return {'error': f"❌ KataGo分析超时 ({ANALYSIS_SETTINGS['timeout']}秒)。", 'raw_output': getattr(e, 'stdout', '') + getattr(e, 'stderr', '')}
    except FileNotFoundError:
        return {'error': "❌ 未找到docker命令，请确认Docker已安装并运行。", 'raw_output': None}
    except Exception as e:
        return {'error': f"❌ 本地分析异常: {e}", 'raw_output': str(e)}

def parse_analysis_result(analysis_data, move_number):
    """解析分析结果"""
    try:
        if analysis_data and analysis_data.get('id') == f"move_{move_number}":
            turn_data = analysis_data.get('rootInfo', {})
            winrate = turn_data.get('winrate', 0.0) * 100.0
            score_lead = turn_data.get('scoreLead', 0.0)
            visits = turn_data.get('visits', 0)
            
            # Find the best move
            best_move_info = None
            if 'moves' in analysis_data:
                for move_info in analysis_data['moves']:
                    if move_info.get('order') == 0:
                        best_move_info = move_info
                        break
            
            recommended_move_gtp = "无"
            if best_move_info and 'move' in best_move_info:
                recommended_move_gtp = best_move_info['move']
            
            return {
                'winrate': winrate,
                'score_lead': score_lead,
                'visits': visits,
                'recommended_move': recommended_move_gtp,
                'error': None
            }
        else:
            return {'error': "❌ 分析数据格式错误或ID不匹配。", 'raw_output': json.dumps(analysis_data) if analysis_data else "无数据"}
    except Exception as e:
        return {'error': f"❌ 分析过程中发生错误: {e}", 'raw_output': None}

def parse_sgf_moves(sgf_content):
    """从SGF内容解析着法"""
    moves = []
    # 查找所有B[xy]或W[xy]模式的着法
    # (;) 是SGF中表示一个节点的开始，包含着法信息
    # [a-t]{2} 匹配两个字符的坐标
    move_pattern = re.compile(r';([BW]\[[a-t]{2}\])')
    
    for match in move_pattern.finditer(sgf_content):
        move_str = match.group(1) # e.g., "B[dp]"
        player = move_str[0] # 'B' or 'W'
        # 提取坐标，通常是两个字符，例如 "dp"
        location = move_str[2:4]
        if location: # 确保坐标存在
            moves.append([player, location])
    return moves


def display_analysis_result(move_number, player, move_coord, result, total_moves):
    """显示单手分析结果"""
    if result.get('error'):
        print(f"❌ 第{move_number}/{total_moves}手: {player} {move_coord} - {result['error']}")
        if result.get('raw_output'):
            print(f"   KataGo原始输出: {result['raw_output']}")
        return
        
    visits = result.get('visits', 0)
    winrate = result.get('winrate', 0)
    score_lead = result.get('score_lead', 0)
    recommended_move = result.get('recommended_move', '无')
    
    status_icon = "✅" if visits > 0 else "⚪"
    print(f"{status_icon} ({visits} PO | {winrate:.1f}%): 第{move_number}/{total_moves}手: {player} {move_coord}")
    print(f"   胜率: {winrate:.1f}% | 分差: {score_lead:.1f} | PO: {visits} | 推荐: {recommended_move}")

def configure_connection():
    """配置连接方式"""
    print("\n🔧 连接配置:")
    print("1. 本地Docker容器 (默认)")
    print("2. 远程KataGo服务")
    
    conn_choice = input("请选择连接方式 (1/2): ").strip()
    
    if conn_choice == "2":
        CONNECTION_CONFIG['use_remote'] = True
        host = input(f"远程主机IP (默认: {CONNECTION_CONFIG['remote_host']}): ").strip()
        if host:
            CONNECTION_CONFIG['remote_host'] = host
        
        port = input(f"远程端口 (默认: {CONNECTION_CONFIG['remote_port']}): ").strip()
        if port:
            try:
                CONNECTION_CONFIG['remote_port'] = int(port)
            except ValueError:
                print("❌ 端口格式错误，使用默认端口")
        
        print(f"✅ 配置为远程模式: {CONNECTION_CONFIG['remote_host']}:{CONNECTION_CONFIG['remote_port']}")
    else:
        CONNECTION_CONFIG['use_remote'] = False
        print("✅ 配置为本地Docker模式")

def main():
    print("🎯 KataGo 逐步分析工具 - GPU版本")
    
    # 配置连接方式
    configure_connection()
    
    # 检查连接
    if not check_connection():
        return

    moves = []
    
    print("\n📝 选择输入方式:")
    print("1. 手动输入着法 (例如: B dp, W pd)")
    print("2. 从SGF文件内容解析 (粘贴SGF内容)")
    
    choice = input("请输入选择 (1/2): ").strip()

    if choice == "1":
        print("\n请输入着法，每行一手 (例如: B dp)。输入 'done' 结束。")
        while True:
            move_input = input("着法: ").strip()
            if move_input.lower() == 'done':
                break
            try:
                parts = move_input.split()
                if len(parts) == 2 and parts[0] in ['B', 'W']:
                    moves.append([parts[0], parts[1]])
                    print(f"   添加: {parts[0]} {parts[1]}")
                else:
                    print("   格式错误，请重新输入")
            except:
                print("   输入错误，请重新输入")
        
        print(f"\n✅ 手动输入完成，共{len(moves)}手")
    
    elif choice == "2":
        print("\n请粘贴SGF文件内容，然后按回车键两次结束输入:")
        sgf_lines = []
        while True:
            line = sys.stdin.readline() # Use sys.stdin.readline to handle multiline input better
            if not line.strip():
                break
            sgf_lines.append(line)
        
        sgf_content = ''.join(sgf_lines).strip() # Join lines and remove leading/trailing whitespace
        
        if not sgf_content:
            print("❌ SGF内容不能为空")
            return
            
        moves = parse_sgf_moves(sgf_content)
        if not moves:
            print("❌ 未从SGF内容中解析到任何着法。请检查SGF格式。")
            return

        print(f"\n✅ 解析到 {len(moves)} 手棋")
        
    else:
        print("❌ 无效选择")
        return
    
    if not moves:
        print("❌ 没有着法可分析")
        return
    
    # 设置分析范围
    start_from = 1
    end_at = len(moves)
    
    range_input = input(f"\n分析范围 (1-{len(moves)}, 直接回车分析全部): ").strip()
    if range_input:
        try:
            if '-' in range_input:
                start_str, end_str = range_input.split('-')
                start_from = int(start_str.strip())
                end_at = int(end_str.strip())
            else:
                end_at = int(range_input)
        except ValueError:
            print("❌ 范围格式错误，使用默认范围")
            start_from = 1
            end_at = len(moves)
    
    # 调试模式
    debug_input = input("是否启用调试模式? (y/N): ").strip().lower()
    debug_mode = debug_input == 'y'

    print("\n📊 进度报告 (最近5手):")
    results_summary = []

    for i in range(start_from, end_at + 1):
        current_moves_for_analysis = moves[:i]
        current_player, current_move_coord_alpha_alpha = moves[i-1] # Get the move being analyzed (in original format)
        
        print(f"\n📍 第{i}手: {current_player} {current_move_coord_alpha_alpha}")
        print("   🔄 分析中...")
        
        start_time = time.time()
        result = analyze_position(current_moves_for_analysis, i, debug_mode)
        end_time = time.time()
        
        display_analysis_result(i, current_player, current_move_coord_alpha_alpha, result, len(moves))

        # 记录最近5手的平均时间
        analysis_time = end_time - start_time
        results_summary.append(analysis_time)
        if len(results_summary) > 5:
            results_summary.pop(0) # Keep only the last 5
        
        avg_time = sum(results_summary) / len(results_summary)
        # 安全地获取visits数量
        avg_po = result.get('visits', 0) if result and not result.get('error') else 0
        
        print(f"\n📊 进度报告 (最近{len(results_summary)}手): 平均{avg_time:.1f}s/手, 平均{avg_po} PO")

        # 短暂延迟以提高稳定性
        time.sleep(0.1)

    print("\n✅ 分析完成。")

if __name__ == "__main__":
    main()