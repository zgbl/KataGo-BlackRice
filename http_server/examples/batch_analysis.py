#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo HTTP服务批量分析示例
演示如何批量分析多个棋局或位置

使用方法:
    python batch_analysis.py [--host HOST] [--port PORT] [--input INPUT_FILE] [--output OUTPUT_FILE]
"""

import argparse
import json
import requests
import time
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AnalysisJob:
    """分析任务"""
    id: str
    moves: List[List[str]]
    board_size: int = 19
    komi: float = 7.5
    rules: str = "tromp-taylor"
    max_visits: int = 1000
    description: str = ""


class BatchAnalyzer:
    """批量分析器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 60):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # 统计信息
        self.total_jobs = 0
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.start_time = None
        
    def analyze_single_position(self, job: AnalysisJob) -> Optional[Dict[str, Any]]:
        """分析单个位置"""
        request_data = {
            "id": job.id,
            "moves": job.moves,
            "rules": job.rules,
            "komi": job.komi,
            "boardXSize": job.board_size,
            "boardYSize": job.board_size,
            "analyzeTurns": [len(job.moves)],
            "maxVisits": job.max_visits,
            "includeOwnership": True,
            "includePVVisits": True
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                result["analysis_time"] = end_time - start_time
                result["job_description"] = job.description
                return result
            else:
                print(f"❌ 分析失败 {job.id}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败 {job.id}: {e}")
            return None
    
    def analyze_batch(self, jobs: List[AnalysisJob], max_workers: int = 4) -> List[Dict[str, Any]]:
        """批量分析"""
        self.total_jobs = len(jobs)
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.start_time = time.time()
        
        print(f"🚀 开始批量分析")
        print(f"📊 总任务数: {self.total_jobs}")
        print(f"🔧 并发数: {max_workers}")
        print(f"🌐 服务地址: {self.base_url}")
        print("-" * 50)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_job = {executor.submit(self.analyze_single_position, job): job for job in jobs}
            
            # 处理完成的任务
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        self.completed_jobs += 1
                        print(f"✅ 完成 {job.id} ({self.completed_jobs}/{self.total_jobs}) - "
                              f"耗时: {result.get('analysis_time', 0):.2f}s")
                    else:
                        self.failed_jobs += 1
                        print(f"❌ 失败 {job.id} ({self.failed_jobs} 个失败)")
                        
                except Exception as e:
                    self.failed_jobs += 1
                    print(f"💥 异常 {job.id}: {e}")
                
                # 显示进度
                progress = (self.completed_jobs + self.failed_jobs) / self.total_jobs * 100
                print(f"📈 进度: {progress:.1f}%")
        
        total_time = time.time() - self.start_time
        print("-" * 50)
        print(f"🏁 批量分析完成")
        print(f"✅ 成功: {self.completed_jobs}/{self.total_jobs}")
        print(f"❌ 失败: {self.failed_jobs}/{self.total_jobs}")
        print(f"⏱️  总耗时: {total_time:.2f}s")
        print(f"📊 平均耗时: {total_time/self.total_jobs:.2f}s/任务")
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """保存分析结果"""
        print(f"💾 保存结果到: {output_file}")
        
        if output_file.endswith('.json'):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif output_file.endswith('.csv'):
            self._save_results_csv(results, output_file)
        else:
            # 默认保存为JSON
            with open(output_file + '.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 结果已保存")
    
    def _save_results_csv(self, results: List[Dict[str, Any]], output_file: str):
        """保存结果为CSV格式"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题行
            headers = [
                'id', 'description', 'moves_count', 'analysis_time',
                'winrate', 'score_mean', 'visits', 'best_move', 'best_move_winrate'
            ]
            writer.writerow(headers)
            
            # 写入数据行
            for result in results:
                row = []
                row.append(result.get('id', ''))
                row.append(result.get('job_description', ''))
                row.append(len(result.get('moves', [])))
                row.append(f"{result.get('analysis_time', 0):.3f}")
                
                # 提取根节点信息
                root_info = result.get('rootInfo', {})
                row.append(f"{root_info.get('winrate', 0):.4f}")
                row.append(f"{root_info.get('scoreMean', 0):.2f}")
                row.append(root_info.get('visits', 0))
                
                # 提取最佳移动
                move_infos = result.get('moveInfos', [])
                if move_infos:
                    best_move = move_infos[0]
                    row.append(best_move.get('move', ''))
                    row.append(f"{best_move.get('winrate', 0):.4f}")
                else:
                    row.append('')
                    row.append('')
                
                writer.writerow(row)


def load_jobs_from_file(input_file: str) -> List[AnalysisJob]:
    """从文件加载分析任务"""
    jobs = []
    
    if input_file.endswith('.json'):
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                job = AnalysisJob(
                    id=item.get('id', f"job_{len(jobs)}"),
                    moves=item.get('moves', []),
                    board_size=item.get('board_size', 19),
                    komi=item.get('komi', 7.5),
                    rules=item.get('rules', 'tromp-taylor'),
                    max_visits=item.get('max_visits', 1000),
                    description=item.get('description', '')
                )
                jobs.append(job)
    
    elif input_file.endswith('.csv'):
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 解析移动序列
                moves_str = row.get('moves', '')
                moves = []
                if moves_str:
                    try:
                        moves = json.loads(moves_str)
                    except:
                        # 尝试简单格式: "B D4, W Q16"
                        for move_str in moves_str.split(','):
                            move_str = move_str.strip()
                            if ' ' in move_str:
                                color, pos = move_str.split(' ', 1)
                                moves.append([color.strip(), pos.strip()])
                
                job = AnalysisJob(
                    id=row.get('id', f"job_{len(jobs)}"),
                    moves=moves,
                    board_size=int(row.get('board_size', 19)),
                    komi=float(row.get('komi', 7.5)),
                    rules=row.get('rules', 'tromp-taylor'),
                    max_visits=int(row.get('max_visits', 1000)),
                    description=row.get('description', '')
                )
                jobs.append(job)
    
    return jobs


def create_sample_jobs() -> List[AnalysisJob]:
    """创建示例分析任务"""
    jobs = []
    
    # 1. 空棋盘
    jobs.append(AnalysisJob(
        id="empty_board",
        moves=[],
        description="空棋盘开局分析"
    ))
    
    # 2. 各种开局
    openings = [
        {
            "id": "star_point_opening",
            "moves": [["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"]],
            "description": "四角星位开局"
        },
        {
            "id": "komoku_opening",
            "moves": [["B", "D4"], ["W", "Q16"], ["B", "R4"], ["W", "C16"]],
            "description": "小目开局"
        },
        {
            "id": "sansan_opening",
            "moves": [["B", "C3"], ["W", "Q16"], ["B", "Q3"], ["W", "C16"]],
            "description": "三三开局"
        },
        {
            "id": "high_approach",
            "moves": [["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"], ["B", "F3"]],
            "description": "高挂开局"
        },
        {
            "id": "low_approach",
            "moves": [["B", "D4"], ["W", "Q16"], ["B", "Q4"], ["W", "D16"], ["B", "F4"]],
            "description": "低挂开局"
        }
    ]
    
    for opening in openings:
        jobs.append(AnalysisJob(
            id=opening["id"],
            moves=opening["moves"],
            description=opening["description"]
        ))
    
    # 3. 不同访问数的测试
    for visits in [100, 500, 1000, 2000]:
        jobs.append(AnalysisJob(
            id=f"visits_test_{visits}",
            moves=[["B", "D4"], ["W", "Q16"]],
            max_visits=visits,
            description=f"访问数测试 - {visits}"
        ))
    
    # 4. 不同棋盘大小
    for size in [9, 13, 19]:
        jobs.append(AnalysisJob(
            id=f"board_size_{size}",
            moves=[],
            board_size=size,
            description=f"{size}x{size} 棋盘分析"
        ))
    
    # 5. 不同贴目
    for komi in [0.5, 5.5, 7.5, 9.5]:
        jobs.append(AnalysisJob(
            id=f"komi_{komi}",
            moves=[["B", "D4"], ["W", "Q16"]],
            komi=komi,
            description=f"贴目 {komi} 分析"
        ))
    
    return jobs


def create_sample_input_file(filename: str):
    """创建示例输入文件"""
    jobs = create_sample_jobs()
    
    if filename.endswith('.json'):
        data = []
        for job in jobs:
            data.append({
                "id": job.id,
                "moves": job.moves,
                "board_size": job.board_size,
                "komi": job.komi,
                "rules": job.rules,
                "max_visits": job.max_visits,
                "description": job.description
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif filename.endswith('.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'moves', 'board_size', 'komi', 'rules', 'max_visits', 'description'])
            
            for job in jobs:
                writer.writerow([
                    job.id,
                    json.dumps(job.moves),
                    job.board_size,
                    job.komi,
                    job.rules,
                    job.max_visits,
                    job.description
                ])
    
    print(f"✅ 示例输入文件已创建: {filename}")


def main():
    parser = argparse.ArgumentParser(description="KataGo HTTP批量分析")
    parser.add_argument("--host", default="localhost", help="服务器地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口 (默认: 8080)")
    parser.add_argument("--input", help="输入文件 (JSON或CSV格式)")
    parser.add_argument("--output", help="输出文件 (JSON或CSV格式)")
    parser.add_argument("--workers", type=int, default=4, help="并发工作线程数 (默认: 4)")
    parser.add_argument("--create-sample", help="创建示例输入文件")
    
    args = parser.parse_args()
    
    # 创建示例文件
    if args.create_sample:
        create_sample_input_file(args.create_sample)
        return
    
    print("🚀 KataGo HTTP批量分析工具")
    print(f"🌐 连接到: http://{args.host}:{args.port}")
    
    try:
        analyzer = BatchAnalyzer(args.host, args.port)
        
        # 加载任务
        if args.input and os.path.exists(args.input):
            print(f"📂 从文件加载任务: {args.input}")
            jobs = load_jobs_from_file(args.input)
        else:
            print("📋 使用示例任务")
            jobs = create_sample_jobs()
        
        if not jobs:
            print("❌ 没有找到分析任务")
            return
        
        # 执行批量分析
        results = analyzer.analyze_batch(jobs, args.workers)
        
        # 保存结果
        if args.output:
            analyzer.save_results(results, args.output)
        else:
            # 默认输出文件名
            timestamp = int(time.time())
            default_output = f"batch_analysis_results_{timestamp}.json"
            analyzer.save_results(results, default_output)
        
        print("\n🎉 批量分析完成！")
        
    except KeyboardInterrupt:
        print("\n🛑 批量分析被用户中断")
    except Exception as e:
        print(f"💥 批量分析异常: {e}")


if __name__ == "__main__":
    main()