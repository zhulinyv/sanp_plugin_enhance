import random
from pathlib import Path

from utils.env import env
from utils.imgtools import get_img_info, img_to_base64

if "nai-diffusion-4" not in env.model:
    from utils.jsondata import json_for_i2i
else:
    from utils.jsondata import json_for_i2i_v4 as json_for_i2i

from utils.prepare import logger
from utils.utils import (
    file_path2dir,
    file_path2list,
    file_path2name,
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
    if "nai-diffusion-4" not in env.model:
        json_for_i2i["parameters"]["sm"] = False
        json_for_i2i["parameters"]["sm_dyn"] = False
    try:
        variety = img_comment["skip_cfg_above_sigma"]
    except KeyError:
        logger.warning("旧版图片不支持 variety 参数, 将使用配置设置中的 variety 参数")
        variety = env.variety
    json_for_i2i["parameters"]["skip_cfg_above_sigma"] = 19 if variety else None
    json_for_i2i["parameters"]["dynamic_thresholding"] = img_comment[
        "dynamic_thresholding"
    ]
    try:
        json_for_i2i["parameters"]["noise_schedule"] = img_comment["noise_schedule"]
    except KeyError:
        pass
    json_for_i2i["parameters"]["seed"] = seed
    json_for_i2i["parameters"]["image"] = img_to_base64(imgpath)
    json_for_i2i["parameters"]["extra_noise_seed"] = seed
    json_for_i2i["parameters"]["negative_prompt"] = img_comment["uc"]

    if "nai-diffusion-4" in env.model:
        try:
            json_for_i2i["parameters"]["use_coords"] = img_comment["v4_prompt"][
                "use_coords"
            ]
            json_for_i2i["parameters"]["v4_prompt"]["caption"]["base_caption"] = (
                img_comment["v4_prompt"]["caption"]["base_caption"]
            )
            json_for_i2i["parameters"]["v4_prompt"]["use_coords"] = img_comment[
                "v4_prompt"
            ]["use_coords"]
            json_for_i2i["parameters"]["v4_negative_prompt"]["caption"][
                "base_caption"
            ] = img_comment["uc"]

            num = 0
            for char_captions in img_comment["v4_prompt"]["caption"]["char_captions"]:
                json_for_i2i["parameters"]["characterPrompts"] = []
                json_for_i2i["parameters"]["characterPrompts"].append(
                    {
                        "prompt": char_captions["char_caption"],
                        "uc": img_comment["v4_negative_prompt"]["caption"][
                            "char_captions"
                        ][num]["char_caption"],
                        "center": {
                            "x": char_captions["centers"][0]["x"],
                            "y": char_captions["centers"][0]["y"],
                        },
                    }
                )
                num += 1
        except KeyError:
            logger.warning("正在使用 NAI3 生成的图片使用 NAI4 图生图!")
            json_for_i2i["parameters"]["use_coords"] = False
            json_for_i2i["parameters"]["v4_prompt"]["caption"]["base_caption"] = ""
            json_for_i2i["parameters"]["v4_prompt"]["use_coords"] = False
            json_for_i2i["parameters"]["v4_negative_prompt"]["caption"][
                "base_caption"
            ] = ""

    return json_for_i2i, json_for_i2i["parameters"]["seed"]


def main(input_image: str, input_path, batch):
    if batch:
        i2i_path = Path(input_path)
        img_list = file_path2list(i2i_path)
    else:
        i2i_path = Path(file_path2dir(input_image))
        img_list = [file_path2name(input_image)]

    for img in img_list:
        times = 1
        while times <= 5:
            try:
                logger.info(f"正在 Enhance: {img}...")
                info_list = img.replace(".png", "").replace(".jpg", "").split("_")
                img_path = i2i_path / img
                json_data, seed = prepare_json(get_img_info(img_path), img_path)

                try:
                    seed = info_list[0]
                    choose_game = info_list[1]
                    choose_character = info_list[2]
                except Exception:
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
