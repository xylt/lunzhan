import json
import os
from typing import List, Dict, Any, Optional

class Department:
    def __init__(
        self, 
        name: str,              # 科室名称
        specialty: str,         # 科室专业
        rotation_times: int,    # 需要轮转次数
        months_per_rotation: float,  # 每次轮转月数
        is_later_rotation: bool = False  # 是否在第一年后轮转
    ):
        self.name = name
        self.specialty = specialty
        self.rotation_times = rotation_times
        self.months_per_rotation = months_per_rotation
        self.is_later_rotation = is_later_rotation
        
    def to_dict(self) -> Dict[str, Any]:
        """将科室信息转换为字典"""
        return {
            "name": self.name,
            "specialty": self.specialty,
            "rotation_times": self.rotation_times,
            "months_per_rotation": self.months_per_rotation,
            "is_later_rotation": self.is_later_rotation
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Department':
        """从字典创建科室对象"""
        return cls(
            name=data["name"],
            specialty=data["specialty"],
            rotation_times=data["rotation_times"],
            months_per_rotation=data["months_per_rotation"],
            is_later_rotation=data.get("is_later_rotation", False)
        )


class DepartmentManager:
    def __init__(self):
        self.departments = []
        self.data_file = "data/departments.json"
        self._load_departments()
        self._initialize_default_departments()
        
    def _load_departments(self):
        """从文件加载科室数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.departments = [Department.from_dict(item) for item in data]
            except Exception as e:
                print(f"加载科室数据失败: {e}")
                self.departments = []
    
    def _initialize_default_departments(self):
        """如果没有科室数据，初始化默认科室"""
        if not self.departments:
            # 心内科 (两次轮转)
            self.add_department(Department("心内一科", "心内科", 2, 2.0))  # 第一次轮转2个月
            self.add_department(Department("心内二科", "心内科", 2, 2.0))  # 第一次轮转2个月
            self.add_department(Department("心电图室", "心内科", 1, 0.5))  # 轮转0.5个月
            
            # 呼吸内科 (两次轮转)
            self.add_department(Department("呼吸一科", "呼吸内科", 2, 1.0))  # 第一次轮转1个月
            self.add_department(Department("呼吸二科", "呼吸内科", 2, 1.0))  # 第一次轮转1个月
            
            # 消化科和中西医肝病科
            self.add_department(Department("消化科", "消化科", 1, 1.0))
            self.add_department(Department("中西医肝病科", "肝病科", 1, 2.0))
            
            # 急诊科 (3个月轮转)
            self.add_department(Department("急诊科", "急诊科", 1, 3.0))
            
            # 2个月轮转的科室
            self.add_department(Department("感染科", "感染科", 1, 2.0))
            self.add_department(Department("风湿科", "风湿科", 1, 2.0))
            self.add_department(Department("肾内科", "肾内科", 1, 2.0))
            self.add_department(Department("血液科", "血液科", 1, 2.0))
            self.add_department(Department("内分泌科", "内分泌科", 1, 2.0))
            self.add_department(Department("神经内科", "神经内科", 1, 2.0))
            self.add_department(Department("重症医学科", "重症医学科", 1, 2.0))
            self.add_department(Department("肿瘤科", "肿瘤科", 1, 2.0))
            self.add_department(Department("老年病科", "老年病科", 1, 2.0))
                
    def save_departments(self):
        """保存科室数据到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [dept.to_dict() for dept in self.departments]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存科室数据失败: {e}")
            
    def add_department(self, department: Department):
        """添加科室"""
        self.departments.append(department)
        self.save_departments()
        
    def remove_department(self, index: int):
        """删除科室"""
        if 0 <= index < len(self.departments):
            del self.departments[index]
            self.save_departments()
            
    def update_department(self, index: int, department: Department):
        """更新科室信息"""
        if 0 <= index < len(self.departments):
            self.departments[index] = department
            self.save_departments()
            
    def get_departments(self) -> List[Department]:
        """获取所有科室"""
        return self.departments
    
    def get_specialties(self) -> List[str]:
        """获取所有科室专业"""
        specialties = set()
        for dept in self.departments:
            specialties.add(dept.specialty)
        return list(specialties)
    
    def get_departments_by_specialty(self, specialty: str) -> List[Department]:
        """根据专业获取科室列表"""
        return [dept for dept in self.departments if dept.specialty == specialty] 