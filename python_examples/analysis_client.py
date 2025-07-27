#!/usr/bin/env python3
"""
KataGo分析引擎客户端示例
演示如何与Docker中的KataGo分析引擎进行交互
"""

import json
import subprocess
import time
import threading
from typing import Dict, List, Any

class KataGoAnalysisClient:
    def __init__(self, katago_path="/usr/local/bin/katago", 
                 config_path="/app/configs/analysis_example.cfg",
                 model_path="/app/models/model.bin.gz"):
        self.katago_path = katago_path
        self.config_path = config_path
        self.model_path = model_path
        self.process = None
        self.running = False
        
    def start(self):
        """启动KataGo分析引擎"""
        if self.process is not None:
            return
            
        cmd = [
            self.katago_path, "analysis",
            "-config", self.config_path,
            "-model", self.model_path
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.running = True
        print("KataGo分析引擎已启动")
        
    def stop(self):
        """停止KataGo分析引擎"""
        if self.process is None:
            return
            
        self.running = False
        self.process.terminate()
        self.process.wait()
        self.process = None
        print("KataGo分析引擎已停止")
        
    def query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送查询并获取结果"""
        if self.process is None:
            raise RuntimeError("分析引擎未启动")
            
        # 发送查询
        query_json = json.dumps(query_data)
        self.process.stdin.write(query_json + "\n")
        self.process.stdin.flush()
        
        # 读取结果
        result_line = self.process.stdout.readline()
        if not result_line:
            raise RuntimeError("未收到分析结果")
            
        return json.loads(result_line.strip())
        
    def analyze_position(self, moves: List[List[str]], 
                        rules: str = "tromp-taylor",
                        komi: float = 7.5,
                        board_size: int = 19,
                        max_visits: int = 1000) -> Dict[str, Any]:
        """分析指定局面"""
        query = {
            "id": f"analysis_{int(time.time())}",
            "moves": moves,
            "rules": rules,
            "komi": komi,
            "boardXSize": board_size,
            "boardYSize": board_size,
            "analyzeTurns": [len(moves)],
            "maxVisits": max_visits,
            "includeOwnership": True,
            "includePolicy": True
        }
        
        return self.query(query)

def main():
    """主函数 - 演示分析引擎的使用"""
    client = KataGoAnalysisClient()
    
    try:
        # 启动分析引擎
        client.start()
        time.sleep(2)  # 等待引擎初始化
        
        # 示例1: 分析空棋盘
        print("=== 示例1: 分析空棋盘 ===")
        result = client.analyze_position([], max_visits=500)
        print(f"查询ID: {result['id']}")
        print(f"最佳着法: {result['moveInfos'][0]['move']}")
        print(f"胜率: {result['moveInfos'][0]['winrate']:.3f}")
        print(f"访问次数: {result['moveInfos'][0]['visits']}")
        
        # 示例2: 分析有子局面
        print("\n=== 示例2: 分析有子局面 ===")
        moves = [["B", "D4"], ["W", "Q16"], ["B", "P4"]]
        result = client.analyze_position(moves, max_visits=1000)
        
        print(f"当前局面: {moves}")
        print("前5个最佳着法:")
        for i, move_info in enumerate(result['moveInfos'][:5]):
            print(f"  {i+1}. {move_info['move']} - 胜率: {move_info['winrate']:.3f}, 访问: {move_info['visits']}")
            
        # 示例3: 查询版本信息
        print("\n=== 示例3: 查询版本信息 ===")
        version_query = {
            "id": "version_check",
            "action": "query_version"
        }
        version_result = client.query(version_query)
        print(f"KataGo版本: {version_result['version']}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 停止分析引擎
        client.stop()

if __name__ == "__main__":
    main()