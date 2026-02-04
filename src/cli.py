#!/usr/bin/env python3
"""
msearch CLI工具 - 用于测试和调试msearch系统
封装所有API接口，提供命令行访问方式
"""

import sys
import os
import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests


class MSearchCLI:
    """msearch CLI工具类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化CLI工具

        Args:
            base_url: API服务器基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        files: dict = None,
        params: dict = None,
    ) -> dict:
        """
        发送HTTP请求

        Args:
            method: HTTP方法（GET/POST）
            endpoint: API端点
            data: 请求体数据
            files: 上传文件
            params: 查询参数

        Returns:
            响应JSON数据
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, data=data, files=files)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            print(f"错误: HTTP {e.response.status_code}")
            try:
                print(f"详情: {e.response.json()['detail']}")
            except:
                print(f"详情: {e.response.text}")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print(f"错误: 无法连接到API服务器 ({self.base_url})")
            print("请确保API服务器正在运行: python3 src/api_server.py")
            sys.exit(1)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)

    def health_check(self):
        """健康检查"""
        print("=" * 60)
        print("健康检查")
        print("=" * 60)

        result = self._request("GET", "/api/v1/health")

        print(f"状态: {result.get('success')}")
        print("\n组件状态:")
        for component, status in result["components"].items():
            print(f"  - {component}: {status}")

        print("\n✓ 系统运行正常")

    def system_info(self):
        """系统信息"""
        print("=" * 60)
        print("系统信息")
        print("=" * 60)

        result = self._request("GET", "/api/v1/system/info")

        print(f"状态: {result.get('success')}")
        print("\n配置信息:")
        for key, value in result["config"].items():
            print(f"  - {key}: {value}")

    def vector_stats(self):
        """向量统计"""
        print("=" * 60)
        print("向量统计")
        print("=" * 60)

        result = self._request("GET", "/api/v1/vector/stats")

        print(f"表名: {result.get('collection_name', 'N/A')}")
        print(f"总向量数: {result.get('total_vectors', 0)}")
        print(f"向量维度: {result.get('vector_dimension', 'N/A')}")

        if "modality_counts" in result:
            print("\n模态分布:")
            for modality, count in result["modality_counts"].items():
                print(f"  - {modality}: {count}")

    def search_text(self, query: str, top_k: int = 20):
        """文本搜索"""
        print("=" * 60)
        print(f"文本搜索: {query}")
        print("=" * 60)

        result = self._request(
            "POST", "/api/v1/search/text", data={"query": query, "top_k": top_k}
        )

        print(f"查询: {result['query']}")
        print(f"结果数: {result['total']}")

        if result["results"]:
            print("\n搜索结果:")
            for i, item in enumerate(result["results"][:10], 1):
                score = item.get("score", "N/A")
                if isinstance(score, (int, float)):
                    score = f"{score:.4f}"
                print(f"\n  [{i}] 相似度: {score}")
                print(f"      文件名: {item.get('file_name', 'N/A')}")
                print(f"      文件路径: {item.get('file_path', 'N/A')}")
                print(f"      模态: {item.get('modality', 'N/A')}")
        else:
            print("\n未找到匹配结果")

    def search_image(self, image_path: str, top_k: int = 20):
        """图像搜索"""
        print("=" * 60)
        print(f"图像搜索: {image_path}")
        print("=" * 60)

        if not os.path.exists(image_path):
            print(f"错误: 文件不存在: {image_path}")
            sys.exit(1)

        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            result = self._request(
                "POST", "/api/v1/search/image", files=files, data={"top_k": top_k}
            )

        print(f"图像: {result['image']}")
        print(f"结果数: {result['total']}")

        if result["results"]:
            print("\n搜索结果:")
            for i, item in enumerate(result["results"][:10], 1):
                score = item.get("score", "N/A")
                if isinstance(score, (int, float)):
                    score = f"{score:.4f}"
                print(f"\n  [{i}] 相似度: {score}")
                print(f"      文件名: {item.get('file_name', 'N/A')}")
                print(f"      文件路径: {item.get('file_path', 'N/A')}")
                print(f"      模态: {item.get('modality', 'N/A')}")
        else:
            print("\n未找到匹配结果")

    def search_audio(self, audio_path: str, top_k: int = 20):
        """音频搜索"""
        print("=" * 60)
        print(f"音频搜索: {audio_path}")
        print("=" * 60)

        if not os.path.exists(audio_path):
            print(f"错误: 文件不存在: {audio_path}")
            sys.exit(1)

        with open(audio_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_path), f, "audio/wav")}
            result = self._request(
                "POST", "/api/v1/search/audio", files=files, data={"top_k": top_k}
            )

        print(f"音频: {result['audio']}")
        print(f"结果数: {result['total']}")

        if result["results"]:
            print("\n搜索结果:")
            for i, item in enumerate(result["results"][:10], 1):
                score = item.get("score", "N/A")
                if isinstance(score, (int, float)):
                    score = f"{score:.4f}"
                print(f"\n  [{i}] 相似度: {score}")
                print(f"      文件名: {item.get('file_name', 'N/A')}")
                print(f"      文件路径: {item.get('file_path', 'N/A')}")
                print(f"      模态: {item.get('modality', 'N/A')}")
        else:
            print("\n未找到匹配结果")

    def task_stats(self):
        """任务统计"""
        print("=" * 60)
        print("任务统计")
        print("=" * 60)

        result = self._request("GET", "/api/v1/tasks/stats")

        print("\n总体统计:")
        overall = result["task_stats"]["overall"]
        total_tasks = result["task_stats"]["total"]
        print(f"  - 总任务数: {total_tasks}")
        print(f"  - 待处理: {overall['pending']}")
        print(f"  - 运行中: {overall['running']}")
        print(f"  - 已完成: {overall['completed']}")
        print(f"  - 失败: {overall['failed']}")
        print(f"  - 已取消: {overall['cancelled']}")

        if result["task_stats"]["by_type"]:
            print("\n按类型统计:")
            for task_type, stats in result["task_stats"]["by_type"].items():
                print(f"  - {task_type}:")
                print(f"      总数: {stats.get('total', 0)}")
                print(f"      完成: {stats.get('completed', 0)}")
                print(f"      失败: {stats.get('failed', 0)}")

        print(f"\n并发数: {result['concurrency']}")

        print("\n资源使用:")
        resources = result["resource_usage"]
        print(f"  - CPU: {resources['cpu_percent']:.1f}%")
        print(f"  - 内存: {resources['memory_percent']:.1f}%")
        print(f"  - GPU: {resources['gpu_percent']:.1f}%")

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
    ):
        """列出任务"""
        print("=" * 60)
        print("任务列表")
        print("=" * 60)

        params = {"limit": limit}
        if status:
            params["status"] = status
        if task_type:
            params["task_type"] = task_type

        result = self._request("GET", "/api/v1/tasks", params=params)

        print(f"任务总数: {result['total_tasks']}")

        if result["tasks"]:
            print("\n任务列表:")
            for i, task in enumerate(result["tasks"], 1):
                print(f"\n  [{i}] 任务ID: {task['task_id'][:8]}...")
                print(f"      类型: {task['task_type']}")
                print(f"      状态: {task['status']}")
                print(f"      优先级: {task['priority']}")
                print(f"      进度: {task['progress']:.1%}")
                if task.get("current_step"):
                    print(f"      当前步骤: {task['current_step']}")
                print(f"      创建时间: {task['created_at'][:19]}")
        else:
            print("\n暂无任务")

    def get_task(self, task_id: str):
        """获取任务详情"""
        print("=" * 60)
        print(f"任务详情: {task_id}")
        print("=" * 60)

        result = self._request("GET", f"/api/v1/tasks/{task_id}")

        print(f"任务ID: {result['task_id']}")
        print(f"类型: {result['task_type']}")
        print(f"状态: {result.get('success')}")
        print(f"优先级: {result['priority']}")
        print(f"进度: {result['progress']:.1%}")
        print(f"创建时间: {result['created_at']}")
        if result.get("started_at"):
            print(f"开始时间: {result['started_at']}")
        if result.get("completed_at"):
            print(f"完成时间: {result['completed_at']}")
        if result.get("current_step"):
            print(f"当前步骤: {result['current_step']}")
        if result.get("step_progress"):
            print(f"步骤进度: {result['step_progress']:.1%}")
        if result.get("error"):
            print(f"错误: {result['error']}")
        if result.get("result"):
            print(f"结果: {result['result']}")

        if result.get("task_data"):
            print(f"\n任务数据:")
            for key, value in result["task_data"].items():
                print(f"  - {key}: {value}")

    def cancel_task(self, task_id: str):
        """取消任务"""
        print("=" * 60)
        print(f"取消任务: {task_id}")
        print("=" * 60)

        result = self._request("POST", f"/api/v1/tasks/{task_id}/cancel")

        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")

    def update_priority(self, task_id: str, priority: int):
        """更新任务优先级"""
        print("=" * 60)
        print(f"更新任务优先级: {task_id}")
        print("=" * 60)

        result = self._request(
            "POST", f"/api/v1/tasks/{task_id}/priority", data={"priority": priority}
        )

        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")
        print(f"新优先级: {result['result']['new_priority']}")

    def cancel_all_tasks(self, cancel_running: bool = False):
        """取消所有任务"""
        print("=" * 60)
        print("取消所有任务")
        print("=" * 60)

        result = self._request(
            "POST",
            "/api/v1/tasks/cancel-all",
            data={"cancel_running": str(cancel_running).lower()},
        )

        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")
        print(f"\n取消统计:")
        print(f"  - 已取消: {result['result']['cancelled']}")
        print(f"  - 失败: {result['result']['failed']}")
        print(f"  - 总计: {result['result']['total']}")

    def cancel_tasks_by_type(self, task_type: str, cancel_running: bool = False):
        """按类型取消任务"""
        print("=" * 60)
        print(f"取消{task_type}类型任务")
        print("=" * 60)

        result = self._request(
            "POST",
            "/api/v1/tasks/cancel-by-type",
            data={
                "task_type": task_type,
                "cancel_running": str(cancel_running).lower(),
            },
        )

        print(f"成功: {result['success']}")
        print(f"消息: {result['message']}")
        print(f"\n取消统计:")
        print(f"  - 任务类型: {result['result']['task_type']}")
        print(f"  - 已取消: {result['result']['cancelled']}")
        print(f"  - 失败: {result['result']['failed']}")
        print(f"  - 总计: {result['result']['total']}")

    def index_file(self, file_path: str):
        """索引单个文件"""
        print("=" * 60)
        print(f"索引文件: {file_path}")
        print("=" * 60)

        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}")
            sys.exit(1)

        # 创建索引任务
        result = self._request(
            "POST", "/api/v1/index/file", data={"file_path": file_path}
        )

        print(f"任务ID: {result.get('data', {}).get('task_id')}")
        print(f"状态: {result.get('success')}")
        print(f"消息: {result['message']}")

        if result.get("task_id"):
            print(f"\n您可以使用以下命令查看任务进度:")
            print(
                f"  python src/cli.py task get {result.get('data', {}).get('task_id')}"
            )

    def index_directory(self, directory: str, recursive: bool = True):
        """索引目录"""
        print("=" * 60)
        print(f"索引目录: {directory}")
        print("=" * 60)

        if not os.path.isdir(directory):
            print(f"错误: 目录不存在: {directory}")
            sys.exit(1)

        # 创建索引任务
        result = self._request(
            "POST",
            "/api/v1/index/directory",
            data={"directory": directory, "recursive": str(recursive).lower()},
        )

        print(f"任务ID: {result.get('data', {}).get('task_id')}")
        print(f"状态: {result.get('success')}")
        print(f"消息: {result['message']}")

        if result.get("stats"):
            print(f"\n扫描统计:")
            stats = result["stats"]
            print(f"  - 总文件数: {stats.get('total_files', 0)}")
            print(f"  - 图像文件: {stats.get('image_files', 0)}")
            print(f"  - 视频文件: {stats.get('video_files', 0)}")
            print(f"  - 音频文件: {stats.get('audio_files', 0)}")
            print(f"  - 其他文件: {stats.get('other_files', 0)}")

        if result.get("task_id"):
            print(f"\n您可以使用以下命令查看任务进度:")
            print(
                f"  python src/cli.py task get {result.get('data', {}).get('task_id')}"
            )

    def reindex_all(self):
        """重新索引所有文件"""
        print("=" * 60)
        print("重新索引所有文件")
        print("=" * 60)

        result = self._request("POST", "/api/v1/index/reindex-all")

        print(f"任务ID: {result.get('data', {}).get('task_id')}")
        print(f"状态: {result.get('success')}")
        print(f"消息: {result['message']}")

        if result.get("task_id"):
            print(f"\n您可以使用以下命令查看任务进度:")
            print(
                f"  python src/cli.py task get {result.get('data', {}).get('task_id')}"
            )

    def get_index_status(self):
        """获取索引状态"""
        print("=" * 60)
        print("索引状态")
        print("=" * 60)

        result = self._request("GET", "/api/v1/index/status")

        print(f"状态: {result.get('success')}")

        if result.get("stats"):
            stats = result["stats"]
            print(f"\n索引统计:")
            print(f"  - 总文件数: {stats.get('total_files', 0)}")
            print(f"  - 已索引: {stats.get('indexed_files', 0)}")
            print(f"  - 待处理: {stats.get('pending_files', 0)}")
            print(f"  - 处理中: {stats.get('processing_files', 0)}")
            print(f"  - 失败: {stats.get('failed_files', 0)}")

            if stats.get("modality_counts"):
                print(f"\n模态分布:")
                for modality, count in stats["modality_counts"].items():
                    print(f"  - {modality}: {count}")

        if result.get("last_index_time"):
            print(f"\n最后索引时间: {result['last_index_time']}")

        if result.get("current_tasks"):
            print(f"\n当前索引任务:")
            for task in result["current_tasks"]:
                print(f"  - {task['task_id'][:8]}... ({task['task_type']})")
                print(f"    进度: {task['progress']:.1%}")
                print(f"    状态: {task['status']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="msearch CLI工具 - 用于测试和调试msearch系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 健康检查
  python src/cli.py health
  
  # 文本搜索
  python src/cli.py search text "老虎"
  
  # 图像搜索
  python src/cli.py search image test.jpg
  
  # 音频搜索
  python src/cli.py search audio test.wav
  
  # 任务统计
  python src/cli.py task stats
  
  # 列出所有任务
  python src/cli.py task list
  
  # 取消所有任务
  python src/cli.py task cancel-all
  
  # 按类型取消任务
  python src/cli.py task cancel-by-type image_preprocess
  
  # 索引单个文件
  python src/cli.py index file /path/to/image.jpg
  
  # 索引目录（递归）
  python src/cli.py index directory /path/to/data
  
  # 索引目录（不递归）
  python src/cli.py index directory /path/to/data --no-recursive
  
  # 重新索引所有文件
  python src/cli.py index reindex-all
  
  # 获取索引状态
  python src/cli.py index status
        """,
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API服务器URL (默认: http://localhost:8000)",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 健康检查命令
    subparsers.add_parser("health", help="健康检查")

    # 系统信息命令
    subparsers.add_parser("info", help="系统信息")

    # 向量统计命令
    subparsers.add_parser("vector-stats", help="向量统计")

    # 搜索命令
    search_parser = subparsers.add_parser("search", help="搜索")
    search_subparsers = search_parser.add_subparsers(
        dest="search_type", help="搜索类型"
    )

    # 文本搜索
    text_search_parser = search_subparsers.add_parser("text", help="文本搜索")
    text_search_parser.add_argument("query", help="搜索查询文本")
    text_search_parser.add_argument(
        "--top-k", type=int, default=20, help="返回结果数量"
    )

    # 图像搜索
    image_search_parser = search_subparsers.add_parser("image", help="图像搜索")
    image_search_parser.add_argument("image_path", help="图像文件路径")
    image_search_parser.add_argument(
        "--top-k", type=int, default=20, help="返回结果数量"
    )

    # 音频搜索
    audio_search_parser = search_subparsers.add_parser("audio", help="音频搜索")
    audio_search_parser.add_argument("audio_path", help="音频文件路径")
    audio_search_parser.add_argument(
        "--top-k", type=int, default=20, help="返回结果数量"
    )

    # 任务命令
    task_parser = subparsers.add_parser("task", help="任务管理")
    task_subparsers = task_parser.add_subparsers(dest="task_action", help="任务操作")

    # 任务统计
    task_subparsers.add_parser("stats", help="任务统计")

    # 列出任务
    list_parser = task_subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--status", help="按状态过滤")
    list_parser.add_argument("--type", help="按类型过滤")
    list_parser.add_argument("--limit", type=int, default=20, help="返回数量限制")

    # 获取任务详情
    get_parser = task_subparsers.add_parser("get", help="获取任务详情")
    get_parser.add_argument("task_id", help="任务ID")

    # 取消任务
    cancel_parser = task_subparsers.add_parser("cancel", help="取消任务")
    cancel_parser.add_argument("task_id", help="任务ID")

    # 更新优先级
    priority_parser = task_subparsers.add_parser("priority", help="更新任务优先级")
    priority_parser.add_argument("task_id", help="任务ID")
    priority_parser.add_argument("priority", type=int, help="新的优先级 (0-11)")

    # 取消所有任务
    cancel_all_parser = task_subparsers.add_parser("cancel-all", help="取消所有任务")
    cancel_all_parser.add_argument(
        "--cancel-running", action="store_true", help="同时取消正在运行的任务"
    )

    # 按类型取消任务
    cancel_type_parser = task_subparsers.add_parser(
        "cancel-by-type", help="按类型取消任务"
    )
    cancel_type_parser.add_argument("task_type", help="任务类型")
    cancel_type_parser.add_argument(
        "--cancel-running", action="store_true", help="同时取消正在运行的任务"
    )

    # 索引命令
    index_parser = subparsers.add_parser("index", help="文件索引")
    index_subparsers = index_parser.add_subparsers(dest="index_action", help="索引操作")

    # 索引单个文件
    index_file_parser = index_subparsers.add_parser("file", help="索引单个文件")
    index_file_parser.add_argument("file_path", help="文件路径")

    # 索引目录
    index_dir_parser = index_subparsers.add_parser("directory", help="索引目录")
    index_dir_parser.add_argument("directory", help="目录路径")
    index_dir_parser.add_argument(
        "--no-recursive", action="store_true", help="不递归索引子目录"
    )

    # 重新索引所有文件
    index_subparsers.add_parser("reindex-all", help="重新索引所有文件")

    # 获取索引状态
    index_subparsers.add_parser("status", help="获取索引状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 创建CLI实例
    cli = MSearchCLI(base_url=args.url)

    # 执行命令
    try:
        if args.command == "health":
            cli.health_check()

        elif args.command == "info":
            cli.system_info()

        elif args.command == "vector-stats":
            cli.vector_stats()

        elif args.command == "search":
            if args.search_type == "text":
                cli.search_text(args.query, args.top_k)
            elif args.search_type == "image":
                cli.search_image(args.image_path, args.top_k)
            elif args.search_type == "audio":
                cli.search_audio(args.audio_path, args.top_k)
            else:
                parser.print_help()
                sys.exit(1)

        elif args.command == "task":
            if args.task_action == "stats":
                cli.task_stats()
            elif args.task_action == "list":
                cli.list_tasks(
                    status=args.status, task_type=args.type, limit=args.limit
                )
            elif args.task_action == "get":
                cli.get_task(args.task_id)
            elif args.task_action == "cancel":
                cli.cancel_task(args.task_id)
            elif args.task_action == "priority":
                cli.update_priority(args.task_id, args.priority)
            elif args.task_action == "cancel-all":
                cli.cancel_all_tasks(cancel_running=args.cancel_running)
            elif args.task_action == "cancel-by-type":
                cli.cancel_tasks_by_type(
                    args.task_type, cancel_running=args.cancel_running
                )
            else:
                parser.print_help()
                sys.exit(1)

        elif args.command == "index":
            if args.index_action == "file":
                cli.index_file(args.file_path)
            elif args.index_action == "directory":
                cli.index_directory(args.directory, recursive=not args.no_recursive)
            elif args.index_action == "reindex-all":
                cli.reindex_all()
            elif args.index_action == "status":
                cli.get_index_status()
            else:
                parser.print_help()
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
