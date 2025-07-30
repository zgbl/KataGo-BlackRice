#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP服务健康检查脚本
用于监控服务状态和性能指标

使用方法:
    python health_check.py [--host HOST] [--port PORT] [--interval INTERVAL]
"""

import argparse
import json
import requests
import time
import sys
import psutil
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List


class HealthChecker:
    """KataGo HTTP服务健康检查器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # 健康状态历史
        self.health_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    def check_http_health(self) -> Dict[str, Any]:
        """检查HTTP服务健康状态"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "http_status": "unknown",
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health")
            end_time = time.time()
            
            result["response_time"] = end_time - start_time
            
            if response.status_code == 200:
                result["http_status"] = "healthy"
                try:
                    data = response.json()
                    result["service_info"] = data
                except:
                    result["service_info"] = {"raw_response": response.text}
            else:
                result["http_status"] = "unhealthy"
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            result["http_status"] = "unreachable"
            result["error"] = str(e)
            
        return result
    
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_gpu_status(self) -> Dict[str, Any]:
        """检查GPU状态"""
        try:
            # 尝试使用nvidia-smi获取GPU信息
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpu_info = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            gpu_info.append({
                                "name": parts[0],
                                "memory_total": int(parts[1]) if parts[1].isdigit() else 0,
                                "memory_used": int(parts[2]) if parts[2].isdigit() else 0,
                                "memory_free": int(parts[3]) if parts[3].isdigit() else 0,
                                "utilization": int(parts[4]) if parts[4].isdigit() else 0,
                                "temperature": int(parts[5]) if parts[5].isdigit() else 0
                            })
                
                return {
                    "available": True,
                    "count": len(gpu_info),
                    "gpus": gpu_info
                }
            else:
                return {
                    "available": False,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {"available": False, "error": "nvidia-smi timeout"}
        except FileNotFoundError:
            return {"available": False, "error": "nvidia-smi not found"}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def check_docker_container(self) -> Dict[str, Any]:
        """检查Docker容器状态"""
        try:
            # 检查KataGo容器
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=katago', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers = []
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # 跳过标题行
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                containers.append({
                                    "name": parts[0].strip(),
                                    "status": parts[1].strip(),
                                    "ports": parts[2].strip()
                                })
                
                return {
                    "available": True,
                    "containers": containers
                }
            else:
                return {
                    "available": False,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {"available": False, "error": "docker command timeout"}
        except FileNotFoundError:
            return {"available": False, "error": "docker not found"}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def perform_health_check(self) -> Dict[str, Any]:
        """执行完整的健康检查"""
        print(f"🏥 执行健康检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "service_url": self.base_url
        }
        
        # HTTP服务检查
        print("🌐 检查HTTP服务...")
        http_health = self.check_http_health()
        health_data["http"] = http_health
        
        if http_health["http_status"] == "healthy":
            print(f"✅ HTTP服务正常 (响应时间: {http_health['response_time']:.3f}s)")
        elif http_health["http_status"] == "unhealthy":
            print(f"⚠️  HTTP服务异常: {http_health['error']}")
        else:
            print(f"❌ HTTP服务不可达: {http_health['error']}")
        
        # 系统资源检查
        print("💻 检查系统资源...")
        system_resources = self.check_system_resources()
        health_data["system"] = system_resources
        
        if "error" not in system_resources:
            cpu_percent = system_resources["cpu"]["percent"]
            memory_percent = system_resources["memory"]["percent"]
            disk_percent = system_resources["disk"]["percent"]
            
            print(f"  CPU: {cpu_percent:.1f}%")
            print(f"  内存: {memory_percent:.1f}%")
            print(f"  磁盘: {disk_percent:.1f}%")
            
            # 资源警告
            if cpu_percent > 80:
                print("⚠️  CPU使用率过高")
            if memory_percent > 80:
                print("⚠️  内存使用率过高")
            if disk_percent > 80:
                print("⚠️  磁盘使用率过高")
        
        # GPU状态检查
        print("🎮 检查GPU状态...")
        gpu_status = self.check_gpu_status()
        health_data["gpu"] = gpu_status
        
        if gpu_status["available"]:
            print(f"✅ 检测到 {gpu_status['count']} 个GPU")
            for i, gpu in enumerate(gpu_status["gpus"]):
                memory_percent = (gpu["memory_used"] / gpu["memory_total"]) * 100 if gpu["memory_total"] > 0 else 0
                print(f"  GPU {i}: {gpu['name']} - 利用率: {gpu['utilization']}%, 内存: {memory_percent:.1f}%, 温度: {gpu['temperature']}°C")
        else:
            print(f"❌ GPU不可用: {gpu_status['error']}")
        
        # Docker容器检查
        print("🐳 检查Docker容器...")
        docker_status = self.check_docker_container()
        health_data["docker"] = docker_status
        
        if docker_status["available"]:
            if docker_status["containers"]:
                print(f"✅ 找到 {len(docker_status['containers'])} 个KataGo容器")
                for container in docker_status["containers"]:
                    print(f"  {container['name']}: {container['status']}")
            else:
                print("⚠️  未找到运行中的KataGo容器")
        else:
            print(f"❌ Docker不可用: {docker_status['error']}")
        
        # 保存历史记录
        self.health_history.append(health_data)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        return health_data
    
    def get_overall_status(self, health_data: Dict[str, Any]) -> str:
        """获取总体健康状态"""
        http_status = health_data.get("http", {}).get("http_status")
        
        if http_status == "healthy":
            # 检查资源使用情况
            system = health_data.get("system", {})
            if "error" not in system:
                cpu_percent = system.get("cpu", {}).get("percent", 0)
                memory_percent = system.get("memory", {}).get("percent", 0)
                
                if cpu_percent > 90 or memory_percent > 90:
                    return "degraded"
            
            return "healthy"
        elif http_status == "unhealthy":
            return "unhealthy"
        else:
            return "critical"
    
    def print_summary(self, health_data: Dict[str, Any]):
        """打印健康检查摘要"""
        overall_status = self.get_overall_status(health_data)
        
        print("\n" + "=" * 50)
        print("📊 健康检查摘要")
        print("=" * 50)
        
        # 总体状态
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "critical": "🚨"
        }
        
        print(f"🎯 总体状态: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
        print(f"🕐 检查时间: {health_data['timestamp']}")
        print(f"🌐 服务地址: {health_data['service_url']}")
        
        # HTTP状态
        http_data = health_data.get("http", {})
        print(f"🌐 HTTP服务: {http_data.get('http_status', 'unknown')}")
        if http_data.get("response_time"):
            print(f"⏱️  响应时间: {http_data['response_time']:.3f}s")
        
        # 系统资源
        system_data = health_data.get("system", {})
        if "error" not in system_data:
            print(f"💻 CPU: {system_data['cpu']['percent']:.1f}%")
            print(f"🧠 内存: {system_data['memory']['percent']:.1f}%")
            print(f"💾 磁盘: {system_data['disk']['percent']:.1f}%")
        
        # GPU状态
        gpu_data = health_data.get("gpu", {})
        if gpu_data.get("available"):
            print(f"🎮 GPU: {gpu_data['count']} 个可用")
        
        print("=" * 50)
    
    def monitor_continuous(self, interval: int = 60):
        """持续监控模式"""
        print(f"🔄 开始持续监控 (间隔: {interval}s)")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                health_data = self.perform_health_check()
                self.print_summary(health_data)
                
                print(f"\n⏳ 等待 {interval} 秒...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 监控已停止")


def main():
    parser = argparse.ArgumentParser(description="KataGo HTTP服务健康检查")
    parser.add_argument("--host", default="localhost", help="服务器地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--timeout", type=int, default=10, help="请求超时时间 (默认: 10s)")
    parser.add_argument("--interval", type=int, default=60, help="监控间隔时间 (默认: 60s)")
    parser.add_argument("--continuous", action="store_true", help="持续监控模式")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    checker = HealthChecker(args.host, args.port, args.timeout)
    
    try:
        if args.continuous:
            checker.monitor_continuous(args.interval)
        else:
            health_data = checker.perform_health_check()
            
            if args.json:
                print(json.dumps(health_data, indent=2))
            else:
                checker.print_summary(health_data)
            
            # 根据健康状态设置退出码
            overall_status = checker.get_overall_status(health_data)
            if overall_status == "healthy":
                sys.exit(0)
            elif overall_status == "degraded":
                sys.exit(1)
            else:
                sys.exit(2)
                
    except KeyboardInterrupt:
        print("\n🛑 健康检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 健康检查过程中发生异常: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()