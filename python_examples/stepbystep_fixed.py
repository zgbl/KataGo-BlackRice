#!/usr/bin/env python3
"""
逐步分析SGF - 彻底修复配置冲突问题
通过创建临时配置文件解决KataGo配置覆盖JSON参数的问题
"""

import json
import subprocess
import re
import time
import tempfile
import os

# 全局设置
ANALYSIS_SETTINGS = {
    'max_visits': 100,      # 默认访问次数
    'max_time': 15.0,       # 默认最大分析时间(秒)
    'timeout': 25           # 默认超时时间(秒)
}

def create_custom_config():
    """创建自定义KataGo配置文件，解决配置冲突问题"""
    config_content = f"""# 自定义分析配置 - 解决配置冲突
logDir = analysis_logs
logAllGTPCommunication = false
logSearchInfo = false
logToStderr = false

# 关键设置 - 覆盖默认值
maxVisits = {ANALYSIS_SETTINGS['max_visits']}
maxTime = {ANALYSIS_SETTINGS['max_time']}

# 神经网络设置
nnCacheSizePowerOfTwo = 23
nnMaxBatchSize = 64
nnMutexPoolSizePowerOfTwo = 17
nnRandomize = true

# 分析线程数
numAnalysisThreads = 4

# 搜索设置
allowResignation = false
resignThreshold = -0.90
resignConsecTurns = 3

# 时间控制
maxTimePondering = 60

# 输出设置
reportAnalysisWinratesAs = SIDETOMOVE
analysisPVLen = 15
"""
    
    return config_content

def send_single_move_analysis(moves, move_number, container_name="katago-analysis", debug=False):
    """分析单独一手棋的局面 - 彻底修复版本"""
    try:
        # 只分析到指定手数的局面
        current_moves = moves[:move_number]
        
        # 构建查询
        query = {
            "id": f"step_{move_number}",
            "moves": current_moves,
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [len(current_moves)],
            "includeOwnership": False,
            "includePolicy": True,
            "includeMovesOwnership": False
        }
        
        query_json = json.dumps(query)
        
        if debug:
            print(f"   调试: 分析局面到第{move_number}手")
            print(f"   调试: 当前局面有{len(current_moves)}手棋")
            print(f"   调试: 使用自定义配置 maxVisits={ANALYSIS_SETTINGS['max_visits']}")
        
        # 创建自定义配置文件
        config_content = create_custom_config()
        
        # 方法1：使用自定义配置文件
        try:
            # 将配置写入容器
            write_config_cmd = [
                "docker", "exec", "-i", container_name,
                "sh", "-c", "cat > /tmp/custom_analysis.cfg"
            ]
            
            subprocess.run(write_config_cmd, input=config_content, text=True, timeout=5)
            
            # 使用自定义配置运行分析
            cmd = [
                "docker", "exec", "-i", container_name,
                "sh", "-c", 
                f"echo '{query_json}' | timeout {ANALYSIS_SETTINGS['timeout']} katago analysis -config /tmp/custom_analysis.cfg -model /app/models/model.bin.gz"
            ]
            
            python_timeout = ANALYSIS_SETTINGS['timeout'] + 5
            
            if debug:
                print(f"   调试: 使用自定义配置文件")
                print(f"   调试: 超时设置 {ANALYSIS_SETTINGS['timeout']}秒")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=python_timeout)
            
            if debug:
                print(f"   调试: 返回码 {result.returncode}")
                if result.stderr:
                    # 检查配置是否生效
                    if "maxVisits = " in result.stderr:
                        max_visits_line = [line for line in result.stderr.split('\n') if 'maxVisits = ' in line]
                        if max_visits_line:
                            print(f"   调试: 配置生效 - {max_visits_line[0].strip()}")
            
            if result.returncode == 0:
                # 查找JSON响应
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('{') and '"id"' in line:
                        try:
                            response = json.loads(line)
                            if debug:
                                print(f"   调试: 分析成功")
                                root_info = response.get('rootInfo', {})
                                print(f"   调试: 胜率={root_info.get('winrate', 'N/A'):.3f}, 访问={root_info.get('visits', 'N/A')}")
                            return response
                        except json.JSONDecodeError as e:
                            if debug:
                                print(f"   调试: JSON解析失败 {e}")
                            continue
            
            if debug:
                print(f"   调试: 自定义配置方法失败")
                if result.stderr:
                    error_lines = result.stderr.split('\n')[:5]  # 只显示前5行错误
                    print(f"   调试: 错误信息: {error_lines}")
                    
        except Exception as e:
            if debug:
                print(f"   调试: 自定义配置异常: {e}")
        
        # 方法2：降级到最小参数
        if debug:
            print(f"   调试: 尝试降级方案")
        
        simple_query = {
            "id": f"simple_{move_number}",
            "moves": current_moves,
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [len(current_moves)],
            "maxVisits": 30  # 极低的访问次数
        }
        
        simple_json = json.dumps(simple_query)
        
        cmd2 = [
            "docker", "exec", "-i", container_name,
            "katago", "analysis", 
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        try:
            result2 = subprocess.run(cmd2, input=simple_json, text=True, capture_output=True, timeout=30)
            
            if result2.returncode == 0:
                lines = result2.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('{') and '"id"' in line:
                        try:
                            response = json.loads(line)
                            if debug:
                                print(f"   调试: 降级方案成功")
                            return response
                        except json.JSONDecodeError:
                            continue
                            
        except subprocess.TimeoutExpired:
            if debug:
                print(f"   调试: 降级方案也超时")
                
        return None
        
    except Exception as e:
        if debug:
            print(f"   调试: 总体异常 {e}")
        return None

def check_docker_status():
    """检查Docker容器状态"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=katago-analysis", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and "katago-analysis" in result.stdout:
            print(f"✅ Docker容器状态: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker容器未运行或不存在")
            return False
            
    except Exception as e:
        print(f"❌ 检查Docker状态失败: {e}")
        return False

def test_basic_analysis():
    """测试基础分析功能"""
    print("🔧 测试基础分析功能...")
    
    if not check_docker_status():
        return False
    
    # 测试自定义配置
    print("测试自定义配置...")
    config_content = create_custom_config()
    
    try:
        # 写入自定义配置
        write_config_cmd = [
            "docker", "exec", "-i", "katago-analysis",
            "sh", "-c", "cat > /tmp/test_config.cfg"
        ]
        
        subprocess.run(write_config_cmd, input=config_content, text=True, timeout=5)
        
        # 测试查询
        query = {
            "id": "config_test",
            "moves": [],
            "rules": "tromp-taylor",
            "komi": 7.5,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": [0]
        }
        
        query_json = json.dumps(query)
        
        cmd = [
            "docker", "exec", "-i", "katago-analysis",
            "sh", "-c", 
            f"echo '{query_json}' | timeout 20 katago analysis -config /tmp/test_config.cfg -model /app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        
        print(f"测试返回码: {result.returncode}")
        
        # 检查配置是否生效
        if result.stderr and "maxVisits = " in result.stderr:
            max_visits_lines = [line for line in result.stderr.split('\n') if 'maxVisits = ' in line]
            if max_visits_lines:
                print(f"✅ 自定义配置生效: {max_visits_lines[0].strip()}")
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        root_info = response.get('rootInfo', {})
                        visits = root_info.get('visits', 0)
                        winrate = root_info.get('winrate', 0)
                        print(f"✅ 测试成功! 访问次数: {visits}, 胜率: {winrate:.3f}")
                        
                        if visits > 0:
                            print("✅ 基础分析测试通过")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ 基础分析测试失败")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
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
                if consecutive_failures >= 3:
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
                black_winrate = winrate
                white_winrate = 1 - winrate
                print(f"   黑棋胜率: {black_winrate:.1%} | 白棋胜率: {white_winrate:.1%}")
            else:
                # 白棋手，显示白棋胜率
                white_winrate = winrate
                black_winrate = 1 - winrate
                print(f"   白棋胜率: {white_winrate:.1%} | 黑棋胜率: {black_winrate:.1%}")
            
            print(f"   目数差: {score_lead:+.1f} | 访问: {visits} | 推荐: {best_move}")
            
            # 保存结果
            results.append({
                'move_number': i,
                'move': moves[i-1] if i <= len(moves) else None,
                'winrate': winrate,
                'score_lead': score_lead,
                'visits': visits,
                'best_move': best_move,
                'analysis_time': end_time - start_time
            })
            
        else:
            print(f"❌ 分析失败")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print(f"\n❌ 连续{consecutive_failures}次分析失败，停止分析")
                print("建议检查:")
                print("1. Docker容器是否正常运行")
                print("2. KataGo模型文件是否存在")
                print("3. 系统资源是否充足")
                break
    
    return results

def display_summary(results):
    """显示分析结果摘要"""
    if not results:
        print("\n❌ 没有有效的分析结果")
        return
    
    print(f"\n📊 分析摘要 (共{len(results)}手)")
    print("=" * 60)
    
    # 胜率变化最大的几手
    winrate_changes = []
    for i in range(1, len(results)):
        prev_wr = results[i-1]['winrate']
        curr_wr = results[i]['winrate']
        change = abs(curr_wr - prev_wr)
        winrate_changes.append((i, change, results[i]))
    
    if winrate_changes:
        winrate_changes.sort(key=lambda x: x[1], reverse=True)
        print("\n🔥 胜率变化最大的几手:")
        for i, (idx, change, result) in enumerate(winrate_changes[:5]):
            move = result['move']
            print(f"   {i+1}. 第{result['move_number']}手 {move[0]} {move[1]} - 变化: {change:.1%}")
    
    # 平均分析时间
    avg_time = sum(r['analysis_time'] for r in results) / len(results)
    print(f"\n⏱️  平均分析时间: {avg_time:.1f}秒")
    
    # 访问次数统计
    avg_visits = sum(r['visits'] for r in results) / len(results)
    print(f"🔍 平均访问次数: {avg_visits:.0f}")

def configure_analysis_settings():
    """配置分析参数"""
    print(f"\n⚙️  当前分析设置:")
    print(f"   访问次数: {ANALYSIS_SETTINGS['max_visits']}")
    print(f"   最大时间: {ANALYSIS_SETTINGS['max_time']}秒")
    print(f"   超时时间: {ANALYSIS_SETTINGS['timeout']}秒")
    
    print(f"\n请选择要修改的设置:")
    print("1. 访问次数 (影响分析精度)")
    print("2. 最大时间 (影响分析深度)")
    print("3. 超时时间 (影响稳定性)")
    print("0. 保持当前设置")
    
    choice = input("请输入选择 (0-3): ").strip()
    
    if choice == "1":
        try:
            new_visits = int(input(f"新的访问次数 (当前: {ANALYSIS_SETTINGS['max_visits']}): "))
            if 10 <= new_visits <= 1000:
                ANALYSIS_SETTINGS['max_visits'] = new_visits
                print(f"✅ 访问次数已设置为 {new_visits}")
            else:
                print("❌ 访问次数应在10-1000之间")
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == "2":
        try:
            new_time = float(input(f"新的最大时间 (当前: {ANALYSIS_SETTINGS['max_time']}): "))
            if 1.0 <= new_time <= 300.0:
                ANALYSIS_SETTINGS['max_time'] = new_time
                print(f"✅ 最大时间已设置为 {new_time}秒")
            else:
                print("❌ 最大时间应在1-300秒之间")
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == "3":
        try:
            new_timeout = int(input(f"新的超时时间 (当前: {ANALYSIS_SETTINGS['timeout']}): "))
            if 10 <= new_timeout <= 600:
                ANALYSIS_SETTINGS['timeout'] = new_timeout
                print(f"✅ 超时时间已设置为 {new_timeout}秒")
            else:
                print("❌ 超时时间应在10-600秒之间")
        except ValueError:
            print("❌ 请输入有效数字")
    elif choice == "0":
        print("✅ 保持当前设置")
    else:
        print("❌ 无效选择")

def main():
    """主函数"""
    print("🔍 KataGo 逐步分析工具 (彻底修复版)")
    print("=" * 50)
    
    while True:
        print("\n请选择:")
        print("1. 逐步分析SGF")
        print("2. 分析指定范围 (如第50-60手)")
        print("3. 快速演示 (前10手)")
        print("4. 分析设置")
        print("5. 调试模式分析")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "0":
            print("再见!")
            break
            
        elif choice == "4":
            configure_analysis_settings()
            
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