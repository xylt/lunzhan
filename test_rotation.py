import pandas as pd
from datetime import datetime, timedelta
from models.student import Student, StudentManager
from models.department import Department, DepartmentManager
from models.rotation import RotationScheduler

def test_rotation():
    # 创建一些测试数据
    student_manager = StudentManager()
    department_manager = DepartmentManager()
    
    # 添加一些测试学生
    student1 = Student(
        name="测试学生1",
        specialty="心内科",
        grade="2023级",
        position="研究生",
        training_type="专科培训"
    )
    student_manager.add_student(student1)
    
    # 确保有一些科室数据
    if not department_manager.get_departments():
        print("初始化科室数据...")
        department_manager._initialize_default_departments()
    
    # 创建调度器
    scheduler = RotationScheduler(student_manager, department_manager)
    
    # 生成排期
    start_date = datetime.now()
    grade = "2023级"
    months = 12
    
    print(f"生成排期: {grade}, 开始日期: {start_date}, 月数: {months}")
    scheduler.generate_schedule(start_date, grade, months)
    
    # 获取排期数据
    print("获取排期数据...")
    
    # 检查学生是否被安排
    students = [s for s in student_manager.get_students() if s.grade == grade]
    print(f"找到 {len(students)} 个学生")
    
    # 检查排期数据
    for student in students:
        if student.name in scheduler.schedule:
            print(f"学生 {student.name} 有排期数据: {len(scheduler.schedule[student.name])} 个月")
        else:
            print(f"学生 {student.name} 没有排期数据")
    
    # 找到所有日期
    all_dates = set()
    for student_name, dates in scheduler.schedule.items():
        if student_name in [s.name for s in students]:
            all_dates.update(dates.keys())
    
    # 排序日期
    sorted_dates = sorted(all_dates)
    print(f"排期日期: {sorted_dates}")
    
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
        if student.name not in scheduler.schedule:
            continue
            
        data["姓名"].append(student.name)
        data["科室"].append(student.specialty)
        data["年级"].append(student.grade)
        data["职位"].append(student.position)
        
        for date in sorted_dates:
            display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
            if date in scheduler.schedule[student.name]:
                data[display_date].append(scheduler.schedule[student.name][date])
            else:
                data[display_date].append("")
    
    # 检查所有列的长度是否一致
    for key, value in data.items():
        print(f"列 '{key}' 长度: {len(value)}")
    
    # 确保所有列长度一致
    length_check = len(data["姓名"])
    for key, value in data.items():
        if len(value) != length_check:
            print(f"修正列 '{key}' 长度")
            data[key] = value + [""] * (length_check - len(value))
    
    # 再次检查所有列的长度
    for key, value in data.items():
        print(f"修正后列 '{key}' 长度: {len(value)}")
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    print("DataFrame创建成功")
    print(df.head())

if __name__ == "__main__":
    test_rotation() 