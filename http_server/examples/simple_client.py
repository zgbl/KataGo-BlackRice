#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP服务简单客户端示例
演示如何使用HTTP API进行围棋分析

使用方法:
    python simple_client.py [--host HOST] [--port PORT]
"""

import argparse
import json
import requests
import time
from typing import Dict, Any, List, Optional


class KataGoHTTPClient:
    """KataGo HTTP客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def analyze_position(self, 
                        moves: List[List[str]] = None,
                        board_size: int = 19,
                        komi: float = 7.5,
                        rules: str = "tromp-taylor",
                        max_visits: int = 1000,
                        analyze_turns: List[int] = None,
                        include_ownership: bool = True,
                        include_pv_visits: bool = True) -> Optional[Dict[str, Any]]:
        """分析棋盘位置"""
        
        if moves is None:
            moves = []
        if analyze_turns is None:
            analyze_turns = [len(moves)]
            
        request_data = {
            "id": f"analysis_{int(time.time())}",
            "moves": moves,
            "rules": rules,
            "komi": komi,
            "boardXSize": board_size,
            "boardYSize": board_size,
            "analyzeTurns": analyze_turns,
            "maxVisits": max_visits,
            "includeOwnership": include_ownership,
            "includePVVisits": include_pv_visits
        }
        
        try:
            print(f"📤 发送分析请求...")
            print(f"   棋盘大小: {board_size}x{board_size}")
            print(f"   贴目: {komi}")
            print(f"   规则: {rules}")
            print(f"   最大访问数: {max_visits}")
            print(f"   移动数: {len(moves)}")
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            print(f"⏱️  请求耗时: {end_time - start_time:.3f}s")
            
            if response.status_code == 200:
                print("✅ 分析成功")
                return response.json()
            else:
                print(f"❌ 分析失败: HTTP {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def print_analysis_result(self, result: Dict[str, Any]):
        """打印分析结果"""
        if not result:
            return
            
        print("\n" + "=" * 60)
        print("📊 分析结果")
        print("=" * 60)
        
        # 基本信息
        print(f"🆔 分析ID: {result.get('id', 'N/A')}")
        
        # 如果有多个回合的分析
        if "turnInfos" in result:
            for turn_idx, turn_info in enumerate(result["turnInfos"]):
                print(f"\n🔄 回合 {turn_idx}:")
                self._print_turn_info(turn_info)
        else:
            # 单回合分析
            self._print_turn_info(result)
    
    def _print_turn_info(self, turn_info: Dict[str, Any]):
        """打印单个回合的分析信息"""
        
        # 根节点信息
        if "rootInfo" in turn_info:
            root_info = turn_info["rootInfo"]
            print(f"  📈 当前局面评估:")
            
            if "winrate" in root_info:
                winrate = root_info["winrate"]
                print(f"    胜率: {winrate:.3f} ({winrate*100:.1f}%)")
            
            if "scoreMean" in root_info:
                score = root_info["scoreMean"]
                print(f"    预期得分: {score:+.1f}")
            
            if "visits" in root_info:
                visits = root_info["visits"]
                print(f"    访问次数: {visits:,}")
        
        # 候选移动
        if "moveInfos" in turn_info:
            move_infos = turn_info["moveInfos"]
            print(f"  🎯 推荐移动 (前5个):")
            
            for i, move_info in enumerate(move_infos[:5]):
                move = move_info.get("move", "pass")
                winrate = move_info.get("winrate", 0)
                visits = move_info.get("visits", 0)
                score = move_info.get("scoreMean", 0)
                
                print(f"    {i+1}. {move:>4} - 胜率: {winrate:.3f} ({winrate*100:.1f}%), "
                      f"访问: {visits:,}, 得分: {score:+.1f}")
                
                # 主要变化
                if "pv" in move_info and move_info["pv"]:
                    pv = " ".join(move_info["pv"][:10])  # 显示前10手
                    if len(move_info["pv"]) > 10:
                        pv += "..."
                    print(f"       主要变化: {pv}")
        
        # 所有权信息
        if "ownership" in turn_info:
            ownership = turn_info["ownership"]
            if ownership:
                # 计算黑白双方的领地
                black_territory = sum(1 for x in ownership if x > 0.5)
                white_territory = sum(1 for x in ownership if x < -0.5)
                neutral = len(ownership) - black_territory - white_territory
                
                print(f"  🏴 领地分析:")
                print(f"    黑棋领地: {black_territory} 点")
                print(f"    白棋领地: {white_territory} 点")
                print(f"    中性区域: {neutral} 点")


def demo_empty_board():
    """演示空棋盘分析"""
    print("\n🎯 演示1: 空棋盘分析")
    print("-" * 40)
    
    client = KataGoHTTPClient()
    
    # 分析空棋盘
    result = client.analyze_position(
        moves=[],
        max_visits=500
    )
    
    if result:
        client.print_analysis_result(result)


def demo_opening_moves():
    """演示开局移动分析"""
    print("\n🎯 演示2: 开局移动分析")
    print("-" * 40)
    
    client = KataGoHTTPClient()
    
    # 一些开局移动
    opening_moves = [
        ["B", "D4"],   # 黑棋小目
        ["W", "Q16"],  # 白棋星位
        ["B", "Q4"],   # 黑棋对角星位
        ["W", "D16"]   # 白棋完成四角开局
    ]
    
    result = client.analyze_position(
        moves=opening_moves,
        max_visits=800,
        analyze_turns=[0, 1, 2, 3, 4]  # 分析每一步
    )
    
    if result:
        client.print_analysis_result(result)


def demo_middle_game():
    """演示中盘分析"""
    print("\n🎯 演示3: 中盘局面分析")
    print("-" * 40)
    
    client = KataGoHTTPClient()
    
    # 一个中盘局面
    middle_game_moves = [
        ["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"],
        ["B", "F3"], ["W", "O17"], ["B", "R6"], ["W", "C14"],
        ["B", "Q10"], ["W", "F17"], ["B", "D10"], ["W", "R14"],
        ["B", "O3"], ["W", "P4"], ["B", "O4"], ["W", "P3"]
    ]
    
    result = client.analyze_position(
        moves=middle_game_moves,
        max_visits=1200,
        include_ownership=True
    )
    
    if result:
        client.print_analysis_result(result)


def interactive_mode():
    """交互模式"""
    print("\n🎮 交互模式")
    print("-" * 40)
    print("输入移动序列进行分析")
    print("格式: B D4, W Q16, B Q4 (颜色 位置)")
    print("输入 'quit' 退出")
    
    client = KataGoHTTPClient()
    
    while True:
        try:
            user_input = input("\n请输入移动序列: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                # 空输入，分析空棋盘
                moves = []
            else:
                # 解析移动
                moves = []
                for move_str in user_input.split(','):
                    move_str = move_str.strip()
                    if ' ' in move_str:
                        color, pos = move_str.split(' ', 1)
                        moves.append([color.strip().upper(), pos.strip().upper()])
            
            print(f"\n分析移动序列: {moves}")
            
            result = client.analyze_position(
                moves=moves,
                max_visits=1000
            )
            
            if result:
                client.print_analysis_result(result)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 输入解析错误: {e}")
    
    print("\n👋 再见！")


def main():
    parser = argparse.ArgumentParser(description="KataGo HTTP客户端示例")
    parser.add_argument("--host", default="localhost", help="服务器地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--demo", choices=["empty", "opening", "middle", "all"], 
                       help="运行特定演示")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    print("🚀 KataGo HTTP客户端示例")
    print(f"🌐 连接到: http://{args.host}:{args.port}")
    
    try:
        if args.interactive:
            interactive_mode()
        elif args.demo:
            if args.demo == "empty" or args.demo == "all":
                demo_empty_board()
            if args.demo == "opening" or args.demo == "all":
                demo_opening_moves()
            if args.demo == "middle" or args.demo == "all":
                demo_middle_game()
        else:
            # 默认运行所有演示
            demo_empty_board()
            demo_opening_moves()
            demo_middle_game()
            
            # 询问是否进入交互模式
            response = input("\n是否进入交互模式? (y/N): ")
            if response.lower().startswith('y'):
                interactive_mode()
    
    except KeyboardInterrupt:
        print("\n🛑 程序被用户中断")
    except Exception as e:
        print(f"💥 程序异常: {e}")


if __name__ == "__main__":
    main()