import json
import os
from typing import List, Dict, Any, Optional

class Student:
    def __init__(
        self, 
        name: str, 
        specialty: str, 
        grade: str, 
        position: str, 
        training_type: str,
        self_selected_specialties: List[str] = None
    ):
        self.name = name
        self.specialty = specialty  # 学生专业对应科室专业
        self.grade = grade
        self.position = position  # 职位：研究生、住院医师等
        self.training_type = training_type  # 培训方式：专科培训、社会培训
        
        # 如果是社会培训，需要自选两个专业
        self.self_selected_specialties = self_selected_specialties or []
        
    def to_dict(self) -> Dict[str, Any]:
        """将学生信息转换为字典"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "grade": self.grade,
            "position": self.position,
            "training_type": self.training_type,
            "self_selected_specialties": self.self_selected_specialties
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """从字典创建学生对象"""
        return cls(
            name=data["name"],
            specialty=data["specialty"],
            grade=data["grade"],
            position=data["position"],
            training_type=data["training_type"],
            self_selected_specialties=data.get("self_selected_specialties", [])
        )


class StudentManager:
    def __init__(self):
        self.students = []
        self.data_file = "data/students.json"
        self._load_students()
        
    def _load_students(self):
        """从文件加载学生数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.students = [Student.from_dict(item) for item in data]
            except Exception as e:
                print(f"加载学生数据失败: {e}")
                self.students = []
                
    def save_students(self):
        """保存学生数据到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [student.to_dict() for student in self.students]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存学生数据失败: {e}")
            
    def add_student(self, student: Student):
        """添加学生"""
        self.students.append(student)
        self.save_students()
        
    def remove_student(self, index: int):
        """删除学生"""
        if 0 <= index < len(self.students):
            del self.students[index]
            self.save_students()
            
    def update_student(self, index: int, student: Student):
        """更新学生信息"""
        if 0 <= index < len(self.students):
            self.students[index] = student
            self.save_students()
            
    def get_students(self) -> List[Student]:
        """获取所有学生"""
        return self.students
        
    def import_from_excel(self, file_path: str) -> int:
        """从Excel导入学生数据"""
        import pandas as pd
        
        try:
            df = pd.read_excel(file_path)
            count = 0
            
            for _, row in df.iterrows():
                # 假设Excel文件有必要的列
                name = row.get('姓名', '')
                specialty = row.get('科室', '')
                grade = row.get('年级', '')
                position = row.get('职位', '')
                
                # 默认为专科培训
                training_type = "专科培训"
                self_selected_specialties = []
                
                if name and specialty and grade:
                    student = Student(
                        name=name,
                        specialty=specialty,
                        grade=grade,
                        position=position,
                        training_type=training_type,
                        self_selected_specialties=self_selected_specialties
                    )
                    self.add_student(student)
                    count += 1
                    
            return count
        except Exception as e:
            print(f"导入Excel失败: {e}")
            return 0 