import sys
import os
# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from main_window import ImageCropperWindow
from config import APP_NAME

def main():
    """程序入口"""
    app = QApplication(sys.argv)
    window = ImageCropperWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()