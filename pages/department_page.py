from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, 
                             QGroupBox, QDoubleSpinBox, QCheckBox, QScrollArea)
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
        
        # 轮转配置 (格式: "2/1.5" 表示两次轮转,分别为2个月和1.5个月)
        form_layout2.addWidget(QLabel("轮转配置(次数/月数):"))
        self.rotation_config_input = QLineEdit()
        self.rotation_config_input.setToolTip("格式: \"2/1.5\" 表示两次轮转,分别为2个月和1.5个月")
        self.rotation_config_input.setPlaceholderText("例如: 2/1.5 或 1/2")
        form_layout2.addWidget(self.rotation_config_input)
        
        # 后期轮转
        self.later_rotation_check = QCheckBox("后期轮转（第一年后）")
        form_layout2.addWidget(self.later_rotation_check)
        
        # 添加到输入布局
        input_layout.addLayout(form_layout2)
        
        # 添加说明标签
        hint_label = QLabel("轮转配置格式说明: 2/1.5 表示需要轮转2次，第一次2个月，第二次1.5个月")
        hint_label.setStyleSheet("color: gray; font-style: italic;")
        input_layout.addWidget(hint_label)
        
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
            "科室名称", "科室专业", "轮转次数", "轮转月数配置", "后期轮转"
        ])
        self.department_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.department_table.clicked.connect(self._on_department_selected)
        
        main_layout.addWidget(self.department_table)
        
        # 保存当前编辑的科室索引
        self.current_edit_index = -1
    
    def _parse_rotation_config(self, config_text):
        """解析轮转配置文本，返回(轮转次数, [月数列表])"""
        try:
            # 移除所有空格
            config_text = config_text.strip().replace(" ", "")
            
            if "/" not in config_text:
                # 如果只有一个数字，解释为一次轮转对应的月数
                try:
                    months = float(config_text)
                    return 1, [months]
                except ValueError:
                    return None, None
            
            # 解析格式为"2/1.5"的情况
            parts = config_text.split("/")
            
            # 尝试将第一部分解析为轮转次数
            try:
                rotation_times = int(parts[0])
            except ValueError:
                return None, None
                
            if rotation_times <= 0:
                return None, None
                
            # 解析后续的月数
            months_per_rotation = []
            for i in range(1, len(parts)):
                try:
                    months = float(parts[i])
                    if months <= 0:
                        return None, None
                    months_per_rotation.append(months)
                except ValueError:
                    return None, None
            
            # 如果没有提供足够的月数，使用最后一个月数填充
            if len(months_per_rotation) < rotation_times:
                last_month = months_per_rotation[-1] if months_per_rotation else 1.0
                while len(months_per_rotation) < rotation_times:
                    months_per_rotation.append(last_month)
            
            # 返回解析结果
            return rotation_times, months_per_rotation
        except Exception:
            return None, None
    
    def _format_rotation_config(self, rotation_times, months_per_rotation):
        """将轮转次数和月数列表格式化为配置文本"""
        if not rotation_times or not months_per_rotation:
            return ""
        
        return f"{rotation_times}/{'/'.join(str(m) for m in months_per_rotation)}"
        
    def _refresh_department_table(self):
        """刷新科室表格"""
        self.department_table.setRowCount(0)
        departments = self.department_manager.get_departments()
        
        for row, department in enumerate(departments):
            self.department_table.insertRow(row)
            self.department_table.setItem(row, 0, QTableWidgetItem(department.name))
            self.department_table.setItem(row, 1, QTableWidgetItem(department.specialty))
            self.department_table.setItem(row, 2, QTableWidgetItem(str(department.rotation_times)))
            
            # 显示每次轮转月数配置，使用简洁格式"2/1.5"表示第一次2个月第二次1.5个月
            months_text = "/".join([str(m) for m in department.months_per_rotation])
            self.department_table.setItem(row, 3, QTableWidgetItem(months_text))
            
            # 后期轮转显示为"是"或"否"
            is_later = "是" if department.is_later_rotation else "否"
            self.department_table.setItem(row, 4, QTableWidgetItem(is_later))
    
    def _add_department(self):
        """添加科室"""
        name = self.name_input.text().strip()
        specialty = self.specialty_input.text().strip()
        rotation_config = self.rotation_config_input.text().strip()
        is_later_rotation = self.later_rotation_check.isChecked()
        
        # 验证基本信息
        if not name or not specialty:
            QMessageBox.warning(self, "提示", "请输入科室名称和专业")
            return
        
        # 检查是否已存在同名科室
        for dept in self.department_manager.get_departments():
            if dept.name == name:
                QMessageBox.warning(self, "提示", f"科室 '{name}' 已存在")
                return
        
        # 解析轮转配置
        rotation_times, months_per_rotation = self._parse_rotation_config(rotation_config)
        if rotation_times is None or months_per_rotation is None:
            QMessageBox.warning(self, "提示", "轮转配置格式错误，请使用如'2/1.5'的格式")
            return
        
        # 创建科室对象
        department = Department(
            name=name,
            specialty=specialty,
            rotation_times=rotation_times,
            months_per_rotation=months_per_rotation,
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
        rotation_config = self.rotation_config_input.text().strip()
        is_later_rotation = self.later_rotation_check.isChecked()
        
        # 验证基本信息
        if not name or not specialty:
            QMessageBox.warning(self, "提示", "请输入科室名称和专业")
            return
            
        # 检查是否已存在同名科室（排除当前编辑的科室）
        departments = self.department_manager.get_departments()
        for i, dept in enumerate(departments):
            if i != self.current_edit_index and dept.name == name:
                QMessageBox.warning(self, "提示", f"科室 '{name}' 已存在")
                return
        
        # 解析轮转配置
        rotation_times, months_per_rotation = self._parse_rotation_config(rotation_config)
        if rotation_times is None or months_per_rotation is None:
            QMessageBox.warning(self, "提示", "轮转配置格式错误，请使用如'2/1.5'的格式")
            return
        
        # 创建科室对象
        department = Department(
            name=name,
            specialty=specialty,
            rotation_times=rotation_times,
            months_per_rotation=months_per_rotation,
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
        
        # 设置轮转配置
        config_text = f"{department.rotation_times}/{'/'.join([str(m) for m in department.months_per_rotation])}"
        self.rotation_config_input.setText(config_text)
        
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
        self.rotation_config_input.clear()
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