#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料插入腳本
用於測試學生、老師、課程功能
"""

import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8001/api"

def test_styles():
    """測試新增風格"""
    print("=== 測試新增風格 ===")
    styles_data = [
        {"name": "Ballet", "description": "芭蕾舞"},
        {"name": "Contemporary", "description": "現代舞"},
        {"name": "Hip-Hop", "description": "街舞"},
        {"name": "Jazz", "description": "爵士舞"}
    ]
    for style in styles_data:
        try:
            response = requests.post(f"{BASE_URL}/styles", json=style)
            if response.status_code == 201:
                print(f"✓ 成功新增風格: {style['name']}")
            else:
                print(f"✗ 新增風格失敗: {style['name']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_teachers():
    """測試新增老師（含風格）"""
    print("=== 測試新增老師 ===")
    teachers_data = [
        {
            "name": "張美麗",
            "email": "zhang@dancestudio.com",
            "phone": "0912-345-678",
            "experience_years": 8,
            "bio": "專業芭蕾舞老師，畢業於國立台北藝術大學",
            "hourly_rate": 1200.00,
            "style_ids": [1, 2]  # 芭蕾、現代舞
        },
        {
            "name": "李強",
            "email": "li@dancestudio.com",
            "phone": "0923-456-789",
            "experience_years": 5,
            "bio": "街舞冠軍，擅長各種流行舞蹈",
            "hourly_rate": 1000.00,
            "style_ids": [3]  # 街舞
        },
        {
            "name": "王雅文",
            "email": "wang@dancestudio.com",
            "phone": "0934-567-890",
            "experience_years": 10,
            "bio": "爵士舞專家，具有豐富的表演經驗",
            "hourly_rate": 1300.00,
            "style_ids": [4]  # 爵士舞
        }
    ]
    for teacher in teachers_data:
        try:
            response = requests.post(f"{BASE_URL}/teachers", json=teacher)
            if response.status_code == 201:
                print(f"✓ 成功新增老師: {teacher['name']}")
            else:
                print(f"✗ 新增老師失敗: {teacher['name']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_students():
    """測試新增學生"""
    print("=== 測試新增學生 ===")
    
    students_data = [
        {
            "name": "陳小明",
            "email": "chen@example.com",
            "phone": "0987-654-321",
            "age": 25,
            "emergency_contact": "陳媽媽",
            "emergency_phone": "0912-123-456",
            "medical_notes": "無特殊疾病"
        },
        {
            "name": "林小華",
            "email": "lin@example.com",
            "phone": "0976-543-210",
            "age": 22,
            "emergency_contact": "林爸爸", 
            "emergency_phone": "0923-234-567",
            "medical_notes": "輕微氣喘"
        },
        {
            "name": "黃小美",
            "email": "huang@example.com",
            "phone": "0965-432-109",
            "age": 28,
            "emergency_contact": "黃先生",
            "emergency_phone": "0934-345-678",
            "medical_notes": "無"
        }
    ]
    
    for student in students_data:
        try:
            response = requests.post(f"{BASE_URL}/students", json=student)
            if response.status_code == 201:
                print(f"✓ 成功新增學生: {student['name']}")
            else:
                print(f"✗ 新增學生失敗: {student['name']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_rooms():
    """測試新增教室"""
    print("=== 測試新增教室 ===")
    
    rooms_data = [
        {
            "name": "Studio E",
            "capacity": 18,
            "equipment": "Sound System, Mirrors, Air Conditioning",
            "description": "新設立的練習室，環境舒適",
            "hourly_rate": 450.00,
            "is_available": True
        },
        {
            "name": "Studio F", 
            "capacity": 12,
            "equipment": "Basic Sound System, Mirrors",
            "description": "小型練習室，適合個人指導",
            "hourly_rate": 350.00,
            "is_available": True
        },
        {
            "name": "VIP Studio",
            "capacity": 8,
            "equipment": "Premium Sound System, Professional Lighting, Mirrors, Air Purifier",
            "description": "豪華練習室，提供最高品質的練習環境",
            "hourly_rate": 1000.00,
            "is_available": True
        }
    ]
    
    for room in rooms_data:
        try:
            response = requests.post(f"{BASE_URL}/rooms", json=room)
            if response.status_code == 201:
                print(f"✓ 成功新增教室: {room['name']}")
            else:
                print(f"✗ 新增教室失敗: {room['name']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_courses():
    """測試新增課程"""
    print("=== 測試新增課程 ===")
    
    courses_data = [
        {
            "name": "初級芭蕾",
            "description": "適合零基礎學員的芭蕾課程",
            "level": "beginner",
            "type": "ballet",
            "duration_minutes": 90,
            "max_students": 12,
            "price": 800.00,
            "teacher_id": 1
        },
        {
            "name": "街舞入門",
            "description": "流行街舞基礎教學",
            "level": "beginner", 
            "type": "hip-hop",
            "duration_minutes": 60,
            "max_students": 15,
            "price": 600.00,
            "teacher_id": 2
        },
        {
            "name": "爵士舞精修",
            "description": "爵士舞進階技巧訓練",
            "level": "advanced",
            "type": "jazz",
            "duration_minutes": 75,
            "max_students": 8,
            "price": 1200.00,
            "teacher_id": 3
        }
    ]
    
    for course in courses_data:
        try:
            response = requests.post(f"{BASE_URL}/courses", json=course)
            if response.status_code == 201:
                print(f"✓ 成功新增課程: {course['name']}")
            else:
                print(f"✗ 新增課程失敗: {course['name']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_get_all():
    """測試查詢所有資料"""
    print("=== 測試查詢資料 ===")
    
    endpoints = [
        ("rooms", "教室"),
        ("teachers", "老師"),
        ("students", "學生"), 
        ("courses", "課程"),
        ("schedules", "課程時間表"),
        ("enrollment", "報名記錄")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ 查詢{name}成功，共 {data.get('total', 0)} 筆記錄")
            else:
                print(f"✗ 查詢{name}失敗: {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

def test_schedules():
    """測試新增課程時間表"""
    print("=== 測試新增課程時間表 ===")
    
    schedules_data = [
        {
            "course_id": 1,
            "schedule_date": "2025-01-20",
            "start_time": "18:00:00",
            "end_time": "19:30:00",
            "room_id": 1,
            "is_active": True
        },
        {
            "course_id": 1,
            "schedule_date": "2025-01-22",
            "start_time": "18:00:00", 
            "end_time": "19:30:00",
            "room_id": 1,
            "is_active": True
        },
        {
            "course_id": 2,
            "schedule_date": "2025-01-21",
            "start_time": "19:00:00",
            "end_time": "20:30:00",
            "room_id": 2,
            "is_active": True
        },
        {
            "course_id": 3,
            "schedule_date": "2025-01-24",
            "start_time": "19:00:00",
            "end_time": "20:00:00",
            "room_id": 3,
            "is_active": True
        }
    ]
    
    for schedule in schedules_data:
        try:
            response = requests.post(f"{BASE_URL}/schedules", json=schedule)
            if response.status_code == 201:
                result = response.json()
                print(f"✓ 成功新增課程時間表: {schedule['schedule_date']} ({result.get('day_of_week')})")
            else:
                print(f"✗ 新增課程時間表失敗: {schedule['schedule_date']} - {response.text}")
        except Exception as e:
            print(f"✗ 請求錯誤: {str(e)}")

if __name__ == "__main__":
    print("開始測試舞蹈教室 API...")
    print("請確保後端服務已啟動在 http://localhost:8001")
    print()
    test_styles()
    print()
    test_rooms()
    print()
    test_teachers()
    print()
    test_students()
    print()
    test_courses()
    print()
    test_schedules()
    print()
    test_get_all()
    print()
    print("測試完成！")
