"""智能剪贴板翻译器 - 入口文件"""

import sys
import os

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db
from gui import App


def main():
    # 初始化数据库
    init_db()
    # 启动 GUI
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
