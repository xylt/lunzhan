from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QTableWidget, 
                             QTableWidgetItem, QFileDialog, QMessageBox, 
                             QHeaderView, QGroupBox, QGridLayout, QFrame)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal

import os
import sys
from models.student import Student, StudentManager
from models.department import DepartmentManager

class StudentPage(QWidget):
    # 定义信号
    student_data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.student_manager = StudentManager()
        self.department_manager = DepartmentManager()
        
        # 设置UI
        self._setup_ui()
        self._refresh_student_table()
        
    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # === 1. 学生信息输入区域 ===
        input_group = QGroupBox("学生信息录入")
        input_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        input_group.setStyleSheet("""
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
        input_layout = QVBoxLayout(input_group)
        
        # 使用网格布局替代原来的两行水平布局
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)
        
        # 创建标签样式
        label_style = """
            QLabel {
                font-weight: bold;
                color: #444444;
            }
        """
        
        # 创建输入控件样式
        input_style = """
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                color: #333333;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #66afe9;
                outline: 0;
                box-shadow: 0 0 8px rgba(102, 175, 233, 0.6);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #cccccc;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #66afe9;
                selection-color: white;
            }
        """
        
        # 姓名
        name_label = QLabel("姓名:")
        name_label.setStyleSheet(label_style)
        form_layout.addWidget(name_label, 0, 0)
        
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(input_style)
        self.name_input.setPlaceholderText("请输入学生姓名")
        form_layout.addWidget(self.name_input, 0, 1)
        
        # 专业
        spec_label = QLabel("专业:")
        spec_label.setStyleSheet(label_style)
        form_layout.addWidget(spec_label, 0, 2)
        
        self.specialty_combo = QComboBox()
        self.specialty_combo.setStyleSheet(input_style)
        self.specialty_combo.setMinimumWidth(120)
        self._populate_specialty_combo()
        form_layout.addWidget(self.specialty_combo, 0, 3)
        
        # 年级
        grade_label = QLabel("年级:")
        grade_label.setStyleSheet(label_style)
        form_layout.addWidget(grade_label, 0, 4)
        
        self.grade_combo = QComboBox()
        self.grade_combo.setStyleSheet(input_style)
        self.grade_combo.addItems(["2023级", "2024级", "2025级"])
        form_layout.addWidget(self.grade_combo, 0, 5)
        
        # 职位
        pos_label = QLabel("职位:")
        pos_label.setStyleSheet(label_style)
        form_layout.addWidget(pos_label, 0, 6)
        
        self.position_combo = QComboBox()
        self.position_combo.setStyleSheet(input_style)
        self.position_combo.addItems(["研究生", "住院医师", "其他"])
        form_layout.addWidget(self.position_combo, 0, 7)
        
        # 培训方式
        train_label = QLabel("培训方式:")
        train_label.setStyleSheet(label_style)
        form_layout.addWidget(train_label, 0, 8)
        
        self.training_type_combo = QComboBox()
        self.training_type_combo.setStyleSheet(input_style)
        self.training_type_combo.addItems(["专科培训", "社会培训"])
        self.training_type_combo.currentTextChanged.connect(self._on_training_type_changed)
        form_layout.addWidget(self.training_type_combo, 0, 9)
        
        # 自选专业 (社会培训选项)
        self.self_selected_label1 = QLabel("自选专业1:")
        self.self_selected_label1.setStyleSheet(label_style)
        self.self_selected_label1.setVisible(False)
        form_layout.addWidget(self.self_selected_label1, 0, 10)
        
        self.self_selected_combo1 = QComboBox()
        self.self_selected_combo1.setStyleSheet(input_style)
        self.self_selected_combo1.setMinimumWidth(120)
        self.self_selected_combo1.setVisible(False)
        self._populate_specialty_combo(self.self_selected_combo1)
        form_layout.addWidget(self.self_selected_combo1, 0, 11)
        
        self.self_selected_label2 = QLabel("自选专业2:")
        self.self_selected_label2.setStyleSheet(label_style)
        self.self_selected_label2.setVisible(False)
        form_layout.addWidget(self.self_selected_label2, 0, 12)
        
        self.self_selected_combo2 = QComboBox()
        self.self_selected_combo2.setStyleSheet(input_style)
        self.self_selected_combo2.setMinimumWidth(120)
        self.self_selected_combo2.setVisible(False)
        self._populate_specialty_combo(self.self_selected_combo2)
        form_layout.addWidget(self.self_selected_combo2, 0, 13)
        
        input_layout.addLayout(form_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #cccccc;")
        input_layout.addWidget(line)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setSpacing(10)
        
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
        
        # 添加按钮
        self.add_button = QPushButton("添加")
        self.add_button.setStyleSheet(button_style)
        self.add_button.clicked.connect(self._add_student)
        button_layout.addWidget(self.add_button)
        
        # 修改按钮
        self.update_button = QPushButton("修改")
        self.update_button.setStyleSheet(button_style)
        self.update_button.clicked.connect(self._update_student)
        self.update_button.setEnabled(False)
        button_layout.addWidget(self.update_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setStyleSheet(button_style)
        self.delete_button.clicked.connect(self._delete_student)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet(button_style)
        self.cancel_button.clicked.connect(self._cancel_edit)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        # 导入Excel
        self.import_button = QPushButton("导入Excel")
        self.import_button.setStyleSheet(button_style)
        self.import_button.clicked.connect(self._import_excel)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        
        input_layout.addLayout(button_layout)
        
        main_layout.addWidget(input_group)
        
        # === 2. 学生列表 ===
        self.student_table = QTableWidget()
        self.student_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.student_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.student_table.setColumnCount(6)
        self.student_table.setHorizontalHeaderLabels(["姓名", "专业", "年级", "职位", "培训方式", "自选专业"])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.student_table.setStyleSheet("""
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
        self.student_table.setAlternatingRowColors(True)
        self.student_table.clicked.connect(self._on_student_selected)
        
        main_layout.addWidget(self.student_table)
        
        # 保存当前编辑的学生索引
        self.current_edit_index = -1
    
    def _populate_specialty_combo(self, combo=None):
        """填充专业下拉框"""
        if combo is None:
            combo = self.specialty_combo
            
        combo.clear()
        specialties = self.department_manager.get_specialties()
        combo.addItems(specialties)
    
    def _refresh_student_table(self):
        """刷新学生表格"""
        self.student_table.setRowCount(0)
        students = self.student_manager.get_students()
        
        for row, student in enumerate(students):
            self.student_table.insertRow(row)
            self.student_table.setItem(row, 0, QTableWidgetItem(student.name))
            self.student_table.setItem(row, 1, QTableWidgetItem(student.specialty))
            self.student_table.setItem(row, 2, QTableWidgetItem(student.grade))
            self.student_table.setItem(row, 3, QTableWidgetItem(student.position))
            self.student_table.setItem(row, 4, QTableWidgetItem(student.training_type))
            
            # 显示自选专业
            if student.training_type == "社会培训" and student.self_selected_specialties:
                self_selected_text = ", ".join(student.self_selected_specialties)
            else:
                self_selected_text = ""
            self.student_table.setItem(row, 5, QTableWidgetItem(self_selected_text))
    
    def _on_training_type_changed(self, text):
        """培训方式改变事件"""
        is_social = (text == "社会培训")
        
        # 显示或隐藏自选专业
        self.self_selected_label1.setVisible(is_social)
        self.self_selected_combo1.setVisible(is_social)
        self.self_selected_label2.setVisible(is_social)
        self.self_selected_combo2.setVisible(is_social)
    
    def _add_student(self):
        """添加学生"""
        name = self.name_input.text().strip()
        specialty = self.specialty_combo.currentText()
        grade = self.grade_combo.currentText()
        position = self.position_combo.currentText()
        training_type = self.training_type_combo.currentText()
        
        # 验证
        if not name:
            QMessageBox.warning(self, "提示", "请输入学生姓名")
            return
            
        # 获取自选专业
        self_selected_specialties = []
        if training_type == "社会培训":
            spec1 = self.self_selected_combo1.currentText()
            spec2 = self.self_selected_combo2.currentText()
            
            if spec1:
                self_selected_specialties.append(spec1)
            if spec2 and spec2 != spec1:
                self_selected_specialties.append(spec2)
            
            # 验证自选专业数量
            if len(self_selected_specialties) < 2:
                QMessageBox.warning(self, "提示", "社会培训需要选择两个不同的自选专业")
                return
        
        # 创建学生对象
        student = Student(
            name=name,
            specialty=specialty,
            grade=grade,
            position=position,
            training_type=training_type,
            self_selected_specialties=self_selected_specialties
        )
        
        # 添加学生
        self.student_manager.add_student(student)
        
        # 刷新表格
        self._refresh_student_table()
        
        # 清空输入
        self._clear_inputs()
        
        # 发送数据变化信号
        self.student_data_changed.emit()
    
    def _update_student(self):
        """更新学生信息"""
        if self.current_edit_index < 0:
            return
            
        name = self.name_input.text().strip()
        specialty = self.specialty_combo.currentText()
        grade = self.grade_combo.currentText()
        position = self.position_combo.currentText()
        training_type = self.training_type_combo.currentText()
        
        # 验证
        if not name:
            QMessageBox.warning(self, "提示", "请输入学生姓名")
            return
            
        # 获取自选专业
        self_selected_specialties = []
        if training_type == "社会培训":
            spec1 = self.self_selected_combo1.currentText()
            spec2 = self.self_selected_combo2.currentText()
            
            if spec1:
                self_selected_specialties.append(spec1)
            if spec2 and spec2 != spec1:
                self_selected_specialties.append(spec2)
            
            # 验证自选专业数量
            if len(self_selected_specialties) < 2:
                QMessageBox.warning(self, "提示", "社会培训需要选择两个不同的自选专业")
                return
        
        # 创建学生对象
        student = Student(
            name=name,
            specialty=specialty,
            grade=grade,
            position=position,
            training_type=training_type,
            self_selected_specialties=self_selected_specialties
        )
        
        # 更新学生
        self.student_manager.update_student(self.current_edit_index, student)
        
        # 刷新表格
        self._refresh_student_table()
        
        # 清空输入
        self._clear_inputs()
        
        # 重置按钮状态
        self._reset_button_states()
        
        # 发送数据变化信号
        self.student_data_changed.emit()
    
    def _delete_student(self):
        """删除学生"""
        if self.current_edit_index < 0:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个学生吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除学生
            self.student_manager.remove_student(self.current_edit_index)
            
            # 刷新表格
            self._refresh_student_table()
            
            # 清空输入
            self._clear_inputs()
            
            # 重置按钮状态
            self._reset_button_states()
            
            # 发送数据变化信号
            self.student_data_changed.emit()
    
    def _cancel_edit(self):
        """取消编辑"""
        self._clear_inputs()
        self._reset_button_states()
    
    def _import_excel(self):
        """导入Excel文件"""
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls)",
            options=options
        )
        
        if file_path:
            # 导入Excel
            count = self.student_manager.import_from_excel(file_path)
            
            if count > 0:
                QMessageBox.information(
                    self,
                    "导入成功",
                    f"成功导入{count}名学生"
                )
                
                # 刷新表格
                self._refresh_student_table()
                
                # 发送数据变化信号
                self.student_data_changed.emit()
            else:
                QMessageBox.warning(
                    self,
                    "导入失败",
                    "未能导入任何学生，请检查Excel文件格式"
                )
    
    def _on_student_selected(self):
        """学生选择事件"""
        selected_rows = self.student_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        self.current_edit_index = row
        
        # 获取学生信息
        students = self.student_manager.get_students()
        student = students[row]
        
        # 填充输入框
        self.name_input.setText(student.name)
        
        # 设置下拉框
        index = self.specialty_combo.findText(student.specialty)
        if index >= 0:
            self.specialty_combo.setCurrentIndex(index)
        
        index = self.grade_combo.findText(student.grade)
        if index >= 0:
            self.grade_combo.setCurrentIndex(index)
        
        index = self.position_combo.findText(student.position)
        if index >= 0:
            self.position_combo.setCurrentIndex(index)
        
        index = self.training_type_combo.findText(student.training_type)
        if index >= 0:
            self.training_type_combo.setCurrentIndex(index)
        
        # 设置自选专业
        if student.training_type == "社会培训" and len(student.self_selected_specialties) >= 2:
            index1 = self.self_selected_combo1.findText(student.self_selected_specialties[0])
            if index1 >= 0:
                self.self_selected_combo1.setCurrentIndex(index1)
            
            index2 = self.self_selected_combo2.findText(student.self_selected_specialties[1])
            if index2 >= 0:
                self.self_selected_combo2.setCurrentIndex(index2)
        
        # 启用按钮
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.add_button.setEnabled(False)
    
    def _clear_inputs(self):
        """清空输入"""
        self.name_input.clear()
        self.specialty_combo.setCurrentIndex(0)
        self.grade_combo.setCurrentIndex(0)
        self.position_combo.setCurrentIndex(0)
        self.training_type_combo.setCurrentIndex(0)
        self.self_selected_combo1.setCurrentIndex(0)
        self.self_selected_combo2.setCurrentIndex(0)
        self.current_edit_index = -1
    
    def _reset_button_states(self):
        """重置按钮状态"""
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.add_button.setEnabled(True)
    
    def get_student_manager(self):
        """获取学生管理器"""
        return self.student_manager 