# 数据库配置
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# PDF 文件存储路径, 可以直接指定该路径（完整），也可以等待自动创建
__DATA_STORAGE_DIR = ""


def get_data_storage_dir():
    """
    获取数据存储路径
    :return: 数据存储路径
    """
    if __DATA_STORAGE_DIR and not __DATA_STORAGE_DIR.trim():
        return __DATA_STORAGE_DIR
    current_file = Path(__file__).resolve()
    # 获取项目根目录, 默认为上一级目录
    # 这里假设 config.py 在 Backend/app/config.py 中， data 文件夹在 Backend/data/ 目录下
    project_root = current_file.parents[1]
    return project_root / "data"
