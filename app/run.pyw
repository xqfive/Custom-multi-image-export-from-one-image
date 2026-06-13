import sys
import os

# 获取当前脚本所在目录
if getattr(sys, 'frozen', False):
    # 打包后的环境
    current_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 将项目根目录添加到Python路径
sys.path.insert(0, current_dir)

# 直接导入main模块中的main函数
import main

if __name__ == "__main__":
    main.main()
