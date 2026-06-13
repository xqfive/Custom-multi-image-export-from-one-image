import os
import sys

# 判断是否是打包后的exe运行环境
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# 全局配置常量
APP_NAME = "批量图片选区导出工具"
SHAPE_TYPES = ["正方形", "矩形", "圆形"]
MIN_SHAPE_SIZE = 1
MAX_SHAPE_SIZE = 20000
DEFAULT_SHAPE_WIDTH = 200
DEFAULT_SHAPE_HEIGHT = 200
DEFAULT_FILE_PREFIX = "v：cqxq05"
DEFAULT_SAVE_PATH = os.path.join(get_base_path(), "output")
DEFAULT_NAMING_MODE = "prefix_with_datetime"

class Config:
    """配置管理类（单例）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.shape_width = DEFAULT_SHAPE_WIDTH
            cls._instance.shape_height = DEFAULT_SHAPE_HEIGHT
            cls._instance.shape_type = SHAPE_TYPES[0]
            cls._instance.file_prefix = DEFAULT_FILE_PREFIX
            cls._instance.save_path = DEFAULT_SAVE_PATH
            cls._instance.naming_mode = DEFAULT_NAMING_MODE
            os.makedirs(cls._instance.save_path, exist_ok=True)
        return cls._instance