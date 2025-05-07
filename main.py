import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QSize

# 创建必要的目录
def ensure_directories():
    """确保必要的目录存在"""
    directories = ["data"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

# 导入各个页面
from pages.student_page import StudentPage
from pages.department_page import DepartmentPage
from pages.rotation_page import RotationPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("医学生轮转排期系统")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Microsoft YaHei", 10))
        
        # 添加三个主要页面
        self.student_page = StudentPage()
        self.department_page = DepartmentPage()
        self.rotation_page = RotationPage(self.student_page, self.department_page)
        
        self.tabs.addTab(self.student_page, "学生录入")
        self.tabs.addTab(self.department_page, "科室配置")
        self.tabs.addTab(self.rotation_page, "轮转排期")
        
        self.setCentralWidget(self.tabs)

if __name__ == "__main__":
    # 确保目录存在
    ensure_directories()
    
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec()) 