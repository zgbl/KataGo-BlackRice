#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP服务远程客户端示例
演示如何连接到远程KataGo服务器并进行分析
支持认证、重试、连接池等高级功能

使用方法:
    python remote_client.py --host remote.server.com --port 8080 --api-key YOUR_API_KEY
"""

import argparse
import json
import requests
import time
import ssl
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str
    port: int = 8080
    use_https: bool = False
    api_key: Optional[str] = None
    timeout: int = 60
    verify_ssl: bool = True
    max_retries: int = 3
    retry_backoff: float = 1.0


class RemoteKataGoClient:
    """远程KataGo HTTP客户端"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.base_url = f"{'https' if config.use_https else 'http'}://{config.host}:{config.port}"
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 创建会话
        self.session = self._create_session()
        
        # 连接状态
        self.is_connected = False
        self.server_info = None
        
    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置超时
        session.timeout = self.config.timeout
        
        # 设置SSL验证
        if not self.config.verify_ssl:
            session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 设置认证头
        if self.config.api_key:
            session.headers.update({
                'Authorization': f'Bearer {self.config.api_key}',
                'X-API-Key': self.config.api_key
            })
        
        # 设置用户代理
        session.headers.update({
            'User-Agent': 'KataGo-Remote-Client/1.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        return session
    
    def connect(self) -> bool:
        """连接到服务器"""
        self.logger.info(f"连接到服务器: {self.base_url}")
        
        try:
            # 健康检查
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                self.is_connected = True
                try:
                    self.server_info = response.json()
                except:
                    self.server_info = {"status": "ok", "raw_response": response.text}
                
                self.logger.info("✅ 连接成功")
                self.logger.info(f"服务器信息: {self.server_info}")
                return True
            else:
                self.logger.error(f"❌ 连接失败: HTTP {response.status_code}")
                self.logger.error(f"响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.session:
            self.session.close()
        self.is_connected = False
        self.logger.info("🔌 已断开连接")
    
    def analyze_position(self, 
                        moves: List[List[str]] = None,
                        board_size: int = 19,
                        komi: float = 7.5,
                        rules: str = "tromp-taylor",
                        max_visits: int = 1000,
                        analyze_turns: List[int] = None,
                        include_ownership: bool = True,
                        include_pv_visits: bool = True,
                        request_id: str = None) -> Optional[Dict[str, Any]]:
        """分析棋盘位置"""
        
        if not self.is_connected:
            self.logger.error("❌ 未连接到服务器")
            return None
        
        if moves is None:
            moves = []
        if analyze_turns is None:
            analyze_turns = [len(moves)]
        if request_id is None:
            request_id = f"remote_analysis_{int(time.time())}"
        
        request_data = {
            "id": request_id,
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
            self.logger.info(f"📤 发送分析请求: {request_id}")
            self.logger.debug(f"请求数据: {json.dumps(request_data, indent=2)}")
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=request_data
            )
            end_time = time.time()
            
            request_time = end_time - start_time
            self.logger.info(f"⏱️  请求耗时: {request_time:.3f}s")
            
            if response.status_code == 200:
                self.logger.info(f"✅ 分析成功: {request_id}")
                result = response.json()
                result["request_time"] = request_time
                result["server_url"] = self.base_url
                return result
            else:
                self.logger.error(f"❌ 分析失败: HTTP {response.status_code}")
                self.logger.error(f"错误响应: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 分析请求异常: {e}")
            return None
    
    def batch_analyze(self, 
                     positions: List[Dict[str, Any]], 
                     max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """批量分析（串行，避免服务器过载）"""
        results = []
        total = len(positions)
        
        self.logger.info(f"🚀 开始批量分析 {total} 个位置")
        
        for i, pos_data in enumerate(positions):
            self.logger.info(f"📊 进度: {i+1}/{total}")
            
            result = self.analyze_position(
                moves=pos_data.get('moves', []),
                board_size=pos_data.get('board_size', 19),
                komi=pos_data.get('komi', 7.5),
                rules=pos_data.get('rules', 'tromp-taylor'),
                max_visits=pos_data.get('max_visits', 1000),
                request_id=pos_data.get('id', f'batch_{i}')
            )
            
            if result:
                results.append(result)
            
            # 避免过于频繁的请求
            if i < total - 1:  # 不是最后一个
                time.sleep(0.5)
        
        self.logger.info(f"🏁 批量分析完成: {len(results)}/{total} 成功")
        return results
    
    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """获取服务器状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "message": response.text}
        except requests.exceptions.RequestException as e:
            return {"error": "connection_failed", "message": str(e)}
    
    def test_connection_quality(self, num_tests: int = 5) -> Dict[str, Any]:
        """测试连接质量"""
        self.logger.info(f"🔍 测试连接质量 ({num_tests} 次测试)")
        
        times = []
        errors = 0
        
        for i in range(num_tests):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health")
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append(end_time - start_time)
                    self.logger.debug(f"测试 {i+1}: {end_time - start_time:.3f}s")
                else:
                    errors += 1
                    self.logger.warning(f"测试 {i+1}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                errors += 1
                self.logger.warning(f"测试 {i+1}: 异常 {e}")
            
            # 测试间隔
            if i < num_tests - 1:
                time.sleep(1)
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            quality = {
                "success_rate": len(times) / num_tests,
                "avg_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "total_tests": num_tests,
                "successful_tests": len(times),
                "failed_tests": errors
            }
            
            self.logger.info(f"📊 连接质量测试结果:")
            self.logger.info(f"  成功率: {quality['success_rate']*100:.1f}%")
            self.logger.info(f"  平均响应时间: {avg_time:.3f}s")
            self.logger.info(f"  响应时间范围: {min_time:.3f}s - {max_time:.3f}s")
            
            return quality
        else:
            return {
                "success_rate": 0,
                "error": "所有测试都失败了",
                "total_tests": num_tests,
                "failed_tests": errors
            }


def demo_remote_analysis(client: RemoteKataGoClient):
    """演示远程分析"""
    print("\n🎯 演示远程分析功能")
    print("-" * 40)
    
    # 测试连接质量
    quality = client.test_connection_quality(3)
    if quality["success_rate"] < 0.8:
        print("⚠️  连接质量较差，可能影响分析性能")
    
    # 分析一些位置
    test_positions = [
        {
            "id": "empty_board",
            "moves": [],
            "description": "空棋盘"
        },
        {
            "id": "opening_moves",
            "moves": [["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"]],
            "description": "开局四手"
        },
        {
            "id": "complex_position",
            "moves": [
                ["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"],
                ["B", "F3"], ["W", "O17"], ["B", "R6"], ["W", "C14"]
            ],
            "description": "复杂局面"
        }
    ]
    
    for pos in test_positions:
        print(f"\n📋 分析: {pos['description']}")
        result = client.analyze_position(
            moves=pos["moves"],
            max_visits=500,
            request_id=pos["id"]
        )
        
        if result:
            # 简单显示结果
            root_info = result.get("rootInfo", {})
            if "winrate" in root_info:
                winrate = root_info["winrate"]
                print(f"  胜率: {winrate:.3f} ({winrate*100:.1f}%)")
            
            move_infos = result.get("moveInfos", [])
            if move_infos:
                best_move = move_infos[0]
                print(f"  推荐移动: {best_move.get('move', 'pass')} "
                      f"(胜率: {best_move.get('winrate', 0):.3f})")
            
            print(f"  请求耗时: {result.get('request_time', 0):.3f}s")
        else:
            print("  ❌ 分析失败")


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(description="KataGo远程HTTP客户端")
    parser.add_argument("--host", required=True, help="服务器地址")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--https", action="store_true", help="使用HTTPS")
    parser.add_argument("--api-key", help="API密钥")
    parser.add_argument("--timeout", type=int, default=60, help="请求超时时间 (默认: 60s)")
    parser.add_argument("--no-ssl-verify", action="store_true", help="跳过SSL证书验证")
    parser.add_argument("--max-retries", type=int, default=3, help="最大重试次数 (默认: 3)")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别 (默认: INFO)")
    parser.add_argument("--test-only", action="store_true", help="仅测试连接")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 创建服务器配置
    config = ServerConfig(
        host=args.host,
        port=args.port,
        use_https=args.https,
        api_key=args.api_key,
        timeout=args.timeout,
        verify_ssl=not args.no_ssl_verify,
        max_retries=args.max_retries
    )
    
    print("🚀 KataGo远程HTTP客户端")
    print(f"🌐 目标服务器: {config.host}:{config.port}")
    print(f"🔒 使用HTTPS: {config.use_https}")
    print(f"🔑 API密钥: {'是' if config.api_key else '否'}")
    
    client = RemoteKataGoClient(config)
    
    try:
        # 连接到服务器
        if not client.connect():
            print("❌ 无法连接到服务器")
            return
        
        # 显示服务器信息
        if client.server_info:
            print(f"📊 服务器信息: {json.dumps(client.server_info, indent=2)}")
        
        if args.test_only:
            # 仅测试连接
            quality = client.test_connection_quality(5)
            print(f"\n📊 连接质量测试结果:")
            print(json.dumps(quality, indent=2))
        else:
            # 运行演示
            demo_remote_analysis(client)
        
        print("\n🎉 远程客户端演示完成！")
        
    except KeyboardInterrupt:
        print("\n🛑 程序被用户中断")
    except Exception as e:
        print(f"💥 程序异常: {e}")
        logging.exception("详细异常信息:")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()