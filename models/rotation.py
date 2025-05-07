import json
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Set

from models.student import Student, StudentManager
from models.department import Department, DepartmentManager

class RotationScheduler:
    def __init__(self, student_manager: StudentManager, department_manager: DepartmentManager):
        self.student_manager = student_manager
        self.department_manager = department_manager
        self.schedule = {}  # 保存排期结果，格式：{学生名: {日期: 科室名}}
        self.department_counts = {}  # 二维数组，记录每个科室每个月的人数
        
    def generate_schedule(self, start_date: datetime, grade: str, months: int = 36) -> Dict[str, Dict[str, str]]:
        """生成轮转排期"""
        students = [s for s in self.student_manager.get_students() if s.grade == grade]
        departments = self.department_manager.get_departments()
        
        if not students or not departments:
            return {}
            
        # 初始化科室月度人数统计
        self._initialize_department_counts(departments, start_date, months)
        
        # 为每个学生生成轮转安排
        for student in students:
            self._schedule_student(student, start_date, months)
            
        return self.schedule
    
    def _initialize_department_counts(self, departments: List[Department], start_date: datetime, months: int):
        """初始化科室月度人数统计"""
        self.department_counts = {}
        
        # 为每个科室创建月度计数器
        for dept in departments:
            self.department_counts[dept.name] = {}
            for i in range(months):
                current_date = start_date + timedelta(days=30*i)
                date_key = current_date.strftime("%Y-%m-%d")
                self.department_counts[dept.name][date_key] = 0
                
    def _schedule_student(self, student: Student, start_date: datetime, total_months: int):
        """为单个学生安排轮转"""
        # 初始化学生的排期
        self.schedule[student.name] = {}
        
        # 构建需要轮转的科室列表
        rotation_departments = self._build_rotation_departments(student)
        
        # 分类科室：常规科室和后期科室
        regular_departments = []
        later_departments = []
        
        for dept_info in rotation_departments:
            if dept_info["department"].is_later_rotation:
                later_departments.append(dept_info)
            else:
                regular_departments.append(dept_info)
        
        # 设置第一年日期
        first_year_end = start_date + timedelta(days=365)
        first_year_months = min(12, total_months)
        
        # 计算每个科室第一轮和第二轮的月数
        # 对于轮转次数>1的科室，单独处理
        first_rotation_departments = []
        second_rotation_departments = []
        
        for dept_info in regular_departments:
            dept = dept_info["department"]
            if dept.rotation_times > 1:
                # 第一轮
                first_month = dept_info["months"][0] if len(dept_info["months"]) > 0 else dept_info["months"][0]
                first_rotation_departments.append({
                    "department": dept,
                    "months": first_month,
                    "rotation_order": 1
                })
                
                # 第二轮
                second_month = dept_info["months"][1] if len(dept_info["months"]) > 1 else dept_info["months"][0]
                second_rotation_departments.append({
                    "department": dept,
                    "months": second_month,
                    "rotation_order": 2
                })
            else:
                first_month = dept_info["months"][0] if len(dept_info["months"]) > 0 else 1.0
                first_rotation_departments.append({
                    "department": dept_info["department"],
                    "months": first_month,
                    "rotation_order": 1
                })
        
        # 随机打乱科室顺序，但保持相同科室不连续
        random.shuffle(first_rotation_departments)
        
        # 安排第一年轮转
        current_date = start_date
        scheduled_departments = set()  # 记录学生已经轮转过的科室专业
        
        # 先排第一轮轮转
        for dept_info in first_rotation_departments:
            dept = dept_info["department"]
            months = dept_info["months"]
            
            # 如果这个科室专业已经轮转过，跳过
            if dept.specialty in scheduled_departments:
                continue
                
            # 安排这个科室
            end_date = self._assign_department(student.name, dept, current_date, months)
            scheduled_departments.add(dept.specialty)
            
            # 更新当前日期
            current_date = end_date
            
            # 如果已经超过第一年，停止
            if current_date >= first_year_end:
                break
        
        # 安排第二轮和后期轮转
        remaining_departments = second_rotation_departments + later_departments
        random.shuffle(remaining_departments)
        
        # 计算剩余月数
        remaining_months = total_months - (current_date.year - start_date.year) * 12 - \
                          (current_date.month - start_date.month)
        
        if remaining_months > 0 and remaining_departments:
            for dept_info in remaining_departments:
                dept = dept_info["department"]
                months = dept_info["months"]
                
                # 对于后期轮转，确保日期至少在开始日期一年后
                if dept.is_later_rotation and current_date < first_year_end:
                    current_date = first_year_end
                
                # 安排这个科室
                end_date = self._assign_department(student.name, dept, current_date, months)
                
                # 更新当前日期
                current_date = end_date
                
                # 如果已经超过总月数，停止
                if current_date >= start_date + timedelta(days=30*total_months):
                    break
    
    def _build_rotation_departments(self, student: Student) -> List[Dict]:
        """构建学生需要轮转的科室列表"""
        rotation_departments = []
        all_departments = self.department_manager.get_departments()
        
        # 添加所有科室
        for dept in all_departments:
            rotation_departments.append({
                "department": dept,
                "months": dept.months_per_rotation.copy() if isinstance(dept.months_per_rotation, list) else [dept.months_per_rotation]
            })
        
        # 处理学生自己的专业（额外多轮转两个月）
        student_specialty_departments = self.department_manager.get_departments_by_specialty(student.specialty)
        for dept in student_specialty_departments:
            # 找到该科室，增加额外的两个月轮转
            for dept_info in rotation_departments:
                if dept_info["department"].name == dept.name:
                    # 在第一次轮转的月数上增加2个月
                    if dept_info["months"] and len(dept_info["months"]) > 0:
                        dept_info["months"][0] += 2
                    break
        
        # 处理社会培训的自选专业（每个专业额外轮转一个月）
        if student.training_type == "社会培训" and student.self_selected_specialties:
            for specialty in student.self_selected_specialties:
                specialty_departments = self.department_manager.get_departments_by_specialty(specialty)
                for dept in specialty_departments:
                    # 找到该科室，增加额外的一个月轮转
                    for dept_info in rotation_departments:
                        if dept_info["department"].name == dept.name:
                            # 在第一次轮转的月数上增加1个月
                            if dept_info["months"] and len(dept_info["months"]) > 0:
                                dept_info["months"][0] += 1
                            break
        
        return rotation_departments
    
    def _assign_department(self, student_name: str, department: Department, start_date: datetime, months: float) -> datetime:
        """为学生安排指定科室的轮转，返回结束日期"""
        current_date = start_date
        
        # 确保months是浮点数而不是列表
        if isinstance(months, list):
            if len(months) > 0:
                remaining_months = float(months[0])
            else:
                remaining_months = 1.0
        else:
            remaining_months = float(months)
        
        while remaining_months > 0:
            date_key = current_date.strftime("%Y-%m-%d")
            
            # 如果当前月份超出了跟踪范围，退出
            if date_key not in self.department_counts.get(department.name, {}):
                break
                
            # 计算本月分配月数
            if remaining_months >= 1:
                month_allocation = 1
            else:
                month_allocation = remaining_months
                
            # 检查当月该科室人数
            min_count = float('inf')
            for dept_name in self.department_counts:
                if date_key in self.department_counts[dept_name]:
                    min_count = min(min_count, self.department_counts[dept_name][date_key])
            
            # 如果该科室人数比最少的科室多2人以上，尝试下个月
            if self.department_counts[department.name][date_key] > min_count + 2:
                # 尝试下个月
                current_date = current_date + timedelta(days=30)
                continue
            
            # 安排本月轮转
            self.schedule[student_name][date_key] = department.name
            self.department_counts[department.name][date_key] += 1
            
            # 更新剩余月数和当前日期
            remaining_months -= month_allocation
            current_date = current_date + timedelta(days=30*month_allocation)
            
            # 特殊处理：心内科第二次轮转后接心电图
            if department.name in ["心内一科", "心内二科"] and remaining_months == 0:
                # 检查心内科是否设置了轮转月数为1.5（表示第二次轮转后需要接心电图）
                second_rotation_months = None
                if len(department.months_per_rotation) > 1:
                    second_rotation_months = department.months_per_rotation[1]
                
                # 判断当前轮转月数是否符合心电图轮转条件
                current_months = float(months) if not isinstance(months, list) else (months[0] if len(months) > 0 else 0)
                
                # 如果是第二次轮转且月数是1.5，自动安排心电图
                if second_rotation_months == 1.5 and current_months == 1.5:
                    # 安排心电图室0.5个月
                    ekg_dept = None
                    for dept in self.department_manager.get_departments():
                        if dept.name == "心电图室":
                            ekg_dept = dept
                            break
                    
                    if ekg_dept:
                        date_key = current_date.strftime("%Y-%m-%d")
                        
                        # 在当前日期安排心电图
                        if date_key in self.schedule[student_name]:
                            # 已经有科室，合并显示
                            self.schedule[student_name][date_key] = f"{self.schedule[student_name][date_key]}/心电图室"
                        else:
                            self.schedule[student_name][date_key] = "心电图室"
                        
                        # 更新计数
                        if date_key in self.department_counts.get("心电图室", {}):
                            self.department_counts["心电图室"][date_key] += 1
                            
        # 返回当前日期作为结束日期
        return current_date
    
    def export_to_excel(self, file_path: str, grade: str):
        """将排期导出到Excel"""
        # 筛选指定年级的学生
        students = [s for s in self.student_manager.get_students() if s.grade == grade]
        
        if not students or not self.schedule:
            return False
            
        # 找到所有日期
        all_dates = set()
        for student_name, dates in self.schedule.items():
            all_dates.update(dates.keys())
        
        # 排序日期
        sorted_dates = sorted(all_dates)
        
        # 创建DataFrame
        data = {
            "姓名": [],
            "科室": [],
            "年级": [],
            "职位": []
        }
        
        # 添加日期列
        for date in sorted_dates:
            data[date] = []
            
        # 填充数据
        for student in students:
            if student.name not in self.schedule:
                continue
                
            data["姓名"].append(student.name)
            data["科室"].append(student.specialty)
            data["年级"].append(student.grade)
            data["职位"].append(student.position)
            
            for date in sorted_dates:
                if date in self.schedule[student.name]:
                    data[date].append(self.schedule[student.name][date])
                else:
                    data[date].append("")
        
        # 创建DataFrame并导出
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        return True
    
    def get_schedule_for_display(self, grade: str) -> pd.DataFrame:
        """获取用于显示的排期数据"""
        # 筛选指定年级的学生
        students = [s for s in self.student_manager.get_students() if s.grade == grade]
        
        if not students or not self.schedule:
            return pd.DataFrame()
            
        # 找到所有日期
        all_dates = set()
        for student_name, dates in self.schedule.items():
            if student_name in [s.name for s in students]:
                all_dates.update(dates.keys())
        
        # 排序日期
        sorted_dates = sorted(all_dates)
        
        if not sorted_dates:
            return pd.DataFrame()
            
        # 创建DataFrame的数据
        data = {
            "姓名": [],
            "科室": [],
            "年级": [],
            "职位": []
        }
        
        # 添加日期列，并为每个日期创建空列表
        for date in sorted_dates:
            display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
            data[display_date] = []
            
        # 填充数据
        for student in students:
            if student.name not in self.schedule:
                continue
                
            data["姓名"].append(student.name)
            data["科室"].append(student.specialty)
            data["年级"].append(student.grade)
            data["职位"].append(student.position)
            
            for date in sorted_dates:
                display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                if date in self.schedule[student.name]:
                    data[display_date].append(self.schedule[student.name][date])
                else:
                    data[display_date].append("")
        
        # 检查所有列的长度是否一致
        length_check = len(data["姓名"])
        for key, value in data.items():
            if len(value) != length_check:
                data[key] = value + [""] * (length_check - len(value))
        
        return pd.DataFrame(data) 