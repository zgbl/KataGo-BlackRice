#!/usr/bin/env python3
"""
逐步分析SGF - 显示每一手的分析进度和结果
修复版本：解决配置文件冲突和分析失败问题
"""

import json
import subprocess
import re
import time

# 全局设置 - 调整为更合理的值
ANALYSIS_SETTINGS = {
    'max_visits': 100,      # 默认访问次数
    'max_time': 15.0,       # 默认最大分析时间(秒)
    'timeout': 20           # 默认超时时间(秒)
}

def check_docker_status():
    """检查Docker容器状态"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-gpu", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and "katago-gpu" in result.stdout:
            print(f"✅ Docker容器状态: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker容器未运行或不存在")
            print("请先启动容器: docker run -d --name katago-gpu ...")
            return False
            
    except Exception as e:
        print(f"❌ 检查Docker状态失败: {e}")
        return False

def send_single_move_analysis(moves, move_number, container_name="katago-gpu", debug=False):
    """分析单独一手棋的局面 - 修复版本"""
    try:
        # 只分析到指定手数的局面
        current_moves = moves[:move_number]
        
        # 构建查询，确保格式正确
        query = {
            "id": f"step_{move_number}",
            "moves": current_moves,
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [len(current_moves)],  # 关键：分析当前局面
            "maxVisits": ANALYSIS_SETTINGS['max_visits'],
            "maxTime": ANALYSIS_SETTINGS['max_time'],
            "includeOwnership": False,
            "includePolicy": True,
            "includeMovesOwnership": False
        }
        
        query_json = json.dumps(query)
        
        if debug:
            print(f"   调试: 分析局面到第{move_number}手")
            print(f"   调试: 当前局面有{len(current_moves)}手棋")
            print(f"   调试: 查询 {query_json[:200]}...")
        
        # 方法1：直接使用默认配置，但通过查询设置参数
        cmd1 = [
            "docker", "exec", "-i", container_name,
            "sh", "-c", 
            f"echo '{query_json}' | timeout {ANALYSIS_SETTINGS['timeout']} katago analysis -config /app/configs/analysis_example.cfg -model /app/models/model.bin.gz"
        ]
        
        # Python超时时间
        python_timeout = ANALYSIS_SETTINGS['timeout'] + 10
        
        if debug:
            print(f"   调试: 使用默认配置文件，查询参数 maxVisits={ANALYSIS_SETTINGS['max_visits']}")
            print(f"   调试: Python超时={python_timeout}秒")
        
        try:
            result = subprocess.run(cmd1, capture_output=True, text=True, timeout=python_timeout)
            
            if debug:
                print(f"   调试: 返回码 {result.returncode}")
                if result.stderr:
                    # 只显示错误输出的关键部分
                    stderr_lines = result.stderr.split('\n')
                    relevant_errors = [line for line in stderr_lines if 'error' in line.lower() or 'exception' in line.lower() or 'failed' in line.lower()]
                    if relevant_errors:
                        print(f"   调试: 关键错误: {relevant_errors[:3]}")
            
            if result.returncode == 0:
                # 查找JSON响应
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('{') and '"id"' in line:
                        try:
                            response = json.loads(line)
                            if debug:
                                print(f"   调试: 找到响应 {response.get('id')}")
                                root_info = response.get('rootInfo', {})
                                print(f"   调试: 胜率={root_info.get('winrate', 'N/A')}, 访问={root_info.get('visits', 'N/A')}")
                            return response
                        except json.JSONDecodeError as e:
                            if debug:
                                print(f"   调试: JSON解析失败 {e}")
                            continue
            
            # 如果方法1失败，尝试方法2：更简单的命令
            if debug:
                print(f"   调试: 方法1失败，尝试方法2")
            
            # 方法2：更简单的查询格式
            simple_query = {
                "id": f"simple_{move_number}",
                "moves": current_moves,
                "rules": "tromp-taylor",
                "komi": 7.5,
                "boardXSize": 19,
                "boardYSize": 19,
                "analyzeTurns": [len(current_moves)],
                "maxVisits": min(50, ANALYSIS_SETTINGS['max_visits'])  # 降低访问次数
            }
            
            simple_json = json.dumps(simple_query)
            
            cmd2 = [
                "docker", "exec", "-i", container_name,
                "katago", "analysis", 
                "-config", "/app/configs/analysis_example.cfg",
                "-model", "/app/models/model.bin.gz"
            ]
            
            if debug:
                print(f"   调试: 尝试简化查询 maxVisits=50")
            
            result2 = subprocess.run(cmd2, input=simple_json, text=True, capture_output=True, timeout=python_timeout)
            
            if result2.returncode == 0:
                lines = result2.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('{') and '"id"' in line:
                        try:
                            response = json.loads(line)
                            if debug:
                                print(f"   调试: 方法2成功")
                            return response
                        except json.JSONDecodeError:
                            continue
            
            if debug:
                print(f"   调试: 两种方法都失败")
                print(f"   调试: 方法1输出: {result.stdout[:200] if result.stdout else 'None'}")
                print(f"   调试: 方法2输出: {result2.stdout[:200] if result2.stdout else 'None'}")
                
        except subprocess.TimeoutExpired:
            if debug:
                print(f"   调试: 命令超时")
            return None
                    
        return None
        
    except Exception as e:
        if debug:
            print(f"   调试: 异常 {e}")
        return None

def test_basic_analysis():
    """测试基础分析功能"""
    print("🔧 测试基础分析功能...")
    
    # 首先检查Docker容器状态
    if not check_docker_status():
        return False
    
    # 使用更简单的测试查询
    query = {
        "id": "test_analysis",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 30  # 降低测试的访问次数
    }
    
    query_json = json.dumps(query)
    print(f"发送测试查询...")
    
    try:
        cmd = [
            "docker", "exec", "-i", "katago-gpu",
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, input=query_json, text=True, capture_output=True, timeout=30)
        
        print(f"测试返回码: {result.returncode}")
        
        if result.returncode == 0:
            # 查找JSON响应
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        print(f"✅ 基础分析成功! ID: {response.get('id')}")
                        root_info = response.get('rootInfo', {})
                        visits = root_info.get('visits', 0)
                        winrate = root_info.get('winrate', 0)
                        print(f"访问次数: {visits}, 胜率: {winrate:.3f}")
                        
                        if visits > 0:
                            print("✅ 基础分析测试通过")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ 基础分析测试失败 - 无有效响应")
        if result.stderr:
            print(f"错误信息: {result.stderr[:300]}")
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ 测试命令超时")
        return False
    except Exception as e:
        print(f"❌ 基础分析测试失败 - {e}")
        return False

def parse_sgf_moves(sgf_content):
    """解析SGF内容中的着法"""
    moves = []
    
    # 清理SGF内容
    sgf_content = re.sub(r'\s+', ' ', sgf_content.strip())
    
    # SGF解析正则表达式
    move_pattern = r';([BW])\[([a-t]*)\]'
    matches = re.findall(move_pattern, sgf_content, re.IGNORECASE)
    
    for color, pos in matches:
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
                
            except Exception as e:
                continue
                
        elif not pos:  # 空着法
            moves.append([color, "pass"])
    
    return moves

def analyze_step_by_step(moves, start_from=1, end_at=None, debug_mode=False):
    """逐步分析每一手棋"""
    if end_at is None:
        end_at = len(moves)
    
    print(f"\n🔄 开始逐步分析 (第{start_from}手到第{end_at}手)")
    print(f"⚙️  分析设置: {ANALYSIS_SETTINGS['max_visits']}次访问, {ANALYSIS_SETTINGS['max_time']}秒限时")
    if debug_mode:
        print("🐛 调试模式已启用")
    print("=" * 80)
    
    # 先测试基础功能
    print("正在测试KataGo连接...")
    if not test_basic_analysis():
        print("❌ 基础分析测试失败，请检查Docker容器配置")
        return []
    
    results = []
    consecutive_failures = 0
    
    for i in range(start_from, min(end_at + 1, len(moves) + 1)):
        if i == 0:
            continue
            
        # 显示当前分析的手数
        if i <= len(moves):
            current_move = moves[i-1]
            print(f"\n📍 第{i}手: {current_move[0]} {current_move[1]}")
        else:
            print(f"\n📍 分析第{i-1}手后的局面")
        
        print(f"   正在分析... ", end="", flush=True)
        
        start_time = time.time()
        result = send_single_move_analysis(moves, i, debug=debug_mode)
        end_time = time.time()
        
        if result:
            # 提取关键信息
            root_info = result.get('rootInfo', {})
            winrate = root_info.get('winrate', 0)
            score_lead = root_info.get('scoreLead', 0)
            visits = root_info.get('visits', 0)
            
            # 检查是否有有效的分析结果
            if visits == 0:
                print(f"⚠️  分析无效 (visits=0)")
                consecutive_failures += 1
                if consecutive_failures >= 5:  # 增加容忍度
                    print(f"\n❌ 连续{consecutive_failures}次无效分析，停止")
                    break
                continue
            
            consecutive_failures = 0  # 重置失败计数
            
            # 获取最佳着法
            best_move = "无"
            if 'moveInfos' in result and result['moveInfos']:
                best_move = result['moveInfos'][0]['move']
            
            print(f"✅ ({end_time - start_time:.1f}s)")
            
            # 根据当前手数决定显示哪方胜率
            is_black_turn = (i % 2 == 1)  # 奇数手是黑棋
            
            if is_black_turn:
                # 黑棋手，显示黑棋胜率
                color_indicator = "⚫"
                display_winrate = winrate
                player_name = "黑"
            else:
                # 白棋手，显示白棋胜率
                color_indicator = "⚪"
                display_winrate = 1 - winrate  # 白棋胜率 = 1 - 黑棋胜率
                player_name = "白"
            
            print(f"   {color_indicator} {player_name}方胜率: {display_winrate:.1%} | 分差: {score_lead:+.1f} | 访问: {visits} | 推荐: {best_move}")
            
            # 保存结果
            results.append({
                'move_number': i,
                'move': moves[i-1] if i <= len(moves) else None,
                'winrate': winrate,
                'display_winrate': display_winrate,
                'is_black_turn': is_black_turn,
                'score_lead': score_lead,
                'visits': visits,
                'best_move': best_move,
                'analysis_time': end_time - start_time
            })
            
        else:
            consecutive_failures += 1
            print(f"❌ 分析失败")
            
            # 如果连续失败太多次，停止分析
            if consecutive_failures >= 5:  # 增加容忍度
                print(f"\n⚠️  连续{consecutive_failures}次分析失败，停止分析")
                print("可能的原因:")
                print("1. KataGo配置文件设置与查询参数冲突")
                print("2. Docker容器内存或CPU资源不足")
                print("3. 模型文件路径问题")
                print("4. 网络权重文件损坏")
                print("\n建议尝试:")
                print("- 重启Docker容器")
                print("- 降低分析参数 (选择快速模式)")
                print("- 检查Docker容器日志")
                break
            
            # 短暂暂停后继续
            time.sleep(1)
    
    return results

def display_summary(results):
    """显示分析总结"""
    if not results:
        return
        
    print(f"\n📈 分析总结")
    print("=" * 80)
    
    # 胜率变化图 (显示当前手方的胜率)
    print("胜率变化 (当前手方视角):")
    for i, result in enumerate(results):
        if i % 5 == 0:  # 每5手显示一次
            move_num = result['move_number']
            display_winrate = result['display_winrate']
            is_black = result['is_black_turn']
            move_info = ""
            if result['move']:
                move_info = f"{result['move'][0]} {result['move'][1]}"
            
            # 简单的胜率条形图
            bar_length = int(display_winrate * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            color_symbol = "⚫" if is_black else "⚪"
            print(f"  第{move_num:3d}手 {color_symbol}{move_info:>6} |{bar}| {display_winrate:.1%}")
    
    # 统计信息
    total_time = sum(r['analysis_time'] for r in results)
    avg_time = total_time / len(results)
    
    print(f"\n统计信息:")
    print(f"  总分析时间: {total_time:.1f}秒")
    print(f"  平均每手: {avg_time:.1f}秒")
    print(f"  分析手数: {len(results)}手")

def configure_analysis_settings():
    """配置分析设置"""
    print("\n⚙️  分析设置")
    print("=" * 30)
    print(f"当前设置:")
    print(f"  访问次数: {ANALYSIS_SETTINGS['max_visits']}")
    print(f"  时间限制: {ANALYSIS_SETTINGS['max_time']}秒")
    print(f"  超时时间: {ANALYSIS_SETTINGS['timeout']}秒")
    
    print("\n选择设置模式:")
    print("1. 快速模式 (30次访问, 5秒) - 推荐用于调试")
    print("2. 标准模式 (100次访问, 10秒)")
    print("3. 精确模式 (300次访问, 20秒)")
    print("4. 自定义设置")
    print("0. 保持当前设置")
    
    choice = input("\n请选择 (0-4): ").strip()
    
    if choice == "1":
        ANALYSIS_SETTINGS['max_visits'] = 30
        ANALYSIS_SETTINGS['max_time'] = 5.0
        ANALYSIS_SETTINGS['timeout'] = 10
        print("✅ 已设置为快速模式")
    elif choice == "2":
        ANALYSIS_SETTINGS['max_visits'] = 100
        ANALYSIS_SETTINGS['max_time'] = 10.0
        ANALYSIS_SETTINGS['timeout'] = 15
        print("✅ 已设置为标准模式")
    elif choice == "3":
        ANALYSIS_SETTINGS['max_visits'] = 300
        ANALYSIS_SETTINGS['max_time'] = 20.0
        ANALYSIS_SETTINGS['timeout'] = 25
        print("✅ 已设置为精确模式")
    elif choice == "4":
        try:
            visits = int(input("访问次数 (10-1000): "))
            time_limit = float(input("时间限制(秒) (1-60): "))
            
            if 10 <= visits <= 1000 and 1 <= time_limit <= 60:
                ANALYSIS_SETTINGS['max_visits'] = visits
                ANALYSIS_SETTINGS['max_time'] = time_limit
                ANALYSIS_SETTINGS['timeout'] = int(time_limit + 5)
                print("✅ 自定义设置已保存")
            else:
                print("❌ 参数超出范围")
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == "0":
        print("✅ 保持当前设置")
    else:
        print("❌ 无效选择")

def diagnose_katago():
    """诊断KataGo配置问题"""
    print("\n🔍 KataGo 配置诊断")
    print("=" * 40)
    
    # 1. 检查容器状态
    print("1. 检查Docker容器...")
    if not check_docker_status():
        return False
    
    # 2. 检查配置文件
    print("\n2. 检查配置文件...")
    try:
        result = subprocess.run([
            "docker", "exec", "katago-gpu",
            "cat", "/app/configs/analysis_example.cfg"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            config_lines = result.stdout.split('\n')
            key_settings = {}
            for line in config_lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key_settings[key.strip()] = value.strip()
            
            print("✅ 配置文件读取成功")
            print(f"   maxVisits = {key_settings.get('maxVisits', '未设置')}")
            print(f"   maxTime = {key_settings.get('maxTime', '未设置')}")
            print(f"   numAnalysisThreads = {key_settings.get('numAnalysisThreads', '未设置')}")
        else:
            print("❌ 无法读取配置文件")
            return False
    except Exception as e:
        print(f"❌ 配置文件检查失败: {e}")
        return False
    
    # 3. 检查模型文件
    print("\n3. 检查模型文件...")
    try:
        result = subprocess.run([
            "docker", "exec", "katago-gpu",
            "ls", "-la", "/app/models/"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 模型目录内容:")
            for line in result.stdout.split('\n'):
                if 'model' in line.lower():
                    print(f"   {line}")
        else:
            print("❌ 无法访问模型目录")
            return False
    except Exception as e:
        print(f"❌ 模型文件检查失败: {e}")
        return False
    
    # 4. 测试简单分析
    print("\n4. 测试最简单的分析...")
    simple_query = '{"id":"diag","moves":[],"rules":"tromp-taylor","komi":7.5,"boardXSize":19,"boardYSize":19,"analyzeTurns":[0],"maxVisits":10}'
    
    try:
        result = subprocess.run([
            "docker", "exec", "-i", "katago-gpu",
            "timeout", "15",
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ], input=simple_query, text=True, capture_output=True, timeout=20)
        
        if result.returncode == 0 and '{"id":"diag"' in result.stdout:
            print("✅ 简单分析测试通过")
            return True
        else:
            print("❌ 简单分析测试失败")
            print(f"返回码: {result.returncode}")
            if result.stderr:
                print(f"错误: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ 简单分析测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🔍 KataGo 逐步分析工具 (修复版)")
    print("=" * 50)
    
    while True:
        print("\n请选择:")
        print("1. 逐步分析SGF")
        print("2. 分析指定范围 (如第50-60手)")
        print("3. 快速演示 (前10手)")
        print("4. 分析设置")
        print("5. 调试模式分析")
        print("6. 系统诊断")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == "0":
            print("再见!")
            break
            
        elif choice == "4":
            configure_analysis_settings()
            
        elif choice == "6":
            diagnose_katago()
            
        elif choice == "5":
            # 调试模式
            print("\n🐛 调试模式 - 分析前3手")
            demo_moves = [["B", "Q4"], ["W", "D4"], ["B", "Q16"]]
            results = analyze_step_by_step(demo_moves, 1, 3, debug_mode=True)
            display_summary(results)
            
        elif choice == "1":
            # 完整逐步分析
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
            
            # 询问是否要分析全部
            if len(moves) > 50:
                confirm = input(f"棋局较长({len(moves)}手)，确定要全部分析吗？(y/n): ")
                if confirm.lower() != 'y':
                    continue
            
            results = analyze_step_by_step(moves)
            display_summary(results)
            
        elif choice == "2":
            # 指定范围分析
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
            
            try:
                start = int(input(f"开始手数 (1-{len(moves)}): "))
                end = int(input(f"结束手数 ({start}-{len(moves)}): "))
                
                if 1 <= start <= end <= len(moves):
                    results = analyze_step_by_step(moves, start, end)
                    display_summary(results)
                else:
                    print("手数范围无效")
            except ValueError:
                print("请输入有效数字")
                
        elif choice == "3":
            # 快速演示
            demo_moves = [
                ["B", "Q4"], ["W", "D4"], ["B", "Q16"], ["W", "Q16"],
                ["B", "R14"], ["W", "C6"], ["B", "F3"], ["W", "Q10"],
                ["B", "O3"], ["W", "C14"]
            ]
            
            print("使用演示局面 (前10手)")
            results = analyze_step_by_step(demo_moves, 1, 10)
            display_summary(results)
            
        else:
            print("无效选择")

if __name__ == "__main__":
    main()