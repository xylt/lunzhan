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
        
    def _calculate_total_rotation_months(self, student: Student) -> int:
        """计算该学生需要的总轮转月数"""
        departments = self.department_manager.get_departments()
            
        # 计算所有科室的基础轮转月数
        total_months = 0
        calculated_specialties = set()
        for dept in departments:
            # 获取科室总月数
            if hasattr(dept, 'get_total_months'):
                # 如果已经遍历过科室的专业，不再计算
                if dept.specialty not in calculated_specialties:
                    total_months += dept.get_total_months()
                    calculated_specialties.add(dept.specialty)
        
        # 学生自己的专业额外增加2个月
        total_months += 2
        
        # 如果是社会培训，额外增加2个自选专业，每个1个月
        if student.training_type == "社会培训" and student.self_selected_specialties:
            total_months += len(student.self_selected_specialties)
            
        return total_months

    def generate_schedule(self, start_date: datetime, grade: str, months: int = 36) -> Dict[str, Dict[str, str]]:
        """生成轮转排期"""
        students = [s for s in self.student_manager.get_students() if s.grade == grade]
        departments = self.department_manager.get_departments()
        
        if not students or not departments:
            return {}
        
        # 获取所有专业
        all_specialties = set(dept.specialty for dept in departments)
        print(f"需要安排的专业: {len(all_specialties)}个 - {', '.join(all_specialties)}")
        
        # 初始化一个全局的月度科室人数矩阵
        max_months = 60  # 设置一个足够大的月数范围
        month_keys = []
        for i in range(max_months):
            current_date = start_date + timedelta(days=30*i)
            month_keys.append(current_date.strftime("%Y-%m-%d"))
        
        # 初始化全局月度科室人数矩阵 {月份: {科室: 人数}}
        global_dept_counts = {}
        for month_key in month_keys:
            global_dept_counts[month_key] = {dept.name: 0 for dept in departments}
        
        # 初始化科室月度人数统计
        self._initialize_department_counts(departments, start_date, max_months)
        
        # 收集所有需要排期的科室信息
        required_rotations = self._build_required_rotations()
        
        # 为每个学生生成轮转安排
        for student in students:
            # 根据学生类型获取需要的总轮转月数
            total_months = self._calculate_total_rotation_months(student)
            print(f"学生 {student.name} 需要轮转 {total_months} 个月")
            
            # 创建学生的排期字典
            self.schedule[student.name] = {}
            
            # 获取该学生需要的轮转科室列表
            student_rotations = self._get_student_required_rotations(student, required_rotations)
            
            # 按科室重要性排序
            student_rotations.sort(key=lambda x: x['优先级'], reverse=True)
            
            # 确保total_months是整数，用于切片
            total_months_int = int(total_months)
            if total_months_int < total_months:
                total_months_int += 1  # 向上取整，确保覆盖所有月份
            
            # 为学生分配轮转科室（按月份顺序）
            self._assign_rotations_by_month(student, student_rotations, start_date, month_keys[:total_months_int], global_dept_counts)
            
            # 确保每个月都有排期
            self._ensure_monthly_schedule(student.name, start_date, month_keys[:total_months_int])
            
        # 处理半月排期合并
        self._handle_special_display()
            
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
    
    def _build_required_rotations(self) -> List[Dict]:
        """构建专科培训所需的轮转科室列表"""
        required_rotations = [
            {"科室名": "心内一科", "月数": 2.0, "优先级": 10, "是否第一次轮转": True},
            {"科室名": "心内一科", "月数": 1.5, "优先级": 5, "是否第一次轮转": False},
            {"科室名": "心内二科", "月数": 2.0, "优先级": 10, "是否第一次轮转": True},
            {"科室名": "心内二科", "月数": 1.5, "优先级": 5, "是否第一次轮转": False},
            {"科室名": "心电图室", "月数": 0.5, "优先级": 5, "是否第一次轮转": True},
            {"科室名": "呼吸一科", "月数": 1.0, "优先级": 9, "是否第一次轮转": True},
            {"科室名": "呼吸二科", "月数": 2.0, "优先级": 8, "是否第一次轮转": False},
            {"科室名": "消化科", "月数": 1.0, "优先级": 8, "是否第一次轮转": True},
            {"科室名": "中西医肝病科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "感染科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "风湿科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "肾内科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "血液科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "内分泌科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "神经内科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "重症医学科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "肿瘤科", "月数": 2.0, "优先级": 7, "是否第一次轮转": True},
            {"科室名": "老年病科", "月数": 2.0, "优先级": 6, "是否第一次轮转": True},
            {"科室名": "急诊科", "月数": 3.0, "优先级": 8, "是否第一次轮转": True},
        ]
        return required_rotations
    
    def _get_student_required_rotations(self, student: Student, base_rotations: List[Dict]) -> List[Dict]:
        """获取该学生需要的轮转科室列表"""
        # 深拷贝基础轮转列表
        student_rotations = []
        for rotation in base_rotations:
            student_rotations.append(rotation.copy())
            
        # 添加学生自己专业的额外轮转月数
        specialty_departments = self.department_manager.get_departments_by_specialty(student.specialty)
        if specialty_departments:
            # 所有学生，添加常规的额外2个月轮转
            main_dept = specialty_departments[0]
            student_rotations.append({
                "科室名": main_dept.name,
                "月数": 2.0,
                "优先级": 10,
                "是否第一次轮转": False,
                "是否本专业": True
            })
            
        # 社会培训学生，添加自选专业额外轮转月数
        if student.training_type == "社会培训" and student.self_selected_specialties:
            for specialty in student.self_selected_specialties:
                # 如果自选专业是学生本专业，已经额外轮转2个月，无需再添加
                if specialty == student.specialty:
                    continue
                
                # 获取该专业的科室
                specialty_depts = self.department_manager.get_departments_by_specialty(specialty)
                if specialty_depts:
                    # 所有学生的自选专业
                    student_rotations.append({
                        "科室名": specialty_depts[0].name,
                        "月数": 1.0,
                        "优先级": 9,
                        "是否第一次轮转": False,
                        "是否自选专业": True
                    })
        
        # 对每个专业选择科室时要特殊处理一些情况
        selected_specialties = {}  # 记录每个专业已经选择的科室和轮转次数
        filtered_rotations = []
        
        # 先获取所有科室所属的专业
        dept_to_specialty = {}
        for dept in self.department_manager.get_departments():
            dept_to_specialty[dept.name] = dept.specialty
        
        # 记录已添加的科室及其轮转次数
        dept_rotation_count = {}
        
        # 筛选并保留需要的轮转科室
        for rotation in student_rotations:
            dept_name = rotation["科室名"]
            specialty = dept_to_specialty.get(dept_name, "未知专业")
            is_first_rotation = rotation.get("是否第一次轮转", False)
            
            # 初始化科室轮转次数计数
            if dept_name not in dept_rotation_count:
                dept_rotation_count[dept_name] = 0
            
            # 针对心内一科和心内二科的特殊处理，允许两次轮转
            if dept_name in ["心内一科", "心内二科"]:
                # 如果是第一次轮转或者尚未达到最大轮转次数
                if is_first_rotation or dept_rotation_count[dept_name] < 2:
                    filtered_rotations.append(rotation)
                    dept_rotation_count[dept_name] += 1
                    continue
            
            # 标准处理
            if specialty not in selected_specialties or rotation.get("是否本专业", False) or rotation.get("是否自选专业", False):
                selected_specialties[specialty] = dept_name
                filtered_rotations.append(rotation)
                dept_rotation_count[dept_name] += 1
        
        return filtered_rotations
        
    def _assign_rotations_by_month(self, student: Student, rotations: List[Dict], 
                              start_date: datetime, month_keys: List[str], global_dept_counts: Dict):
        """按月份顺序为学生分配轮转科室，每月优先安排人数最少的科室"""
        # 深拷贝轮转列表，以免修改原始数据
        remaining_rotations = rotations.copy()
        
        # 记录需要连续安排的轮转（如某科室需要连续轮转2个月）
        continuous_rotation = None
        continuous_months_left = 0
        
        # 记录近期轮转的专业，防止同一专业连续轮转超过3个月
        recent_specialties = []
        
        # 获取所有科室所属的专业
        dept_to_specialty = {}
        for dept in self.department_manager.get_departments():
            dept_to_specialty[dept.name] = dept.specialty
            
        # 按月份顺序安排
        for month_key in month_keys:
            # 如果有连续轮转，优先处理
            if continuous_rotation and continuous_months_left > 0:
                # 获取该科室的专业
                dept_name = continuous_rotation["科室名"]
                specialty = dept_to_specialty.get(dept_name, "未知专业")
                
                # 检查这个专业是否已经连续轮转了3个月
                continuous_specialty_count = 1  # 当前月份算一个月
                for recent_specialty in recent_specialties[-2:]:  # 加上前两个月的记录
                    if recent_specialty == specialty:
                        continuous_specialty_count += 1
                
                # 如果已经连续轮转了3个月，停止连续轮转
                if continuous_specialty_count >= 3:
                    # 尝试安排其他专业，特别是针对心内科
                    # 临时跳过连续轮转，稍后重新安排
                    continuous_rotation = None
                    continuous_months_left = 0
                else:
                    # 继续安排该科室
                    self.schedule[student.name][month_key] = dept_name
                    
                    # 更新全局计数
                    global_dept_counts[month_key][dept_name] += 1
                    
                    # 更新近期轮转专业记录
                    recent_specialties.append(specialty)
                    if len(recent_specialties) > 6:  # 保持最近6个月的记录
                        recent_specialties.pop(0)
                    
                    # 减少剩余连续月数
                    continuous_months_left -= 1
                    
                    # 如果连续安排结束，检查是否需要从列表中移除该轮转
                    if continuous_months_left == 0:
                        continuous_rotation["剩余月数"] = continuous_rotation["剩余月数"] - 1
                        # 如果该轮转已完成，从列表中移除
                        if continuous_rotation["剩余月数"] <= 0:
                            if continuous_rotation in remaining_rotations:
                                remaining_rotations.remove(continuous_rotation)
                        continuous_rotation = None
                    
                    continue
            
            # 计算当月各科室人数，用于选择人数最少的科室
            dept_counts = global_dept_counts[month_key]
            
            # 从剩余轮转中选择当月人数最少的科室，同时避免专业连续轮转超过3个月
            best_rotation = None
            min_count = float('inf')
            
            for rotation in remaining_rotations:
                dept_name = rotation["科室名"]
                dept_count = dept_counts.get(dept_name, 0)
                specialty = dept_to_specialty.get(dept_name, "未知专业")
                
                # 检查该专业是否会导致连续轮转超过3个月
                consecutive_count = 1  # 当前月份算一个月
                for recent_specialty in recent_specialties[-2:]:  # 检查最近2个月
                    if recent_specialty == specialty:
                        consecutive_count += 1
                
                # 特别处理心内科专业，因为它容易出现连续轮转问题
                is_heart_specialty = specialty == "心内科"
                
                # 如果该专业已经连续轮转2个月，且不是强制的本专业轮转，则跳过
                # 对于心内科，如果已经连续轮转2个月，无论是否是本专业，都尝试跳过
                if (consecutive_count >= 2 and not rotation.get("是否本专业", False) and not rotation.get("是否自选专业", False)) or \
                   (is_heart_specialty and consecutive_count >= 2 and not rotation.get("优先级", 0) > 9):
                    continue
                
                # 如果人数更少，更新最佳科室
                if dept_count < min_count:
                    min_count = dept_count
                    best_rotation = rotation
            
            # 如果找不到合适的科室，跳过当前月份
            if not best_rotation:
                continue
            
            # 获取科室名和月数
            dept_name = best_rotation["科室名"]
            months = best_rotation.get("月数", 1.0)
            
            # 更新近期轮转专业记录
            specialty = dept_to_specialty.get(dept_name, "未知专业")
            recent_specialties.append(specialty)
            if len(recent_specialties) > 6:  # 保持最近6个月的记录
                recent_specialties.pop(0)
            
            # 初始化剩余月数（如果不存在）
            if "剩余月数" not in best_rotation:
                best_rotation["剩余月数"] = months
                
            # 安排当月轮转
            self.schedule[student.name][month_key] = dept_name
            
            # 如果是0.5个月轮转，添加标记
            if months == 0.5 or best_rotation["剩余月数"] == 0.5:
                self.schedule[student.name][month_key] = f"{dept_name}:half"
                best_rotation["剩余月数"] -= 0.5
            else:
                # 对于连续多月的轮转，设置连续轮转状态
                if best_rotation["剩余月数"] > 1:
                    continuous_rotation = best_rotation
                    # 限制连续安排不超过2个月，防止同一专业连续超过3个月
                    # 特别是对于心内科，限制连续安排不超过1个月
                    if specialty == "心内科":
                        continuous_months_left = min(1, int(best_rotation["剩余月数"]) - 1)
                    else:
                        continuous_months_left = min(2, int(best_rotation["剩余月数"]) - 1)
                    best_rotation["剩余月数"] = best_rotation["剩余月数"] - 1
                else:
                    # 一个月或不足一个月的轮转
                    best_rotation["剩余月数"] -= 1
            
            # 更新全局计数
            global_dept_counts[month_key][dept_name] += 1
            
            # 如果该轮转已完成，从列表中移除
            if best_rotation["剩余月数"] <= 0 and not continuous_months_left:
                remaining_rotations.remove(best_rotation)
                
        # 检查是否所有轮转都已安排
        if remaining_rotations:
            print(f"警告: 学生 {student.name} 还有 {len(remaining_rotations)} 个科室未安排完成")
            for rotation in remaining_rotations:
                print(f"  - {rotation['科室名']}: 剩余 {rotation.get('剩余月数', rotation.get('月数', 0))} 个月")

    def _ensure_monthly_schedule(self, student_name: str, start_date: datetime, month_keys: List[str]):
        """确保每个月都有排期安排"""
        # 获取所有有排期的月份
        scheduled_months = set(self.schedule[student_name].keys())
        
        # 获取所有需要排期的月份
        required_months = set(month_keys)
        
        # 找出缺少排期的月份
        missing_months = required_months - scheduled_months
        
        if missing_months:
            print(f"学生 {student_name} 有 {len(missing_months)} 个月缺少排期")
            
            # 获取所有科室
            departments = self.department_manager.get_departments()
            
            # 获取学生信息
            student = next((s for s in self.student_manager.get_students() if s.name == student_name), None)
            if not student:
                return
                
            # 获取所有科室专业映射
            dept_to_specialty = {}
            for dept in departments:
                dept_to_specialty[dept.name] = dept.specialty
                
            # 遍历每个缺少排期的月份
            for missing_month in sorted(missing_months):
                # 获取学生已经安排过的科室
                arranged_depts = set()
                arranged_specialties = {}  # 记录各专业已安排的月数
                for month, dept_name in self.schedule[student_name].items():
                    # 去掉可能的半月标记
                    if ":half" in dept_name:
                        dept_name = dept_name.split(":half")[0]
                    arranged_depts.add(dept_name)
                    
                    # 统计各专业的安排月数
                    specialty = dept_to_specialty.get(dept_name, "未知专业")
                    arranged_specialties[specialty] = arranged_specialties.get(specialty, 0) + 1
                
                # 常规处理：优先安排学生未轮转过的科室
                unarranged_depts = [dept for dept in departments if dept.name not in arranged_depts]
                
                if unarranged_depts:
                    # 计算每个科室当前月的人数
                    dept_counts = {}
                    for dept in unarranged_depts:
                        dept_counts[dept.name] = self.department_counts.get(dept.name, {}).get(missing_month, 0)
                    
                    # 在未安排的科室中选择人数最少的科室
                    best_dept = min(unarranged_depts, key=lambda dept: dept_counts[dept.name])
                    self.schedule[student_name][missing_month] = best_dept.name
                    
                    # 更新科室人数统计
                    if best_dept.name not in self.department_counts:
                        self.department_counts[best_dept.name] = {}
                    if missing_month not in self.department_counts[best_dept.name]:
                        self.department_counts[best_dept.name][missing_month] = 0
                    self.department_counts[best_dept.name][missing_month] += 1
                else:
                    # 如果所有科室都已安排过，则选择当前月份人数最少的科室
                    # 计算每个科室当前月的人数
                    dept_counts = {}
                    for dept in departments:
                        dept_counts[dept.name] = self.department_counts.get(dept.name, {}).get(missing_month, 0)
                    
                    # 选择当前月人数最少的科室
                    best_dept = min(departments, key=lambda dept: dept_counts[dept.name])
                    self.schedule[student_name][missing_month] = best_dept.name
                    
                    # 更新科室人数统计
                    if best_dept.name not in self.department_counts:
                        self.department_counts[best_dept.name] = {}
                    if missing_month not in self.department_counts[best_dept.name]:
                        self.department_counts[best_dept.name][missing_month] = 0
                    self.department_counts[best_dept.name][missing_month] += 1
    
    def _handle_special_display(self):
        """处理特殊显示需求，合并所有0.5个月的科室排期"""
        for student_name, schedule_dict in self.schedule.items():
            # 处理所有0.5个月的科室排期
            half_month_dates = []
            
            # 第一步：找出所有包含半月标记的排期
            for date_key, dept in list(schedule_dict.items()):
                if ":half" in dept:
                    half_month_dates.append(date_key)
                    # 去掉标记
                    schedule_dict[date_key] = dept.split(":half")[0]
            
            # 第二步：尝试合并相邻的半月排期
            half_month_dates.sort()
            for i in range(len(half_month_dates) - 1):
                current_date = half_month_dates[i]
                next_date = half_month_dates[i + 1]
                
                # 计算日期之间的间隔
                current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                next_dt = datetime.strptime(next_date, "%Y-%m-%d")
                days_gap = (next_dt - current_dt).days
                
                # 如果两个日期足够接近（间隔不超过20天），合并显示
                if days_gap <= 20:
                    current_dept = schedule_dict[current_date]
                    next_dept = schedule_dict[next_date]
                    
                    # 合并显示
                    combined_dept = f"{current_dept}/{next_dept}"
                    schedule_dict[current_date] = combined_dept
    
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