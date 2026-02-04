"""
简化版WebUI应用，只保留核心检索功能
"""
import gradio as gr
import os
import sys
from typing import Dict, Any, List
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.webui.api_client import APIClient

logger = logging.getLogger(__name__)


class SimpleMSearchWebUI:
    """简化版msearch WebUI，只保留核心检索功能"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        初始化简化版WebUI

        Args:
            api_base_url: API服务器基础URL
        """
        self.api_client = APIClient(api_base_url)
        self.demo = self._create_interface()

    def _create_interface(self):
        """创建界面"""
        with gr.Blocks(title="msearch - 简化版检索界面") as demo:
            gr.Markdown("# 🔍 msearch 简化检索界面")
            gr.Markdown("支持文本、图像和音频检索")

            with gr.Tabs():
                # 文本检索标签页
                with gr.Tab("📝 文本检索"):
                    with gr.Row():
                        with gr.Column():
                            text_query = gr.Textbox(
                                label="输入搜索文本",
                                placeholder="请输入要搜索的内容...",
                                lines=3
                            )
                            text_top_k = gr.Slider(
                                minimum=1,
                                maximum=50,
                                value=20,
                                step=1,
                                label="返回结果数量"
                            )
                            text_threshold = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.0,
                                step=0.01,
                                label="相似度阈值 (可选)"
                            )
                            text_search_btn = gr.Button("🔍 搜索", variant="primary")
                        
                        with gr.Column():
                            text_results = gr.Gallery(
                                label="检索结果",
                                show_label=True,
                                elem_id="text_gallery",
                                columns=4,
                                object_fit="contain",
                                height="auto"
                            )
                            text_status = gr.Textbox(
                                label="状态信息",
                                interactive=False
                            )

                    text_search_btn.click(
                        fn=self._text_search,
                        inputs=[text_query, text_top_k, text_threshold],
                        outputs=[text_results, text_status]
                    )

                # 图像检索标签页
                with gr.Tab("🖼️ 图像检索"):
                    with gr.Row():
                        with gr.Column():
                            image_query = gr.Image(
                                label="上传参考图像",
                                type="filepath"
                            )
                            image_top_k = gr.Slider(
                                minimum=1,
                                maximum=50,
                                value=20,
                                step=1,
                                label="返回结果数量"
                            )
                            image_search_btn = gr.Button("🔍 搜索", variant="primary")
                        
                        with gr.Column():
                            image_results = gr.Gallery(
                                label="检索结果",
                                show_label=True,
                                elem_id="image_gallery",
                                columns=4,
                                object_fit="contain",
                                height="auto"
                            )
                            image_status = gr.Textbox(
                                label="状态信息",
                                interactive=False
                            )

                    image_search_btn.click(
                        fn=self._image_search,
                        inputs=[image_query, image_top_k],
                        outputs=[image_results, image_status]
                    )

                # 音频检索标签页
                with gr.Tab("🎵 音频检索"):
                    with gr.Row():
                        with gr.Column():
                            audio_query = gr.Audio(
                                label="上传参考音频",
                                type="filepath"
                            )
                            audio_top_k = gr.Slider(
                                minimum=1,
                                maximum=50,
                                value=20,
                                step=1,
                                label="返回结果数量"
                            )
                            audio_search_btn = gr.Button("🔍 搜索", variant="primary")
                        
                        with gr.Column():
                            audio_results = gr.Gallery(
                                label="检索结果",
                                show_label=True,
                                elem_id="audio_gallery",
                                columns=4,
                                object_fit="contain",
                                height="auto"
                            )
                            audio_status = gr.Textbox(
                                label="状态信息",
                                interactive=False
                            )

                    audio_search_btn.click(
                        fn=self._audio_search,
                        inputs=[audio_query, audio_top_k],
                        outputs=[audio_results, audio_status]
                    )

            # 系统信息
            with gr.Accordion("ℹ️ 系统信息", open=False):
                with gr.Row():
                    with gr.Column():
                        system_info_btn = gr.Button("获取系统信息")
                        system_info_output = gr.JSON(label="系统信息")
                    
                    with gr.Column():
                        task_status_btn = gr.Button("获取任务状态")
                        task_status_output = gr.Textbox(label="任务状态", interactive=False)

                system_info_btn.click(
                    fn=self._get_system_info,
                    inputs=[],
                    outputs=[system_info_output]
                )

                task_status_btn.click(
                    fn=self._get_task_status,
                    inputs=[],
                    outputs=[task_status_output]
                )

        return demo

    def _text_search(self, query: str, top_k: int, threshold: float):
        """文本检索"""
        try:
            if not query or not query.strip():
                return None, "请输入搜索文本"
            
            params = {
                "query": query.strip(),
                "top_k": int(top_k)
            }
            if threshold and threshold > 0:
                params["threshold"] = threshold
            
            result = self.api_client.search_text(
                query=query.strip(),
                top_k=int(top_k),
                threshold=threshold if threshold > 0 else None
            )
            
            results = result.get("results", [])
            formatted_results = []
            
            for item in results:
                file_path = item.get("file_path", "")
                if os.path.exists(file_path):
                    formatted_results.append((file_path, os.path.basename(file_path)))
                else:
                    logger.warning(f"结果文件不存在: {file_path}")
            
            status = f"找到 {len(formatted_results)} 个结果"
            return formatted_results, status
            
        except Exception as e:
            logger.error(f"文本检索失败: {e}", exc_info=True)
            return None, f"检索失败: {str(e)}"

    def _image_search(self, image_path: str, top_k: int):
        """图像检索"""
        try:
            if not image_path:
                return None, "请上传图像文件"
            
            result = self.api_client.search_image(
                image_path=image_path,
                top_k=int(top_k)
            )
            
            results = result.get("results", [])
            formatted_results = []
            
            for item in results:
                file_path = item.get("file_path", "")
                if os.path.exists(file_path):
                    formatted_results.append((file_path, os.path.basename(file_path)))
                else:
                    logger.warning(f"结果文件不存在: {file_path}")
            
            status = f"找到 {len(formatted_results)} 个结果"
            return formatted_results, status
            
        except Exception as e:
            logger.error(f"图像检索失败: {e}", exc_info=True)
            return None, f"检索失败: {str(e)}"

    def _audio_search(self, audio_path: str, top_k: int):
        """音频检索"""
        try:
            if not audio_path:
                return None, "请上传音频文件"
            
            result = self.api_client.search_audio(
                audio_path=audio_path,
                top_k=int(top_k)
            )
            
            results = result.get("results", [])
            formatted_results = []
            
            for item in results:
                file_path = item.get("file_path", "")
                if os.path.exists(file_path):
                    formatted_results.append((file_path, os.path.basename(file_path)))
                else:
                    logger.warning(f"结果文件不存在: {file_path}")
            
            status = f"找到 {len(formatted_results)} 个结果"
            return formatted_results, status
            
        except Exception as e:
            logger.error(f"音频检索失败: {e}", exc_info=True)
            return None, f"检索失败: {str(e)}"

    def _get_system_info(self):
        """获取系统信息"""
        try:
            result = self.api_client.get_system_info()
            return result
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}", exc_info=True)
            return {"error": str(e)}

    def _get_task_status(self):
        """获取任务状态"""
        try:
            # 获取任务统计信息
            result = self.api_client.get_task_stats()
            if "stats" in result:
                stats = result["stats"]
                status_text = (
                    f"总任务: {stats.get('total', 0)}, "
                    f"待处理: {stats.get('pending', 0)}, "
                    f"运行中: {stats.get('running', 0)}, "
                    f"已完成: {stats.get('completed', 0)}, "
                    f"失败: {stats.get('failed', 0)}"
                )
            else:
                status_text = "无法获取任务状态"
            return status_text
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}", exc_info=True)
            return f"获取任务状态失败: {str(e)}"

    def run(self, host: str = "0.0.0.0", port: int = 7860, share: bool = False, **kwargs):
        """
        启动WebUI

        Args:
            host: 主机地址
            port: 端口号
            share: 是否创建公共链接
            **kwargs: 其他Gradio参数
        """
        print(f"启动简化版msearch WebUI，地址: http://{host}:{port}")
        self.demo.launch(
            server_name=host,
            server_port=port,
            share=share,
            **kwargs
        )


if __name__ == "__main__":
    # 创建简化版WebUI实例
    webui = SimpleMSearchWebUI()
    
    # 启动服务
    webui.run(host="0.0.0.0", port=7862)