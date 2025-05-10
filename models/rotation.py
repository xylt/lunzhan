import json
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any, Tuple, Set

from models.student import Student, StudentManager
from models.department import Department, DepartmentManager

class RotationScheduler:
    def __init__(self, student_manager: StudentManager, department_manager: DepartmentManager):
        self.student_manager = student_manager
        self.department_manager = department_manager
        self.schedule = {}  # 保存排期结果，格式：{学生名: {日期: 科室名}}
        self.department_counts = {}  # 二维数组，记录每个科室每个月的人数
        self.department_total_counts = {}  # 一维数组，记录每个科室的总人数

    def _calculate_base_rotation_months(self) -> int:
        """计算该学生的基础轮转月数"""
        departments = self.department_manager.get_departments()
        total_months = 0
        calculated_specialties = set()
        
        for dept in departments:
            # 获取科室总月数
            if hasattr(dept, 'get_total_months'):
                # 如果已经遍历过科室的专业，不再计算
                if dept.specialty not in calculated_specialties:
                    total_months += dept.get_total_months()
                    calculated_specialties.add(dept.specialty)
        
        return total_months
        
    def _calculate_total_rotation_months(self, student: Student) -> int:
        """计算该学生需要的总轮转月数"""
            
        # 计算所有科室的基础轮转月数
        total_months = 0
        total_months += self._calculate_base_rotation_months()
        
        # 学生自己的专业额外增加2个月
        total_months += 2
        
        # 如果是社会培训，额外增加2个自选专业，每个1个月
        if student.training_type == "社会培训" and student.self_selected_specialties:
            total_months += len(student.self_selected_specialties)
            
        return total_months

    def generate_schedule(self, start_date: datetime, grade: str) -> Dict[str, Dict[str, str]]:
        """生成轮转排期"""
        students = [s for s in self.student_manager.get_students() if s.grade == grade]
        departments = self.department_manager.get_departments()
        
        if not students or not departments:
            return {}
        
        # 获取所有专业
        all_specialties = set(dept.specialty for dept in departments)
        # print(f"需要安排的专业: {len(all_specialties)}个 - {', '.join(all_specialties)}")
        
        # 初始化一个全局的月度科室人数矩阵
        max_months = self._calculate_base_rotation_months() + 4  # 设置最大月数
        max_months_int = int(max_months)
        if max_months_int < max_months:
            max_months_int += 1  # 向上取整，确保覆盖所有月份
        month_keys = []
        for i in range(max_months_int):
            current_date = start_date + relativedelta(months=i)
            month_keys.append(current_date.strftime("%Y-%m"))
        
        # 初始化全局月度科室人数矩阵 {月份: {科室: 人数}}
        global_dept_counts = {}
        for month_key in month_keys:
            global_dept_counts[month_key] = {dept.name: 0 for dept in departments}
        
        # 初始化科室月度人数统计
        self._initialize_department_counts(departments, start_date, max_months_int)
        
        # 收集所有需要排期的科室信息
        required_rotations = self._build_required_rotations()
        
        # 为每个学生生成轮转安排
        for student in students:
            # 根据学生类型获取需要的总轮转月数
            total_months = self._calculate_total_rotation_months(student)
            # print(f"学生 {student.name} 需要轮转 {total_months} 个月")
            
            # 创建学生的排期字典
            self.schedule[student.name] = {}
            
            # 获取该学生需要的轮转科室列表
            student_rotations = self._get_student_required_rotations(student, required_rotations)
            
            # 确保total_months是整数，用于切片
            total_months_int = int(total_months)
            if total_months_int < total_months:
                total_months_int += 1  # 向上取整，确保覆盖所有月份
            
            # 为学生分配轮转科室（按月份顺序）
            self._assign_rotations_by_month(student, student_rotations, start_date, month_keys[:total_months_int], global_dept_counts)
            
            
        return self.schedule

    def _initialize_department_counts(self, departments: List[Department], start_date: datetime, months: int):
        """初始化科室月度人数统计"""
        self.department_counts = {}
        
        # 为每个科室创建月度计数器
        for dept in departments:
            self.department_counts[dept.name] = {}
            for i in range(months):
                current_date = start_date + relativedelta(months=i)
                date_key = current_date.strftime("%Y-%m")
                self.department_counts[dept.name][date_key] = 0
    
    def _build_required_rotations(self) -> List[Dict]:
        """遍历科室，构建基础轮转科室列表"""
        departments = self.department_manager.get_departments()

        base_rotations = []
        for dept in departments:
            # 基础信息
            # 遍历科室的轮转月数配置
            if hasattr(dept, 'months_per_rotation') and dept.months_per_rotation:
                for i,months in enumerate(dept.months_per_rotation, start=1):
                    rotation_info = {
                        "科室名": dept.name,
                        "科室专业": dept.specialty,
                        "月数": months,
                        "第几次轮转": i,
                        "后期轮转": dept.is_later_rotation
                    }
                    base_rotations.append(rotation_info)
        return base_rotations
    
    def _get_student_required_rotations(self, student: Student, base_rotations: List[Dict]) -> List[Dict]:
        """获取该学生需要的轮转科室列表"""
        # 深拷贝基础轮转列表
        student_rotations = []
        for rotation in base_rotations:
            student_rotations.append(rotation.copy())
            
        # 添加学生自己专业的额外轮转月数
        specialty_departments = self.department_manager.get_departments_by_specialty(student.specialty)
        # 所有学生，添加常规的额外2个月本专业轮转
        for specialty_department in specialty_departments:
            rotation_info = {
                "科室名": specialty_department.name,
                "科室专业": specialty_department.specialty,
                "月数": 2.0,
                "第几次轮转": 1,
                "后期轮转": True
            }
            student_rotations.append(rotation_info)
            
        # 社会培训学生，添加自选专业额外轮转月数
        if student.training_type == "社会培训" and student.self_selected_specialties:
            for specialty in student.self_selected_specialties:
                # 获取该专业的科室
                self_selected_depts = self.department_manager.get_departments_by_specialty(specialty)
                for self_selected_dept in self_selected_depts:
                    rotation_info = {
                        "科室名": self_selected_dept.name,
                        "科室专业": self_selected_dept.specialty,
                        "月数": 1.0,
                        "第几次轮转": 1,
                        "后期轮转": False
                    }
                    student_rotations.append(rotation_info)
        
        # 对每个专业选择科室时要特殊处理一些情况
        selected_specialties = {} # 记录每个专业已经选择的科室
        departments = self.department_manager.get_departments()
        # 遍历科室，选择每个专业人数最少的科室
        for dept in departments:
            specialty = dept.specialty
            # 如果该专业还未选择科室
            if specialty not in selected_specialties:
                # 获取该专业人数最少的科室
                least_assigned_dept = self._get_least_assigned_department(specialty)
                if least_assigned_dept:
                    selected_specialties[specialty] = least_assigned_dept

        
        filtered_rotations = []
        # 筛选并保留需要的轮转科室
        for rotation in student_rotations:
            dept_name = rotation["科室名"]
            dept_specialty = rotation["科室专业"]
            if(dept_name != selected_specialties[dept_specialty]):
                continue
            filtered_rotations.append(rotation)
            self.department_total_counts[dept_name] = self.department_total_counts.get(dept_name, 0) + 1
        return filtered_rotations
    
    def _get_least_assigned_department(self, specialty: str) -> str:
        """
        获取指定专业中总安排人数最少的科室名称
        Args:
            specialty: str - 专业名称
        Returns:
            str - 总人数最少的科室名称
        """
        # 获取该专业的所有科室
        specialty_depts = self.department_manager.get_departments_by_specialty(specialty)
        
        if not specialty_depts:
            return None
            
        # 找出该专业中总人数最少的科室
        min_count = float('inf')
        selected_dept = None
        
        for dept in specialty_depts:
            # 获取该科室的总安排人数
            total_count = self.department_total_counts.get(dept.name, 0)
            
            # 更新最小值
            if total_count < min_count:
                min_count = total_count
                selected_dept = dept.name
                
        return selected_dept

    def _assign_rotations_by_month(self, student: Student, rotations: List[Dict], 
                              start_date: datetime, month_keys: List[str], global_dept_counts: Dict):
        """按月份顺序为学生分配轮转科室，每月优先安排当月人数最少的科室"""
        # 深拷贝轮转列表，以免修改原始数据
        remaining_rotations = rotations.copy()
        # 给每个轮转科室添加剩余月数
        for rotation in remaining_rotations:
            rotation["剩余月数"] = rotation["月数"]
        
        # 记录近期轮转的专业，防止同一专业连续轮转超过3个月
        recent_specialties = []
            
        # 按月份顺序安排
        for i in range(len(month_keys)):
            month_key = month_keys[i]
            # 计算当月各科室人数，用于选择人数最少的科室
            dept_counts = global_dept_counts[month_key]
            
            # 从剩余轮转中选择当月人数最少的科室
            best_rotation = remaining_rotations[0] if remaining_rotations else None
            min_count = float('inf')
            for rotation in remaining_rotations:
                dept_name = rotation["科室名"]
                dept_count = dept_counts.get(dept_name, 0)
                # 如果月数和剩余月数不相等，则优先安排
                if rotation["月数"] != rotation["剩余月数"]:
                    best_rotation = rotation
                    break
                is_later_rotation = rotation["后期轮转"]
                # 如果是后期轮转，检查当前月份是否在一年后
                if is_later_rotation:
                    current_month = datetime.strptime(month_key, "%Y-%m")
                    start_month = start_date
                    months_diff = (current_month.year - start_month.year) * 12 + (current_month.month - start_month.month)
                    if months_diff < 12:
                        continue
                
                # 如果人数更少，更新最佳科室
                if dept_count < min_count:
                    min_count = dept_count
                    best_rotation = rotation
            
            if not best_rotation:
                continue
            # 获取科室名和月数
            dept_name = best_rotation["科室名"]
            months = best_rotation.get("月数", 1.0)
            specialty = best_rotation["科室专业"]
           
            
            # 更新近期轮转专业记录
            recent_specialties.append(specialty)
            if len(recent_specialties) > 4:  # 保持所有科室最大月数+1个月的记录
                recent_specialties.pop(0)
                
            # 安排当月轮转
            self.schedule[student.name][month_key] = dept_name
            
            # 如果是0.5个月轮转，寻找月数不是整数的科室
            if best_rotation["剩余月数"] == 0.5:
                for rotation in remaining_rotations:
                    if rotation["科室名"] == dept_name:
                        continue
                    if rotation["月数"] != int(rotation["月数"]):
                        self.schedule[student.name][month_key] = f"{dept_name}/{rotation['科室名']}"
                        global_dept_counts[month_key][dept_name] += 1
                        global_dept_counts[month_key][rotation["科室名"]] += 1
                        best_rotation["剩余月数"] -= 0.5
                        rotation["剩余月数"] -= 0.5
                        if rotation["剩余月数"] <= 0:
                            remaining_rotations.remove(rotation)
                        break
            else:
                # 更新全局计数
                global_dept_counts[month_key][dept_name] += 1
                best_rotation["剩余月数"] -= 1
            
            # 如果该轮转已完成，从列表中移除
            if best_rotation["剩余月数"] <= 0:
                remaining_rotations.remove(best_rotation)
                
        # # 检查是否所有轮转都已安排
        # if remaining_rotations:
        #     print(f"警告: 学生 {student.name} 还有 {len(remaining_rotations)} 个科室未安排完成")
        #     for rotation in remaining_rotations:
        #         print(f"  - {rotation['科室名']}: 剩余 {rotation.get('剩余月数', rotation.get('月数', 0))} 个月")

    
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
            display_date = datetime.strptime(date, "%Y-%m").strftime("%Y-%m")
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
                display_date = datetime.strptime(date, "%Y-%m").strftime("%Y-%m")
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