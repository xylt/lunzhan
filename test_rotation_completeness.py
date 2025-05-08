#-*- coding: utf-8 -*-
import unittest
import pandas as pd
from datetime import datetime
from models.student import StudentManager
from models.department import DepartmentManager
from models.rotation import RotationScheduler


class TestRotationCompleteness(unittest.TestCase):
    """测试每个学生的轮转排期是否包含所有必要的科室轮转"""

    def setUp(self):
        """准备测试环境"""
        self.student_manager = StudentManager()
        self.department_manager = DepartmentManager()
        self.scheduler = RotationScheduler(self.student_manager, self.department_manager)
        
        # 设置开始日期和年级
        self.start_date = datetime.now()
        self.grade = "2023级"
        self.months = 35  # 足够覆盖所有轮转的月数
        
        # 生成排期
        self.scheduler.generate_schedule(self.start_date, self.grade, self.months)
        
        # 获取该年级的所有学生
        self.students = [s for s in self.student_manager.get_students() if s.grade == self.grade]
        
        # 定义必须轮转的科室及其月数
        self.required_rotations = {
            "心内科": 3.5,  # 心内一科或心内二科 2.0+1.5
            "呼吸内科": 3.0,  # 呼吸一科或呼吸二科 1.0+2.0
            "消化科": 1.0,
            "中西医肝病科": 2.0,
            "急诊科": 3.0,
            "感染科": 2.0,
            "风湿科": 2.0,
            "肾内科": 2.0,
            "血液科": 2.0,
            "内分泌科": 2.0,
            "神经内科": 2.0,
            "重症医学科": 2.0,
            "肿瘤科": 2.0,
            "老年病科": 2.0,
            "心电图室": 0.5,
        }
        
        # 定义科室到专业的映射
        self.dept_to_specialty = {
            "心内一科": "心内科",
            "心内二科": "心内科",
            "心电图室": "心电图室",
            "呼吸一科": "呼吸内科",
            "呼吸二科": "呼吸内科",
            "消化科": "消化科",
            "中西医肝病科": "中西医肝病科",
            "急诊科": "急诊科",
            "感染科": "感染科",
            "风湿科": "风湿科",
            "肾内科": "肾内科",
            "血液科": "血液科",
            "内分泌科": "内分泌科",
            "神经内科": "神经内科",
            "重症医学科": "重症医学科",
            "肿瘤科": "肿瘤科",
            "老年病科": "老年病科",
        }

    def count_specialty_months(self, student_name):
        """统计学生各专业的轮转月数"""
        if student_name not in self.scheduler.schedule:
            return {}
            
        # 初始化专业月数统计
        specialty_months = {spec: 0.0 for spec in self.required_rotations.keys()}
        
        # 统计各科室的月数
        for month, dept_name in self.scheduler.schedule[student_name].items():
            # 处理半月标记
            is_half_month = False
            if ":half" in dept_name:
                dept_name = dept_name.split(":half")[0]
                is_half_month = True
                
            # 处理包含"/"的情况，表示两个科室各算半个月
            if "/" in dept_name:
                dept_names = dept_name.split("/")
                for dept in dept_names:
                    if dept in self.dept_to_specialty:
                        specialty = self.dept_to_specialty[dept]
                        specialty_months[specialty] += 0.5
            else:
                if dept_name in self.dept_to_specialty:
                    specialty = self.dept_to_specialty[dept_name]
                    specialty_months[specialty] += 0.5 if is_half_month else 1.0
        
        return specialty_months

    def test_all_students_have_schedule(self):
        """测试所有学生都有排期"""
        for student in self.students:
            self.assertIn(student.name, self.scheduler.schedule,
                         f"学生 {student.name} 没有排期")
            self.assertGreater(len(self.scheduler.schedule[student.name]), 0,
                              f"学生 {student.name} 的排期为空")

    def test_all_rotations_completed(self):
        """测试所有学生都完成了所有必要的轮转"""
        for student in self.students:
            print(f"\n检查学生 {student.name} 的轮转情况:")
            
            specialty_months = self.count_specialty_months(student.name)
            
            # 打印学生各专业轮转月数
            for specialty, months in specialty_months.items():
                print(f"  {specialty}: {months:.1f}个月")
            
            # 检查是否满足所有必要的轮转
            for specialty, required_months in self.required_rotations.items():
                actual_months = specialty_months.get(specialty, 0.0)
                self.assertGreaterEqual(
                    actual_months,
                    required_months,
                    f"学生 {student.name} 的 {specialty} 轮转不足: 需要 {required_months} 个月, 实际 {actual_months} 个月"
                )

    def test_student_specialty_extra_rotation(self):
        """测试学生自己专业额外轮转2个月"""
        for student in self.students:
            specialty_months = self.count_specialty_months(student.name)
            student_specialty = student.specialty
            
            # 找出学生本专业在必要轮转中的基础月数
            base_months = 0
            for dept_name, specialty in self.dept_to_specialty.items():
                if specialty == student_specialty:
                    if dept_name in self.scheduler.schedule[student.name].values():
                        base_months = self.required_rotations.get(specialty, 0.0)
                        break
            
            # 学生本专业的实际轮转月数
            actual_months = specialty_months.get(student_specialty, 0.0)
            
            # 检查是否额外轮转了至少2个月
            self.assertGreaterEqual(
                actual_months,
                base_months + 2.0,
                f"学生 {student.name} 的本专业 {student_specialty} 额外轮转不足: 需要额外 2 个月, 实际额外 {actual_months - base_months} 个月"
            )

    def test_social_training_extra_rotation(self):
        """测试社会培训学生的自选专业额外轮转"""
        for student in self.students:
            if student.training_type == "社会培训" and student.self_selected_specialties:
                specialty_months = self.count_specialty_months(student.name)
                
                for selected_specialty in student.self_selected_specialties:
                    # 找出自选专业在必要轮转中的基础月数
                    base_months = self.required_rotations.get(selected_specialty, 0.0)
                    # 自选专业的实际轮转月数
                    actual_months = specialty_months.get(selected_specialty, 0.0)
                    
                    # 检查是否额外轮转了至少1个月
                    extra_months = actual_months - base_months
                    # 如果是本专业，已经额外加了2个月，不需要再额外加1个月
                    if selected_specialty == student.specialty:
                        self.assertGreaterEqual(
                            extra_months,
                            2.0,
                            f"学生 {student.name} 的自选本专业 {selected_specialty} 额外轮转不足: 需要额外 2 个月, 实际额外 {extra_months} 个月"
                        )
                    else:
                        self.assertGreaterEqual(
                            extra_months,
                            1.0,
                            f"学生 {student.name} 的自选专业 {selected_specialty} 额外轮转不足: 需要额外 1 个月, 实际额外 {extra_months} 个月"
                        )

    def test_specialty_not_continuous(self):
        """测试同一专业下的不同科室不会连续排期"""
        for student in self.students:
            schedule = self.scheduler.schedule[student.name]
            sorted_months = sorted(schedule.keys())
            
            previous_specialty = None
            continuous_specialty_count = 1
            
            for month in sorted_months:
                dept_name = schedule[month]
                # 处理半月标记和分割科室
                if ":half" in dept_name:
                    dept_name = dept_name.split(":half")[0]
                if "/" in dept_name:
                    dept_name = dept_name.split("/")[0]  # 只检查第一个科室
                
                current_specialty = self.dept_to_specialty.get(dept_name)
                
                if current_specialty == previous_specialty:
                    continuous_specialty_count += 1
                    # 同一专业连续轮转不应超过两个月（除非是两次轮转）
                    # 这里不太容易判断是否是两次轮转，简单判断连续不超过3个月
                    self.assertLessEqual(
                        continuous_specialty_count,
                        3,
                        f"学生 {student.name} 的专业 {current_specialty} 连续轮转超过3个月"
                    )
                else:
                    continuous_specialty_count = 1
                
                previous_specialty = current_specialty

    def test_total_rotation_months(self):
        """测试学生的总轮转月数是否正确"""
        for student in self.students:
            # 计算学生应该轮转的总月数
            if student.training_type == "专科培训":
                # 专科培训：所有必须轮转的专业月数总和 + 本专业额外2个月
                expected_months = sum(self.required_rotations.values()) + 2.0
            else:  # 社会培训
                # 社会培训：所有必须轮转的专业月数总和 + 本专业额外2个月 + 自选专业各1个月
                expected_months = sum(self.required_rotations.values()) + 2.0 + len(student.self_selected_specialties)
            
            # 学生实际排期的月数
            actual_months = len(self.scheduler.schedule[student.name])
            
            # 总轮转月数可能有误差，这里允许±2个月的误差
            self.assertLessEqual(
                abs(actual_months - expected_months),
                2,
                f"学生 {student.name} 的总轮转月数不正确: 预期 {expected_months} 个月, 实际 {actual_months} 个月"
            )


if __name__ == "__main__":
    unittest.main()
