# 舞蹈教室管理系統 API 文檔

## 概述
這個 API 提供了完整的舞蹈教室管理功能，包括學生管理、老師管理、課程管理和報名管理。

## 基礎 URL
```
http://localhost:8001/api
```

## API 端點

### 1. 學生管理 (`/api/students`)

#### GET /api/students
取得所有學生資料
- **方法**: GET
- **回應格式**:
```json
{
  "success": true,
  "students": [
    {
      "id": 1,
      "name": "陳小明",
      "email": "chen@example.com",
      "phone": "0987-654-321",
      "age": 25,
      "emergency_contact": "陳媽媽",
      "emergency_phone": "0912-123-456",
      "medical_notes": "無特殊疾病",
      "remaining_classes": 10,
      "membership_expiry": "2025-12-31",
      "created_at": "2025-01-01T12:00:00",
      "updated_at": "2025-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

#### POST /api/students
新增學生
- **方法**: POST
- **請求格式**:
```json
{
  "name": "陳小明",
  "email": "chen@example.com",
  "phone": "0987-654-321",
  "age": 25,
  "emergency_contact": "陳媽媽",
  "emergency_phone": "0912-123-456",
  "medical_notes": "無特殊疾病",
  "remaining_classes": 10,
  "membership_expiry": "2025-12-31"
}
```

### 2. 老師管理 (`/api/teachers`)

#### GET /api/teachers
取得所有老師資料，包含風格資訊
- **方法**: GET
- **回應格式**:
```json
{
  "success": true,
  "teachers": [
    {
      "id": 1,
      "name": "張美麗",
      "email": "zhang@dancestudio.com",
      "phone": "0912-345-678",
      "experience_years": 8,
      "bio": "專業芭蕾舞老師，畢業於國立台北藝術大學",
      "hourly_rate": 1200.00,
      "styles": [
        { "id": 1, "name": "Ballet" },
        { "id": 2, "name": "Contemporary" }
      ],
      "created_at": "2025-01-01T12:00:00",
      "updated_at": "2025-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

#### POST /api/teachers
新增老師（可指定風格 ID 陣列）
- **方法**: POST
- **請求格式**:
```json
{
  "name": "張美麗",
  "email": "zhang@dancestudio.com",
  "phone": "0912-345-678",
  "experience_years": 8,
  "bio": "專業芭蕾舞老師，畢業於國立台北藝術大學",
  "hourly_rate": 1200.00,
  "style_ids": [1, 2]
}
```

### 2.1 風格管理 (`/api/styles`)

#### GET /api/styles
取得所有風格資料
- **方法**: GET
- **回應格式**:
```json
{
  "success": true,
  "styles": [
    { "id": 1, "name": "Ballet", "description": "芭蕾舞" },
    { "id": 2, "name": "Contemporary", "description": "現代舞" }
  ],
  "total": 2
}
```

#### POST /api/styles
新增風格
- **方法**: POST
- **請求格式**:
```json
{
  "name": "Jazz",
  "description": "爵士舞"
}
```

### 3. 課程管理 (`/api/courses`)

#### GET /api/courses
取得所有課程資料（包含老師資訊）
- **方法**: GET

#### POST /api/courses
新增課程
- **方法**: POST
- **請求格式**:
```json
{
  "name": "初級芭蕾",
  "description": "適合零基礎學員的芭蕾課程",
  "level": "beginner",
  "type": "ballet",
  "duration_minutes": 90,
  "max_students": 12,
  "price": 800.00,
  "teacher_id": 1
}
```

### 4. 教室管理 (`/api/rooms`)

#### GET /api/rooms
取得所有教室資料
- **方法**: GET
- **回應格式**:
```json
{
  "success": true,
  "rooms": [
    {
      "id": 1,
      "name": "Studio A",
      "capacity": 20,
      "equipment": "Sound System, Mirrors, Ballet Barre",
      "description": "大型練習室，適合芭蕾和現代舞",
      "hourly_rate": 500.00,
      "is_available": true,
      "created_at": "2025-01-01T12:00:00",
      "updated_at": "2025-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

#### POST /api/rooms
新增教室
- **方法**: POST
- **請求格式**:
```json
{
  "name": "Studio E",
  "capacity": 18,
  "equipment": "Sound System, Mirrors, Air Conditioning",
  "description": "新設立的練習室",
  "hourly_rate": 450.00,
  "is_available": true
}
```

### 5. 課程時間表 (`/api/schedules`)

#### GET /api/schedules
取得所有課程時間表（包含具體日期和教室資訊）
- **方法**: GET
- **回應格式**:
```json
{
  "success": true,
  "schedules": [
    {
      "id": 1,
      "course_id": 1,
      "schedule_date": "2025-01-06",
      "day_of_week": "Monday",
      "start_time": "18:00:00",
      "end_time": "19:30:00",
      "room_id": 1,
      "is_active": true,
      "course_name": "初級芭蕾",
      "level": "beginner",
      "type": "ballet",
      "teacher_name": "張美麗",
      "room_name": "Studio A",
      "room_capacity": 20,
      "created_at": "2025-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

#### POST /api/schedules
新增課程時間表
- **方法**: POST
- **請求格式**:
```json
{
  "course_id": 1,
  "schedule_date": "2025-01-20",
  "start_time": "18:00:00",
  "end_time": "19:30:00",
  "room_id": 1,
  "is_active": true
}
```
- **說明**: 
  - `schedule_date` 必須為 YYYY-MM-DD 格式
  - `day_of_week` 會自動從日期計算得出
  - `room_id` 為教室ID (外鍵)
  - `is_active` 為可選欄位

### 6. 報名管理 (`/api/enrollment`)

#### GET /api/enrollment
取得所有報名記錄
- **方法**: GET

#### POST /api/enrollment
新增報名
- **方法**: POST
- **請求格式**:
```json
{
  "studentName": "陳小明",
  "lesson": {
    "name": "初級芭蕾",
    "time": "18:00-19:30",
    "day": "Monday",
    "teacher": "張美麗",
    "level": "beginner",
    "type": "ballet"
  }
}
```

## 資料庫表格結構

### students (學生表)
- `id`: 主鍵
- `name`: 姓名 (必填)
- `email`: 電子郵件 (唯一)
- `phone`: 電話
- `age`: 年齡
- `emergency_contact`: 緊急聯絡人
- `emergency_phone`: 緊急聯絡電話
- `medical_notes`: 醫療註記
- `remaining_classes`: 剩餘堂數 (預設: 0)
- `membership_expiry`: 會員到期日
- `created_at`: 建立時間
- `updated_at`: 更新時間

### rooms (教室表)
- `id`: 主鍵
- `name`: 教室名稱 (必填，唯一)
- `capacity`: 容納人數
- `equipment`: 設備描述
- `description`: 教室描述
- `hourly_rate`: 時租價格
- `is_available`: 是否可用
- `created_at`: 建立時間
- `updated_at`: 更新時間

### teachers (老師表)
- `id`: 主鍵
- `name`: 姓名 (必填)
- `email`: 電子郵件 (唯一)
- `phone`: 電話
- `experience_years`: 經驗年數
- `bio`: 個人簡介
- `hourly_rate`: 時薪
- `created_at`: 建立時間
- `updated_at`: 更新時間

### styles (風格表)
- `id`: 主鍵
- `name`: 風格名稱 (必填，唯一)
- `description`: 風格描述

### teacher_styles (老師-風格關聯表)
- `teacher_id`: 老師ID (外鍵)
- `style_id`: 風格ID (外鍵)

### courses (課程表)
- `id`: 主鍵
- `name`: 課程名稱 (必填)
- `description`: 課程描述
- `level`: 難度級別 (必填) - beginner, intermediate, advanced
- `type`: 課程類型 (必填) - ballet, jazz, hip-hop, contemporary, etc.
- `duration_minutes`: 課程時長 (分鐘)
- `max_students`: 最大學生數
- `price`: 價格
- `teacher_id`: 老師ID (外鍵)
- `created_at`: 建立時間
- `updated_at`: 更新時間

### course_schedules (課程時間表)
- `id`: 主鍵
- `course_id`: 課程ID (外鍵)
- `schedule_date`: 具體日期 (YYYY-MM-DD)
- `day_of_week`: 星期幾 (自動計算)
- `start_time`: 開始時間
- `end_time`: 結束時間
- `room_id`: 教室ID (外鍵)
- `is_active`: 是否啟用
- `created_at`: 建立時間

### enrollments (報名表)
- `id`: 主鍵
- `student_id`: 學生ID (外鍵)
- `course_id`: 課程ID (外鍵)
- `schedule_id`: 時間表ID (外鍵)
- `student_name`: 學生姓名
- `lesson_name`: 課程名稱
- `lesson_time`: 上課時間
- `lesson_day`: 上課日期
- `lesson_teacher`: 授課老師
- `lesson_level`: 課程級別
- `lesson_type`: 課程類型
- `enrollment_time`: 報名時間
- `status`: 狀態

## 測試方法

1. 啟動 Docker 容器:
```bash
docker-compose up -d
```

2. 運行測試腳本:
```bash
python test_data.py
```

3. 使用 curl 測試 API:
```bash
# 取得所有教室
curl -X GET http://localhost:8001/api/rooms

# 新增教室
curl -X POST http://localhost:8001/api/rooms \
  -H "Content-Type: application/json" \
  -d '{"name":"Studio G","capacity":15,"equipment":"Sound System, Mirrors","description":"多功能練習室","hourly_rate":400.00}'

# 取得所有老師
curl -X GET http://localhost:8001/api/teachers

# 新增學生
curl -X POST http://localhost:8001/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"測試學生","email":"test@example.com","phone":"0912345678","age":25}'

# 新增課程時間表 (使用教室ID)
curl -X POST http://localhost:8001/api/schedules \
  -H "Content-Type: application/json" \
  -d '{"course_id":1,"schedule_date":"2025-01-25","start_time":"18:00:00","end_time":"19:30:00","room_id":1}'

# 查詢特定日期的課程
curl -X GET http://localhost:8001/api/schedules
```

## 特殊功能說明

### 日期自動計算星期
當您新增課程時間表時，系統會自動從 `schedule_date` 計算出對應的 `day_of_week`：
- 輸入: `"schedule_date": "2025-01-20"`
- 自動計算: `"day_of_week": "Monday"`

### 課程時間表排序
課程時間表會按照日期和時間自動排序，方便查看課程安排。
