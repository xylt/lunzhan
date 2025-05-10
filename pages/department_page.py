from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, 
                             QGroupBox, QDoubleSpinBox, QCheckBox, QScrollArea,
                             QGridLayout, QFrame)
from PyQt6.QtGui import QFont, QColor, QPalette
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
        form_layout.setColumnStretch(1, 1)  # 输入框列拉伸
        form_layout.setColumnStretch(3, 1)  # 输入框列拉伸
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)
        
        # 创建标签样式
        label_style = """
            QLabel {
                font-weight: bold;
                color: #444444;
            }
        """
        
        # 创建输入框样式
        input_style = """
            QLineEdit, QComboBox, QCheckBox {
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
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #66afe9;
                selection-color: white;
            }
        """
        
        # 科室名称
        name_label = QLabel("科室名称:")
        name_label.setStyleSheet(label_style)
        form_layout.addWidget(name_label, 0, 0)
        
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(input_style)
        self.name_input.setPlaceholderText("请输入科室名称")
        form_layout.addWidget(self.name_input, 0, 1)
        
        # 科室专业
        spec_label = QLabel("科室专业:")
        spec_label.setStyleSheet(label_style)
        form_layout.addWidget(spec_label, 0, 2)
        
        self.specialty_input = QLineEdit()
        self.specialty_input.setStyleSheet(input_style)
        self.specialty_input.setPlaceholderText("请输入科室专业")
        form_layout.addWidget(self.specialty_input, 0, 3)
        
        # 轮转配置
        rot_label = QLabel("轮转月数:")
        rot_label.setStyleSheet(label_style)
        form_layout.addWidget(rot_label, 0, 4)
        
        self.rotation_config_input = QLineEdit()
        self.rotation_config_input.setStyleSheet(input_style)
        self.rotation_config_input.setToolTip("使用斜杠分隔每次轮转的月数，例如：2.0/1.5")
        self.rotation_config_input.setPlaceholderText("例如: 2.0/1.5")
        form_layout.addWidget(self.rotation_config_input, 0, 5)
        
        # 后期轮转
        self.later_rotation_check = QCheckBox("后期轮转（第一年后）")
        self.later_rotation_check.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #444444;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #66afe9;
                background-color: #66afe9;
                border-radius: 3px;
            }
        """)
        form_layout.addWidget(self.later_rotation_check, 0, 6)
        
        input_layout.addLayout(form_layout)
        
        # 添加说明标签
        hint_label = QLabel("轮转配置格式说明: 直接输入每次轮转的月数，如\"2.0/1.5\"表示需要轮转2次，第一次2个月，第二次1.5个月")
        hint_label.setStyleSheet("color: #888888; font-style: italic; padding: 5px;")
        input_layout.addWidget(hint_label)
        
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
        self.add_button.clicked.connect(self._add_department)
        button_layout.addWidget(self.add_button)
        
        # 修改按钮
        self.update_button = QPushButton("修改")
        self.update_button.setStyleSheet(button_style)
        self.update_button.clicked.connect(self._update_department)
        self.update_button.setEnabled(False)
        button_layout.addWidget(self.update_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setStyleSheet(button_style)
        self.delete_button.clicked.connect(self._delete_department)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet(button_style)
        self.cancel_button.clicked.connect(self._cancel_edit)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        input_layout.addLayout(button_layout)
        
        main_layout.addWidget(input_group)
        
        # === 2. 科室列表 ===
        self.department_table = QTableWidget()
        self.department_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.department_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.department_table.setColumnCount(4)
        self.department_table.setHorizontalHeaderLabels([
            "科室名称", "科室专业", "轮转配置", "后期轮转"
        ])
        self.department_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.department_table.setStyleSheet("""
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
        self.department_table.setAlternatingRowColors(True)
        self.department_table.clicked.connect(self._on_department_selected)
        
        main_layout.addWidget(self.department_table)
        
        # 保存当前编辑的科室索引
        self.current_edit_index = -1
    
    def _parse_rotation_config(self, config_text):
        """解析轮转配置文本，返回(轮转次数, [月数列表])"""
        try:
            # 移除所有空格
            config_text = config_text.strip().replace(" ", "")
            
            if not config_text:
                return None, None
            
            # 新的解析方式：直接按/分割，分隔的数量决定轮转次数
            months_list = []
            if "/" in config_text:
                # 按/分割获取所有月数
                parts = config_text.split("/")
                
                for part in parts:
                    try:
                        months = float(part)
                        if months <= 0:
                            return None, None
                        months_list.append(months)
                    except ValueError:
                        return None, None
            else:
                # 如果没有/，则视为单次轮转
                try:
                    months = float(int(config_text/0.5)*0.5)
                    if months <= 0:
                        return None, None
                    months_list.append(months)
                except ValueError:
                    return None, None
            
            # 轮转次数就是月数列表的长度
            rotation_times = len(months_list)
            
            # 验证轮转次数必须大于0
            if rotation_times <= 0:
                return None, None
            
            return rotation_times, months_list
        except Exception:
            return None, None
    
    def _format_rotation_config(self, rotation_times, months_per_rotation):
        """将轮转次数和月数列表格式化为配置文本"""
        if not rotation_times or not months_per_rotation:
            return ""
        
        # 直接返回月数的字符串，用斜杠分隔
        return "/".join(str(m) for m in months_per_rotation)
        
    def _refresh_department_table(self):
        """刷新科室表格"""
        self.department_table.setRowCount(0)
        departments = self.department_manager.get_departments()
        
        for row, department in enumerate(departments):
            self.department_table.insertRow(row)
            self.department_table.setItem(row, 0, QTableWidgetItem(department.name))
            self.department_table.setItem(row, 1, QTableWidgetItem(department.specialty))
            
            # 显示轮转配置
            config_text = self._format_rotation_config(department.rotation_times, department.months_per_rotation)
            self.department_table.setItem(row, 2, QTableWidgetItem(config_text))
            
            # 后期轮转显示为"是"或"否"
            is_later = "是" if department.is_later_rotation else "否"
            self.department_table.setItem(row, 3, QTableWidgetItem(is_later))
    
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
        config_text = self._format_rotation_config(department.rotation_times, department.months_per_rotation)
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