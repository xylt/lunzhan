from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, 
                             QGroupBox, QDoubleSpinBox, QCheckBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from models.department import Department, DepartmentManager

class DepartmentPage(QWidget):
    # 定义信号
    department_data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.department_manager = DepartmentManager()
        
        # 设置UI
        self._setup_ui()
        self._refresh_department_table()
        
    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # === 1. 科室信息输入区域 ===
        input_group = QGroupBox("科室信息配置")
        input_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        input_layout = QVBoxLayout(input_group)
        
        # 表单布局 - 第一行
        form_layout1 = QHBoxLayout()
        
        # 科室名称
        form_layout1.addWidget(QLabel("科室名称:"))
        self.name_input = QLineEdit()
        form_layout1.addWidget(self.name_input)
        
        # 科室专业
        form_layout1.addWidget(QLabel("科室专业:"))
        self.specialty_input = QLineEdit()
        form_layout1.addWidget(self.specialty_input)
        
        input_layout.addLayout(form_layout1)
        
        # 表单布局 - 第二行
        form_layout2 = QHBoxLayout()
        
        # 轮转次数
        form_layout2.addWidget(QLabel("轮转次数:"))
        self.rotation_times_spin = QDoubleSpinBox()
        self.rotation_times_spin.setMinimum(1)
        self.rotation_times_spin.setMaximum(5)
        self.rotation_times_spin.setDecimals(0)
        self.rotation_times_spin.setValue(1)
        form_layout2.addWidget(self.rotation_times_spin)
        
        # 每次轮转月数
        form_layout2.addWidget(QLabel("轮转月数:"))
        self.months_spin = QDoubleSpinBox()
        self.months_spin.setMinimum(0.5)
        self.months_spin.setMaximum(12)
        self.months_spin.setSingleStep(0.5)
        self.months_spin.setValue(1)
        form_layout2.addWidget(self.months_spin)
        
        # 后期轮转
        self.later_rotation_check = QCheckBox("后期轮转（第一年后）")
        form_layout2.addWidget(self.later_rotation_check)
        
        input_layout.addLayout(form_layout2)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加按钮
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self._add_department)
        button_layout.addWidget(self.add_button)
        
        # 修改按钮
        self.update_button = QPushButton("修改")
        self.update_button.clicked.connect(self._update_department)
        self.update_button.setEnabled(False)
        button_layout.addWidget(self.update_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self._delete_department)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self._cancel_edit)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        input_layout.addLayout(button_layout)
        
        main_layout.addWidget(input_group)
        
        # === 2. 科室列表 ===
        self.department_table = QTableWidget()
        self.department_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.department_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.department_table.setColumnCount(5)
        self.department_table.setHorizontalHeaderLabels([
            "科室名称", "科室专业", "轮转次数", "每次轮转月数", "后期轮转"
        ])
        self.department_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.department_table.clicked.connect(self._on_department_selected)
        
        main_layout.addWidget(self.department_table)
        
        # 保存当前编辑的科室索引
        self.current_edit_index = -1
    
    def _refresh_department_table(self):
        """刷新科室表格"""
        self.department_table.setRowCount(0)
        departments = self.department_manager.get_departments()
        
        for row, department in enumerate(departments):
            self.department_table.insertRow(row)
            self.department_table.setItem(row, 0, QTableWidgetItem(department.name))
            self.department_table.setItem(row, 1, QTableWidgetItem(department.specialty))
            self.department_table.setItem(row, 2, QTableWidgetItem(str(department.rotation_times)))
            self.department_table.setItem(row, 3, QTableWidgetItem(str(department.months_per_rotation)))
            
            # 后期轮转显示为"是"或"否"
            is_later = "是" if department.is_later_rotation else "否"
            self.department_table.setItem(row, 4, QTableWidgetItem(is_later))
    
    def _add_department(self):
        """添加科室"""
        name = self.name_input.text().strip()
        specialty = self.specialty_input.text().strip()
        rotation_times = int(self.rotation_times_spin.value())
        months = float(self.months_spin.value())
        is_later_rotation = self.later_rotation_check.isChecked()
        
        # 验证
        if not name or not specialty:
            QMessageBox.warning(self, "提示", "请输入科室名称和专业")
            return
            
        # 检查是否已存在同名科室
        for dept in self.department_manager.get_departments():
            if dept.name == name:
                QMessageBox.warning(self, "提示", f"科室 '{name}' 已存在")
                return
        
        # 创建科室对象
        department = Department(
            name=name,
            specialty=specialty,
            rotation_times=rotation_times,
            months_per_rotation=months,
            is_later_rotation=is_later_rotation
        )
        
        # 添加科室
        self.department_manager.add_department(department)
        
        # 刷新表格
        self._refresh_department_table()
        
        # 清空输入
        self._clear_inputs()
        
        # 发送数据变化信号
        self.department_data_changed.emit()
    
    def _update_department(self):
        """更新科室信息"""
        if self.current_edit_index < 0:
            return
            
        name = self.name_input.text().strip()
        specialty = self.specialty_input.text().strip()
        rotation_times = int(self.rotation_times_spin.value())
        months = float(self.months_spin.value())
        is_later_rotation = self.later_rotation_check.isChecked()
        
        # 验证
        if not name or not specialty:
            QMessageBox.warning(self, "提示", "请输入科室名称和专业")
            return
            
        # 检查是否已存在同名科室（排除当前编辑的科室）
        departments = self.department_manager.get_departments()
        for i, dept in enumerate(departments):
            if i != self.current_edit_index and dept.name == name:
                QMessageBox.warning(self, "提示", f"科室 '{name}' 已存在")
                return
        
        # 创建科室对象
        department = Department(
            name=name,
            specialty=specialty,
            rotation_times=rotation_times,
            months_per_rotation=months,
            is_later_rotation=is_later_rotation
        )
        
        # 更新科室
        self.department_manager.update_department(self.current_edit_index, department)
        
        # 刷新表格
        self._refresh_department_table()
        
        # 清空输入
        self._clear_inputs()
        
        # 重置按钮状态
        self._reset_button_states()
        
        # 发送数据变化信号
        self.department_data_changed.emit()
    
    def _delete_department(self):
        """删除科室"""
        if self.current_edit_index < 0:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个科室吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除科室
            self.department_manager.remove_department(self.current_edit_index)
            
            # 刷新表格
            self._refresh_department_table()
            
            # 清空输入
            self._clear_inputs()
            
            # 重置按钮状态
            self._reset_button_states()
            
            # 发送数据变化信号
            self.department_data_changed.emit()
    
    def _cancel_edit(self):
        """取消编辑"""
        self._clear_inputs()
        self._reset_button_states()
    
    def _on_department_selected(self):
        """科室选择事件"""
        selected_rows = self.department_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        self.current_edit_index = row
        
        # 获取科室信息
        departments = self.department_manager.get_departments()
        department = departments[row]
        
        # 填充输入框
        self.name_input.setText(department.name)
        self.specialty_input.setText(department.specialty)
        self.rotation_times_spin.setValue(department.rotation_times)
        self.months_spin.setValue(department.months_per_rotation)
        self.later_rotation_check.setChecked(department.is_later_rotation)
        
        # 启用按钮
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.add_button.setEnabled(False)
    
    def _clear_inputs(self):
        """清空输入"""
        self.name_input.clear()
        self.specialty_input.clear()
        self.rotation_times_spin.setValue(1)
        self.months_spin.setValue(1)
        self.later_rotation_check.setChecked(False)
        self.current_edit_index = -1
    
    def _reset_button_states(self):
        """重置按钮状态"""
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.add_button.setEnabled(True)
    
    def get_department_manager(self):
        """获取科室管理器"""
        return self.department_manager 