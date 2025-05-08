from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFileDialog, QMessageBox, QHeaderView, QGroupBox, 
                             QComboBox, QDateEdit, QSpinBox, QScrollArea,
                             QFrame, QGridLayout, QTabWidget)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QDate, pyqtSlot, QSize

import os
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

from models.rotation import RotationScheduler
from pages.student_page import StudentPage
from pages.department_page import DepartmentPage

class GanttChartTable(QTableWidget):
    """甘特图表格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # 设置表格样式
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                border: 1px solid #dddddd;
                border-radius: 4px;
                gridline-color: #dddddd;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #66afe9;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dddddd;
                font-weight: bold;
            }
        """)
        
        # 设置一些颜色映射，用于不同科室显示不同颜色
        self.specialty_colors = {}
        self.color_index = 0
        self.base_colors = [
            "#FF9AA2", "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
            "#C7CEEA", "#B5D8EB", "#D0B8EA", "#FFC6FF", "#BDB2FF",
            "#A0C4FF", "#9BF6FF", "#CAFFBF", "#FDFFB6", "#FFD6A5"
        ]
        
    def _get_specialty_color(self, specialty):
        """获取科室专业对应的颜色"""
        if specialty not in self.specialty_colors:
            self.specialty_colors[specialty] = self.base_colors[self.color_index % len(self.base_colors)]
            self.color_index += 1
        return self.specialty_colors[specialty]
        
    def sizeHint(self):
        """提供表格的建议大小"""
        width = self.horizontalHeader().length() + self.verticalHeader().width() + 50  # 额外空间用于滚动条
        height = self.verticalHeader().length() + self.horizontalHeader().height() + 50
        return QSize(width, height)


class DepartmentMonthTable(QTableWidget):
    """科室-月份人数统计表格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # 设置表格样式
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                border: 1px solid #dddddd;
                border-radius: 4px;
                gridline-color: #dddddd;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #66afe9;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dddddd;
                font-weight: bold;
            }
        """)
        
    def sizeHint(self):
        """提供表格的建议大小"""
        width = self.horizontalHeader().length() + self.verticalHeader().width() + 50
        height = self.verticalHeader().length() + self.horizontalHeader().height() + 50
        return QSize(width, height)


class RotationPage(QWidget):
    def __init__(self, student_page: StudentPage, department_page: DepartmentPage):
        super().__init__()
        
        # 保存页面引用
        self.student_page = student_page
        self.department_page = department_page
        
        # 连接信号
        self.student_page.student_data_changed.connect(self._on_data_changed)
        self.department_page.department_data_changed.connect(self._on_data_changed)
        
        # 创建调度器
        self.scheduler = None
        
        # 设置UI
        self._setup_ui()
        
    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === 1. 轮转设置区域 ===
        settings_group = QGroupBox("轮转排期设置")
        settings_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        settings_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f5;
                border: 1px solid #dcdcdc;
                border-radius: 6px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #f5f5f5;
            }
        """)
        
        # 使用网格布局代替水平布局，以保持与其他页面的一致性
        settings_layout = QGridLayout(settings_group)
        settings_layout.setVerticalSpacing(10)
        settings_layout.setHorizontalSpacing(15)
        
        # 创建标签样式
        label_style = """
            QLabel {
                font-weight: bold;
                color: #444444;
            }
        """
        
        # 创建输入控件样式
        input_style = """
            QLineEdit, QComboBox, QDateEdit {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                color: #333333;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #66afe9;
                outline: 0;
                box-shadow: 0 0 8px rgba(102, 175, 233, 0.6);
            }
            QComboBox::drop-down, QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #cccccc;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #66afe9;
                selection-color: white;
            }
        """
        
        # 年级选择
        grade_label = QLabel("年级:")
        grade_label.setStyleSheet(label_style)
        settings_layout.addWidget(grade_label, 0, 0)
        
        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(input_style)
        self.grade_combo.addItems(["2023级", "2024级", "2025级", "2026级", "2027级", "2028级"])
        settings_layout.addWidget(self.grade_combo, 0, 1)
        
        # 开始日期
        date_label = QLabel("开始日期:")
        date_label.setStyleSheet(label_style)
        settings_layout.addWidget(date_label, 0, 2)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setStyleSheet(input_style)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-QDate.currentDate().month() % 12 + 1))  # 设为当年9月1日
        settings_layout.addWidget(self.start_date_edit, 0, 3)
        
        # 按钮样式
        button_style = """
            QPushButton {
                padding: 4px 12px;
                font-weight: bold;
                border-radius: 3px;
                min-width: 80px;
                min-height: 24px;
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
                border: 1px solid #dddddd;
            }
        """
        
        # 生成排期按钮
        self.generate_button = QPushButton("生成排期")
        self.generate_button.setStyleSheet(button_style)
        self.generate_button.clicked.connect(self._generate_schedule)
        settings_layout.addWidget(self.generate_button, 0, 4)
        
        # 导出Excel按钮
        self.export_button = QPushButton("导出Excel")
        self.export_button.setStyleSheet(button_style)
        self.export_button.clicked.connect(self._export_excel)
        self.export_button.setEnabled(False)
        settings_layout.addWidget(self.export_button, 0, 5)
        
        # 添加一个弹性空间
        settings_layout.setColumnStretch(6, 1)
        
        main_layout.addWidget(settings_group)
        
        # === 2. 创建标签页容器 ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { /* 标签页内容区域 */
                border: 1px solid #dddddd;
                background: white;
                border-radius: 3px;
            }
            QTabBar::tab { /* 标签页标签 */
                background: #f0f0f0;
                border: 1px solid #dddddd;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { /* 选中的标签页 */
                background: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)
        
        # === 3. 学生排期表格页 ===
        student_schedule_page = QWidget()
        student_layout = QVBoxLayout(student_schedule_page)
        
        self.schedule_table = GanttChartTable()
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 创建滚动区域包装表格
        student_scroll_area = QScrollArea()
        student_scroll_area.setWidgetResizable(True)
        student_scroll_area.setWidget(self.schedule_table)
        student_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                height: 15px;
            }
            QScrollBar:vertical {
                width: 15px;
            }
            QScrollBar::handle {
                background: #bbbbbb;
                border-radius: 4px;
            }
            QScrollBar::handle:hover {
                background: #999999;
            }
        """)
        
        student_layout.addWidget(student_scroll_area)
        
        # === 4. 科室月份统计表格页 ===
        dept_month_page = QWidget()
        dept_layout = QVBoxLayout(dept_month_page)
        
        self.dept_month_table = DepartmentMonthTable()
        self.dept_month_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 创建滚动区域包装表格
        dept_scroll_area = QScrollArea()
        dept_scroll_area.setWidgetResizable(True)
        dept_scroll_area.setWidget(self.dept_month_table)
        dept_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                height: 15px;
            }
            QScrollBar:vertical {
                width: 15px;
            }
            QScrollBar::handle {
                background: #bbbbbb;
                border-radius: 4px;
            }
            QScrollBar::handle:hover {
                background: #999999;
            }
        """)
        
        dept_layout.addWidget(dept_scroll_area)
        
        # 添加标签页
        self.tab_widget.addTab(student_schedule_page, "学生排期表")
        self.tab_widget.addTab(dept_month_page, "科室人数统计")
        
        main_layout.addWidget(self.tab_widget)
        
        # 设置标签页占据更多空间
        main_layout.setStretch(0, 1)  # 设置区域占比较小
        main_layout.setStretch(1, 4)  # 标签页区域占比较大
    
    def _calculate_base_months(self, grade):
        """根据科室配置计算总轮转月数"""
        department_manager = self.department_page.get_department_manager()
        departments = department_manager.get_departments()
        
        # 默认基础月数为0个月
        default_months = 0
        
        if not departments:
            return default_months
            
        # 计算所有科室的总轮转月数
        total_months = 0
        calculated_specialties = set()
        for dept in departments:
            # 获取科室总月数
            if hasattr(dept, 'get_total_months'):
                # 如果已经遍历过科室的专业，不再计算
                if dept.specialty not in calculated_specialties:
                    total_months += dept.get_total_months()
                    calculated_specialties.add(dept.specialty)
        
        return int(total_months)
    
    def _generate_schedule(self):
        """生成排期"""
        try:
            # 获取参数
            grade = self.grade_combo.currentText()
            start_date = self.start_date_edit.date().toPyDate()
            
            # 计算基础轮转月数
            months = self._calculate_base_months(grade)
            
            # 创建调度器
            student_manager = self.student_page.get_student_manager()
            department_manager = self.department_page.get_department_manager()
            
            if not student_manager.get_students():
                QMessageBox.warning(self, "提示", "没有学生数据，请先在学生录入页面添加学生")
                return
                
            if not department_manager.get_departments():
                QMessageBox.warning(self, "提示", "没有科室数据，请先在科室配置页面添加科室")
                return
            
            # 显示正在生成
           # QMessageBox.information(self, "提示", f"正在生成{months}个月的排期，可能需要等待几秒钟...")
            
            # 创建调度器并生成排期
            self.scheduler = RotationScheduler(student_manager, department_manager)
            self.scheduler.generate_schedule(start_date, grade, months)
            
            # 显示排期结果
            self._display_schedule(grade)
            self._display_dept_month_stats(grade)
            
            # 启用导出按钮
            self.export_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成排期时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_schedule(self, grade):
        """显示学生排期表"""
        try:
            if not self.scheduler:
                return
                
            # 筛选指定年级的学生
            student_manager = self.student_page.get_student_manager()
            students = [s for s in student_manager.get_students() if s.grade == grade]
            
            if not students or not self.scheduler.schedule:
                QMessageBox.warning(self, "提示", f"没有{grade}的学生数据或排期结果")
                return
                
            # 找到所有日期
            all_dates = set()
            for student_name, dates in self.scheduler.schedule.items():
                if student_name in [s.name for s in students]:
                    all_dates.update(dates.keys())
            
            # 排序日期
            sorted_dates = sorted(all_dates)
            
            if not sorted_dates:
                QMessageBox.warning(self, "提示", "没有排期数据")
                return
                
            # 创建DataFrame的数据
            data = {
                "姓名": [],
                "科室": [],
                "年级": [],
                "职位": []
            }
            
            # 添加日期列，并为每个日期创建空列表
            date_columns = []
            for date in sorted_dates:
                display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                if display_date not in data:
                    data[display_date] = []
                    date_columns.append(display_date)
                
            # 填充数据
            for student in students:
                if student.name not in self.scheduler.schedule:
                    continue
                    
                data["姓名"].append(student.name)
                data["科室"].append(student.specialty)
                data["年级"].append(student.grade)
                data["职位"].append(student.position)
                
                for display_date in date_columns:
                    found = False
                    for date in sorted_dates:
                        curr_display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                        if curr_display_date == display_date and date in self.scheduler.schedule[student.name]:
                            data[display_date].append(self.scheduler.schedule[student.name][date])
                            found = True
                            break
                    if not found:
                        data[display_date].append("")
            
            # 检查所有列的长度是否一致
            length_check = len(data["姓名"])
            for key, value in data.items():
                if len(value) != length_check:
                    data[key] = value + [""] * (length_check - len(value))
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                QMessageBox.warning(self, "提示", "没有排期数据")
                return
                
            # 设置表格
            row_count = df.shape[0]
            column_count = df.shape[1]
            
            self.schedule_table.setRowCount(row_count)
            self.schedule_table.setColumnCount(column_count)
            
            # 设置列标题
            self.schedule_table.setHorizontalHeaderLabels(df.columns.tolist())
            
            # 填充数据
            for row in range(row_count):
                for col in range(column_count):
                    value = str(df.iloc[row, col])
                    item = QTableWidgetItem(value)
                    
                    # 如果是轮转科室（日期列）
                    if col >= 4:  # 前4列是姓名、科室、年级、职位
                        # 科室名称
                        dept_name = value
                        
                        # 如果有科室名称，添加背景颜色
                        if dept_name:
                            # 为科室专业设置颜色
                            specialty = None
                            
                            # 尝试从科室名称获取专业
                            for dept in self.department_page.get_department_manager().get_departments():
                                if dept_name.startswith(dept.name):
                                    specialty = dept.specialty
                                    break
                            
                            # 如果找到专业，设置背景色
                            if specialty:
                                color = self.schedule_table._get_specialty_color(specialty)
                                item.setBackground(QColor(color))
                    
                    self.schedule_table.setItem(row, col, item)
            
            # 调整列宽
            # 前4列使用ResizeToContents模式
            for i in range(4):
                self.schedule_table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.ResizeToContents)
            
            # 获取前4列已使用的宽度
            used_width = 0
            for i in range(4):
                used_width += self.schedule_table.columnWidth(i)
            
            # 计算平均每个日期列的宽度（最小60像素）
            date_columns_count = column_count - 4
            if date_columns_count > 0:
                available_width = max(self.width() - used_width - 50, date_columns_count * 60)  # 50为滚动条和边距
                date_column_width = max(int(available_width / date_columns_count), 60)
                
                # 设置日期列为固定宽度
                for col in range(4, column_count):
                    self.schedule_table.setColumnWidth(col, date_column_width)
            
            # 设置表格可以水平滚动
            self.schedule_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # 调整表格大小以适应内容
            self.schedule_table.resizeRowsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示排期时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_dept_month_stats(self, grade):
        """显示科室-月份人数统计表"""
        try:
            if not self.scheduler or not self.scheduler.schedule:
                return
                
            # 筛选指定年级的学生
            student_manager = self.student_page.get_student_manager()
            department_manager = self.department_page.get_department_manager()
            students = [s for s in student_manager.get_students() if s.grade == grade]
            
            if not students:
                return
                
            # 找到所有日期和科室
            all_dates = set()
            all_departments = set()
            for student_name, dates in self.scheduler.schedule.items():
                if student_name in [s.name for s in students]:
                    all_dates.update(dates.keys())
                    for date, dept in dates.items():
                        if dept:  # 确保科室名不为空
                            all_departments.add(dept)
            
            # 排序日期和科室
            sorted_dates = sorted(all_dates)
            sorted_departments = sorted(all_departments)
            
            if not sorted_dates or not sorted_departments:
                return
                
            # 创建月份列表（YYYY-MM格式）
            months = set()
            for date in sorted_dates:
                month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                months.add(month)
            sorted_months = sorted(months)
            
            # 初始化科室-月份人数统计
            dept_month_count = defaultdict(lambda: defaultdict(int))
            
            # 计算每个科室每个月的人数
            for student_name, dates in self.scheduler.schedule.items():
                if student_name in [s.name for s in students]:
                    for date, dept in dates.items():
                        if dept:  # 确保科室名不为空
                            month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                            dept_month_count[dept][month] += 1
            
            # 找出最大人数，用于颜色梯度计算
            max_count = 1
            for dept, months_data in dept_month_count.items():
                for month, count in months_data.items():
                    max_count = max(max_count, count)
            
            # 设置表格
            self.dept_month_table.setRowCount(len(sorted_departments))
            self.dept_month_table.setColumnCount(len(sorted_months))
            
            # 设置科室名称为垂直表头
            self.dept_month_table.setVerticalHeaderLabels(sorted_departments)
            
            # 设置水平表头（月份）
            self.dept_month_table.setHorizontalHeaderLabels(sorted_months)
            
            # 颜色分界阈值
            threshold = 3
            
            # 定义颜色函数：人数≤3使用绿色系，>3使用橙色到红色系
            def get_color_for_count(count):
                if count == 0:
                    return QColor(255, 255, 255)  # 白色(无人)
                
                # 返回颜色和是否需要使用白色文字
                if count <= threshold:
                    # 绿色系 - 从浅到深 (较少人数)
                    # 255/255/255 到 120/255/120
                    intensity = count / threshold  # 0到1之间
                    r = int(255 - 135 * intensity)
                    g = 255
                    b = int(255 - 135 * intensity)
                    return QColor(r, g, b), False  # 不需要白色文字
                else:
                    # 橙色到红色系 - 从浅到深 (较多人数)
                    intensity = min((count - threshold) / (max_count - threshold), 1.0) if max_count > threshold else 0
                    need_white_text = intensity > 0.3  # 当颜色较深时需要白色文字
                    
                    if intensity < 0.5:  # 橙色区间
                        # 橙色从浅到深
                        normalized = intensity * 2  # 0到1范围
                        r = 255
                        g = int(255 - 128 * normalized)
                        b = 0
                    else:  # 红色区间
                        # 橙色过渡到红色
                        normalized = (intensity - 0.5) * 2  # 0到1范围
                        r = 255
                        g = int(127 - 127 * normalized)
                        b = 0
                        
                    return QColor(r, g, b), need_white_text
            
            # 填充数据
            for row, dept in enumerate(sorted_departments):
                # 各月份人数
                for col, month in enumerate(sorted_months):
                    count = dept_month_count[dept][month]
                    item = QTableWidgetItem(str(count))
                    
                    # 根据人数设置背景颜色
                    if count > 0:
                        color, need_white_text = get_color_for_count(count)
                        
                        # 设置文本颜色
                        if need_white_text:
                            item.setForeground(QColor(255, 255, 255))  # 白色文字
                        
                        # 设置背景颜色
                        item.setBackground(color)
                    
                    # 居中对齐
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.dept_month_table.setItem(row, col, item)
            
            # 设置垂直表头自适应宽度
            self.dept_month_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            # 确保垂直表头可见
            self.dept_month_table.verticalHeader().setVisible(True)
            
            # 所有列宽都自适应内容
            for i in range(len(sorted_months)):
                self.dept_month_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
            # 适当增加单元格间距
            self.dept_month_table.setStyleSheet(self.dept_month_table.styleSheet() + """
                QTableWidget::item {
                    padding: 8px;
                }
            """)
            
            # 调整水平表头样式，使其更突出
            self.dept_month_table.horizontalHeader().setStyleSheet("""
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 8px;
                    border: 1px solid #cccccc;
                    font-weight: bold;
                }
            """)
            
            # 调整表格大小，使其适应内容
            self.dept_month_table.resizeColumnsToContents()
            self.dept_month_table.resizeRowsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示科室月份统计时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _export_excel(self):
        """导出Excel"""
        if not self.scheduler:
            QMessageBox.warning(self, "提示", "请先生成排期")
            return
            
        # 获取年级
        grade = self.grade_combo.currentText()
        
        # 选择保存路径
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存Excel文件",
            f"{grade}_轮转排期.xlsx",
            "Excel文件 (*.xlsx)",
            options=options
        )
        
        if file_path:
            # 确保文件扩展名为.xlsx
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
                
            # 导出Excel
            try:
                if self.scheduler.export_to_excel(file_path, grade):
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"排期已导出到 {file_path}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "导出失败",
                        "导出Excel失败，请检查文件路径和权限"
                    )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出Excel时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
    
    @pyqtSlot()
    def _on_data_changed(self):
        """数据变化时的处理"""
        # 数据变化后，重置调度器
        self.scheduler = None
        self.export_button.setEnabled(False)
        
        # 清空表格
        self.schedule_table.setRowCount(0)
        self.schedule_table.setColumnCount(0)
        self.dept_month_table.setRowCount(0)
        self.dept_month_table.setColumnCount(0) 