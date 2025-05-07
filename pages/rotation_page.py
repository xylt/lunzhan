from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFileDialog, QMessageBox, QHeaderView, QGroupBox, 
                             QComboBox, QDateEdit, QSpinBox, QScrollArea)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QDate, pyqtSlot, QSize

import os
import pandas as pd
from datetime import datetime

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
        settings_layout = QHBoxLayout(settings_group)
        
        # 年级选择
        settings_layout.addWidget(QLabel("年级:"))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["2023级", "2024级", "2025级"])
        settings_layout.addWidget(self.grade_combo)
        
        # 开始日期
        settings_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-QDate.currentDate().month() % 12 + 1))  # 设为当年9月1日
        settings_layout.addWidget(self.start_date_edit)
        
        # 生成排期按钮
        self.generate_button = QPushButton("生成排期")
        self.generate_button.clicked.connect(self._generate_schedule)
        settings_layout.addWidget(self.generate_button)
        
        # 导出Excel按钮
        self.export_button = QPushButton("导出Excel")
        self.export_button.clicked.connect(self._export_excel)
        self.export_button.setEnabled(False)
        settings_layout.addWidget(self.export_button)
        
        main_layout.addWidget(settings_group)
        
        # === 2. 轮转排期表格 ===
        self.schedule_table = GanttChartTable()
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 创建滚动区域包装表格，确保在窗口变小时可以滚动查看
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.schedule_table)
        
        main_layout.addWidget(scroll_area)
        
        # 设置表格占据更多空间
        main_layout.setStretch(0, 1)  # 设置区域占比较小
        main_layout.setStretch(1, 4)  # 表格区域占比较大
    
    def _calculate_total_months(self, grade):
        """根据科室配置计算总轮转月数"""
        department_manager = self.department_page.get_department_manager()
        departments = department_manager.get_departments()
        
        # 默认总月数为36个月
        default_months = 36
        
        if not departments:
            return default_months
            
        # 计算所有科室的总轮转月数
        total_months = 0
        for dept in departments:
            # 获取科室总月数
            if hasattr(dept, 'get_total_months'):
                total_months += dept.get_total_months()
            else:
                # 兼容旧版本
                if isinstance(dept.months_per_rotation, list):
                    total_months += sum(dept.months_per_rotation)
                else:
                    total_months += dept.months_per_rotation * dept.rotation_times
        
        # 确保总月数在合理范围内
        total_months = max(12, min(48, total_months))
        
        return int(total_months)
    
    def _generate_schedule(self):
        """生成排期"""
        try:
            # 获取参数
            grade = self.grade_combo.currentText()
            start_date = self.start_date_edit.date().toPyDate()
            
            # 计算总轮转月数
            months = self._calculate_total_months(grade)
            
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
            QMessageBox.information(self, "提示", f"正在生成{months}个月的排期，可能需要等待几秒钟...")
            
            # 创建调度器并生成排期
            self.scheduler = RotationScheduler(student_manager, department_manager)
            self.scheduler.generate_schedule(start_date, grade, months)
            
            # 显示排期结果
            self._display_schedule(grade)
            
            # 启用导出按钮
            self.export_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成排期时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_schedule(self, grade):
        """显示排期结果"""
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