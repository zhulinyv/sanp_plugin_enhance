import random
from pathlib import Path

import ujson as json
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from utils.env import env
from utils.imgtools import get_img_info, img_to_base64, return_pnginfo
from utils.jsondata import json_for_i2i
from utils.prepare import logger
from utils.utils import (
    file_path2list,
    generate_image,
    save_image,
    sleep_for_cool,
)


def prepare_json(imginfo: dict, imgpath):
    if imginfo["Software"] != "NovelAI":
        logger.error("不是 NovelAI 生成的图片!")
        return
    img_comment = imginfo["Comment"]
    seed = random.randint(1000000000, 9999999999)
    json_for_i2i["input"] = img_comment["prompt"]
    json_for_i2i["parameters"]["width"] = img_comment["width"]
    json_for_i2i["parameters"]["height"] = img_comment["height"]
    json_for_i2i["parameters"]["scale"] = img_comment["scale"]
    json_for_i2i["parameters"]["sampler"] = img_comment["sampler"]
    json_for_i2i["parameters"]["steps"] = img_comment["steps"]
    json_for_i2i["parameters"]["strength"] = 0.2
    json_for_i2i["parameters"]["noise"] = 0
    json_for_i2i["parameters"]["sm"] = img_comment["sm"]
    json_for_i2i["parameters"]["sm_dyn"] = img_comment["sm_dyn"]
    try:
        skip_cfg_above_sigma = img_comment["skip_cfg_above_sigma"]
    except KeyError:
        skip_cfg_above_sigma = None
    json_for_i2i["parameters"]["skip_cfg_above_sigma"] = skip_cfg_above_sigma
    json_for_i2i["parameters"]["dynamic_thresholding"] = img_comment[
        "dynamic_thresholding"
    ]
    json_for_i2i["parameters"]["noise_schedule"] = img_comment["noise_schedule"]
    json_for_i2i["parameters"]["seed"] = seed
    json_for_i2i["parameters"]["image"] = img_to_base64(imgpath)
    json_for_i2i["parameters"]["extra_noise_seed"] = seed
    json_for_i2i["parameters"]["negative_prompt"] = img_comment["uc"]

    return json_for_i2i, json_for_i2i["parameters"]["seed"]


def main(input_image: Image.Image, input_path, batch):
    if batch:
        i2i_path = Path(input_path)
        img_list = file_path2list(i2i_path)
    else:
        info = json.loads(return_pnginfo(input_image)[-1])
        software = info["Software"]
        comment = info["Comment"]
        metadata = PngInfo()
        metadata.add_text("Software", software)
        metadata.add_text("Comment", str(comment))

        input_image.save("./output/temp.png", pnginfo=metadata)
        i2i_path = Path("./output")
        img_list = ["temp.png"]

    for img in img_list:
        times = 1
        while times <= 5:
            try:
                logger.info(f"正在 Enhance: {img}...")
                info_list = img.replace(".png", "").split("_")
                img_path = i2i_path / img
                json_data, seed = prepare_json(get_img_info(img_path), img_path)

                if batch:
                    seed = info_list[0]
                    choose_game = info_list[1]
                    choose_character = info_list[2]
                else:
                    seed = seed
                    choose_game = "None"
                    choose_character = "None"

                saved_path = save_image(
                    generate_image(json_data),
                    "enhance",
                    seed,
                    choose_game,
                    choose_character,
                )
                if saved_path != "寄":
                    pass
                else:
                    raise Exception
                sleep_for_cool(env.i2i_cool_time - 3, env.i2i_cool_time + 3)
                break
            except Exception as e:
                sleep_for_cool(4, 8)
                times += 1
                logger.error(f"出现错误: {e}")
                logger.warning(f"重试 {times-1}/5...")

    return "Enhance 完成!", saved_path
