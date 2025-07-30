#!/usr/bin/env python3
"""
KataGo HTTP客户端示例 - 纯HTTP模式
这个脚本演示如何通过HTTP API与KataGo服务器进行交互

使用方法:
    python step_by_step_http.py [--host HOST] [--port PORT] [--timeout TIMEOUT]

示例:
    # 连接到本地KataGo HTTP服务
    python step_by_step_http.py
    
    # 连接到远程KataGo HTTP服务
    python step_by_step_http.py --host 192.168.1.100 --port 8080
    
    # 设置超时时间
    python step_by_step_http.py --timeout 30
"""

import json
import requests
import time
import argparse
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class GameState:
    """围棋游戏状态"""
    board_size: int = 19
    moves: List[Dict[str, Any]] = None
    komi: float = 7.5
    rules: str = "chinese"
    
    def __post_init__(self):
        if self.moves is None:
            self.moves = []
    
    def add_move(self, player: str, x: int, y: int):
        """添加一步棋"""
        move = {
            "player": player.upper(),
            "x": x,
            "y": y
        }
        self.moves.append(move)
        print(f"添加棋步: {player.upper()} 在 ({x}, {y})")
    
    def to_sgf_moves(self) -> List[List[str]]:
        """转换为SGF格式的棋步"""
        sgf_moves = []
        for move in self.moves:
            player = move["player"]
            x, y = move["x"], move["y"]
            # 转换坐标为SGF格式 (a-s)
            sgf_x = chr(ord('a') + x)
            sgf_y = chr(ord('a') + y)
            sgf_moves.append([player, sgf_x + sgf_y])
        return sgf_moves


class KataGoHTTPClient:
    """KataGo HTTP客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'KataGo-HTTP-Client/1.0'
        })
        
        print(f"初始化KataGo HTTP客户端: {self.base_url}")
    
    def check_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 服务器健康状态: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ 健康检查失败: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """获取服务器信息"""
        try:
            response = self.session.get(
                f"{self.base_url}/info",
                timeout=self.timeout
            )
            if response.status_code == 200:
                info = response.json()
                print("📊 服务器信息:")
                print(f"  版本: {info.get('version', 'unknown')}")
                print(f"  模型: {info.get('model', 'unknown')}")
                print(f"  GPU: {info.get('gpu_info', 'unknown')}")
                return info
            else:
                print(f"❌ 获取服务器信息失败: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取服务器信息失败: {e}")
            return None
    
    def analyze_position(self, game_state: GameState, 
                        max_visits: int = 1000,
                        include_ownership: bool = True,
                        include_moves_ownership: bool = False) -> Optional[Dict[str, Any]]:
        """分析当前局面"""
        
        # 构建分析请求
        request_data = {
            "id": f"analysis_{int(time.time())}",
            "initialStones": [],
            "moves": game_state.to_sgf_moves(),
            "rules": game_state.rules,
            "komi": game_state.komi,
            "boardXSize": game_state.board_size,
            "boardYSize": game_state.board_size,
            "maxVisits": max_visits,
            "includeOwnership": include_ownership,
            "includeMovesOwnership": include_moves_ownership,
            "includePVVisits": True
        }
        
        try:
            print(f"🔍 发送分析请求 (最大访问数: {max_visits})...")
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 分析完成")
                return result
            else:
                print(f"❌ 分析失败: HTTP {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 分析请求失败: {e}")
            return None
    
    def print_analysis_result(self, result: Dict[str, Any]):
        """打印分析结果"""
        if not result:
            print("❌ 没有分析结果")
            return
        
        print("\n📈 分析结果:")
        print("=" * 50)
        
        # 基本信息
        if 'id' in result:
            print(f"请求ID: {result['id']}")
        
        if 'turnNumber' in result:
            print(f"回合数: {result['turnNumber']}")
        
        # 根节点信息
        if 'rootInfo' in result:
            root_info = result['rootInfo']
            print(f"\n🎯 当前局面评估:")
            print(f"  访问数: {root_info.get('visits', 0)}")
            print(f"  胜率: {root_info.get('winrate', 0):.1%}")
            print(f"  得分: {root_info.get('scoreMean', 0):.1f}")
            print(f"  得分标准差: {root_info.get('scoreStdev', 0):.1f}")
        
        # 最佳着法
        if 'moveInfos' in result and result['moveInfos']:
            print(f"\n🎲 推荐着法:")
            for i, move_info in enumerate(result['moveInfos'][:5]):  # 显示前5个着法
                move = move_info.get('move', 'pass')
                visits = move_info.get('visits', 0)
                winrate = move_info.get('winrate', 0)
                score = move_info.get('scoreMean', 0)
                
                print(f"  {i+1}. {move}: 胜率={winrate:.1%}, 得分={score:.1f}, 访问={visits}")
                
                # 显示主要变化
                if 'pv' in move_info and move_info['pv']:
                    pv_str = ' '.join(move_info['pv'][:5])  # 显示前5步
                    print(f"     主要变化: {pv_str}")
        
        # 所有权信息
        if 'ownership' in result:
            ownership = result['ownership']
            black_territory = sum(1 for x in ownership if x > 0.5)
            white_territory = sum(1 for x in ownership if x < -0.5)
            print(f"\n🏴 领地预测:")
            print(f"  黑棋领地: ~{black_territory} 个交叉点")
            print(f"  白棋领地: ~{white_territory} 个交叉点")
        
        print("=" * 50)
    
    def close(self):
        """关闭客户端"""
        self.session.close()
        print("🔌 HTTP客户端已关闭")


def demo_empty_board(client: KataGoHTTPClient):
    """演示空棋盘分析"""
    print("\n🎯 演示1: 空棋盘分析")
    print("-" * 30)
    
    game_state = GameState()
    result = client.analyze_position(game_state, max_visits=500)
    client.print_analysis_result(result)


def demo_opening_moves(client: KataGoHTTPClient):
    """演示开局着法分析"""
    print("\n🎯 演示2: 开局着法分析")
    print("-" * 30)
    
    game_state = GameState()
    
    # 添加一些开局着法
    game_state.add_move("B", 15, 3)   # 黑棋 Q4
    game_state.add_move("W", 3, 15)   # 白棋 D16
    game_state.add_move("B", 15, 15)  # 黑棋 Q16
    game_state.add_move("W", 3, 3)    # 白棋 D4
    
    result = client.analyze_position(game_state, max_visits=1000)
    client.print_analysis_result(result)


def demo_middle_game(client: KataGoHTTPClient):
    """演示中盘分析"""
    print("\n🎯 演示3: 中盘局面分析")
    print("-" * 30)
    
    game_state = GameState()
    
    # 模拟一个中盘局面
    moves = [
        ("B", 15, 3), ("W", 3, 15), ("B", 15, 15), ("W", 3, 3),
        ("B", 9, 9), ("W", 9, 15), ("B", 15, 9), ("W", 9, 3),
        ("B", 6, 6), ("W", 12, 12), ("B", 6, 12), ("W", 12, 6)
    ]
    
    for player, x, y in moves:
        game_state.add_move(player, x, y)
    
    result = client.analyze_position(game_state, max_visits=2000, include_ownership=True)
    client.print_analysis_result(result)


def interactive_mode(client: KataGoHTTPClient):
    """交互模式"""
    print("\n🎮 进入交互模式")
    print("输入着法格式: <颜色> <x> <y> (例如: B 15 3)")
    print("输入 'analyze' 进行分析")
    print("输入 'reset' 重置棋盘")
    print("输入 'quit' 退出")
    print("-" * 40)
    
    game_state = GameState()
    
    while True:
        try:
            user_input = input("\n> ").strip().lower()
            
            if user_input == 'quit':
                break
            elif user_input == 'reset':
                game_state = GameState()
                print("🔄 棋盘已重置")
            elif user_input == 'analyze':
                print(f"\n当前棋盘状态: {len(game_state.moves)} 步棋")
                result = client.analyze_position(game_state, max_visits=1000)
                client.print_analysis_result(result)
            else:
                # 解析着法输入
                parts = user_input.split()
                if len(parts) == 3:
                    try:
                        color = parts[0].upper()
                        x = int(parts[1])
                        y = int(parts[2])
                        
                        if color in ['B', 'W'] and 0 <= x < 19 and 0 <= y < 19:
                            game_state.add_move(color, x, y)
                        else:
                            print("❌ 无效输入。颜色应为B或W，坐标应在0-18之间")
                    except ValueError:
                        print("❌ 坐标必须是数字")
                else:
                    print("❌ 输入格式错误。使用: <颜色> <x> <y>")
                    
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except EOFError:
            break


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="KataGo HTTP客户端示例")
    parser.add_argument('--host', default='localhost', help='KataGo服务器主机 (默认: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='KataGo服务器端口 (默认: 8080)')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间 (默认: 30秒)')
    parser.add_argument('--demo-only', action='store_true', help='只运行演示，不进入交互模式')
    parser.add_argument('--max-visits', type=int, default=1000, help='最大访问数 (默认: 1000)')
    
    args = parser.parse_args()
    
    print("🚀 KataGo HTTP客户端启动")
    print(f"连接到: {args.host}:{args.port}")
    print(f"超时时间: {args.timeout}秒")
    print("=" * 50)
    
    # 创建客户端
    client = KataGoHTTPClient(args.host, args.port, args.timeout)
    
    try:
        # 检查服务器连接
        if not client.check_health():
            print("\n❌ 无法连接到KataGo服务器")
            print("请确保KataGo HTTP服务正在运行")
            print("\n启动服务器的命令示例:")
            print("  cd http_server")
            print("  docker-compose up -d")
            sys.exit(1)
        
        # 获取服务器信息
        client.get_server_info()
        
        # 运行演示
        demo_empty_board(client)
        demo_opening_moves(client)
        demo_middle_game(client)
        
        # 交互模式
        if not args.demo_only:
            interactive_mode(client)
        
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()