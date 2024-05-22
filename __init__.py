from pathlib import Path

import gradio as gr

from plugins.i2i.sanp_plugin_enhance.utils import main
from utils.utils import open_folder


def plugin():
    with gr.Tab("Enhance"):
        with gr.Row():
            with gr.Column(scale=6):
                gr.Markdown(
                    "> NovelAI 的 Enhance 功能, 本质就是图生图, 甚至重绘幅度是固定的 0.2"
                )
            with gr.Row():
                folder = gr.Textbox(Path("./output/enhance"), visible=False)
                open_folder_ = gr.Button("打开保存目录")
                open_folder_.click(open_folder, inputs=folder)
        with gr.Row():
            with gr.Column():
                enhance_button = gr.Button("开始 Enhance")
                input_image = gr.Image(label="要 Enhance 的图片", type="pil")
                with gr.Row():
                    input_path = gr.Textbox(value=None, label="批处理路径", scale=3)
                    batch = gr.Checkbox(value=False, label="是否启用批处理")
            with gr.Column():
                output_info = gr.Textbox(label="输出信息")
                output_image = gr.Image()

            enhance_button.click(
                main,
                inputs=[input_image, input_path, batch],
                outputs=[output_info, output_image],
            )
