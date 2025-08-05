from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date
import os
import time

app = Flask(__name__)
CORS(app)  # 允許跨域請求
api = Api(app)

# 資料庫連接配置
DB_CONFIG = {
    'host': 'db',  # Docker Compose 中的服務名稱
    'port': 3306,
    'user': 'user',
    'password': 'userpass',
    'database': 'testdb',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """取得資料庫連接，包含重試機制"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            return connection
        except mysql.connector.Error as err:
            print(f"資料庫連接嘗試 {attempt + 1}/{max_retries} 失敗: {err}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒後重試...")
                time.sleep(retry_delay)
            else:
                print("資料庫連接失敗，已達最大重試次數")
                return None

def init_database_tables():
    """初始化所有資料庫表格，包含重試機制"""
    print("正在初始化資料庫表格...")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # 學生表格
            students_table = """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                age INT,
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                medical_notes TEXT,
                remaining_classes INT DEFAULT 0 COMMENT '剩餘堂數',
                membership_expiry DATE COMMENT '會員到期日',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # 教室表格
            rooms_table = """
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                capacity INT DEFAULT 20,
                equipment TEXT,
                description TEXT,
                hourly_rate DECIMAL(10,2),
                is_available BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # 老師表格（移除 specialties 欄位）
            teachers_table = """
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                experience_years INT,
                bio TEXT,
                hourly_rate DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """

            # 風格表格
            styles_table = """
            CREATE TABLE IF NOT EXISTS styles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT
            )
            """

            # 老師-風格關聯表
            teacher_styles_table = """
            CREATE TABLE IF NOT EXISTS teacher_styles (
                teacher_id INT NOT NULL,
                style_id INT NOT NULL,
                PRIMARY KEY (teacher_id, style_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
            )
            """
            
            # 課程表格
            courses_table = """
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                level VARCHAR(20) NOT NULL,
                style_id INT,
                duration_minutes INT DEFAULT 60,
                max_students INT DEFAULT 15,
                price DECIMAL(10,2),
                teacher_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
                FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE SET NULL
            )
            """
            
            # 更新課程時間表格
            schedules_table = """
            CREATE TABLE IF NOT EXISTS course_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                schedule_date DATE NOT NULL,
                day_of_week VARCHAR(20) NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                room_id INT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
            )
            """
            
            # 報名表格
            enrollments_table = """
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                course_id INT,
                schedule_id INT,
                student_name VARCHAR(100) NOT NULL,
                lesson_name VARCHAR(100) NOT NULL,
                lesson_time VARCHAR(50) NOT NULL,
                lesson_day VARCHAR(20) NOT NULL,
                lesson_teacher VARCHAR(50) NOT NULL,
                lesson_level VARCHAR(20) NOT NULL,
                lesson_type VARCHAR(50) NOT NULL,
                enrollment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'confirmed',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL,
                FOREIGN KEY (schedule_id) REFERENCES course_schedules(id) ON DELETE SET NULL
            )
            """
            
            # 執行表格建立
            cursor.execute(students_table)
            cursor.execute(rooms_table)
            cursor.execute(teachers_table)
            cursor.execute(styles_table)
            cursor.execute(teacher_styles_table)
            cursor.execute(courses_table)
            cursor.execute(schedules_table)
            cursor.execute(enrollments_table)
            connection.commit()
            print("所有資料庫表格初始化成功")
            
        except mysql.connector.Error as err:
            print(f"建立表格錯誤: {err}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("無法初始化資料庫表格 - 將在執行時重試")

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class Enrollment(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # 驗證必要欄位
            if not data or 'studentName' not in data or 'lesson' not in data:
                return {'error': '缺少必要欄位'}, 400
            
            student_name = data['studentName'].strip()
            lesson = data['lesson']
            
            if not student_name:
                return {'error': '請輸入有效的姓名'}, 400
            
            # 連接資料庫
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                # 插入報名記錄
                insert_query = """
                INSERT INTO enrollments 
                (student_name, lesson_name, lesson_time, lesson_day, 
                 lesson_teacher, lesson_level, lesson_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    student_name,
                    lesson.get('name', ''),
                    lesson.get('time', ''),
                    lesson.get('day', ''),
                    lesson.get('teacher', ''),
                    lesson.get('level', ''),
                    lesson.get('type', '')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                enrollment_id = cursor.lastrowid
                
                print(f"=== 新的課程報名 ===")
                print(f"報名編號: {enrollment_id}")
                print(f"學生姓名: {student_name}")
                print(f"課程名稱: {lesson.get('name')}")
                print(f"上課時間: {lesson.get('day')} {lesson.get('time')}")
                print(f"授課老師: {lesson.get('teacher')}")
                print("==================")
                
                return {
                    'success': True,
                    'message': '報名成功！',
                    'enrollment': {
                        'id': enrollment_id,
                        'studentName': student_name,
                        'lesson': lesson,
                        'enrollmentTime': datetime.now().isoformat()
                    }
                }, 201
                
            except mysql.connector.Error as err:
                print(f"資料庫操作錯誤: {err}")
                return {'error': '報名處理失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"報名處理錯誤: {str(e)}")
            return {'error': '報名處理失敗，請稍後再試'}, 500
    
    def get(self):
        """取得所有報名記錄"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM enrollments ORDER BY enrollment_time DESC")
                enrollments = cursor.fetchall()
                
                # 轉換 datetime 物件為 ISO 格式字串
                for enrollment in enrollments:
                    if enrollment.get('enrollment_time') and isinstance(enrollment['enrollment_time'], datetime):
                        enrollment['enrollment_time'] = enrollment['enrollment_time'].isoformat()
                
                return {
                    'success': True,
                    'enrollments': enrollments,
                    'total': len(enrollments)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢錯誤: {err}")
                return {'error': '查詢失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢錯誤: {str(e)}")
            return {'error': '查詢失敗'}, 500

class Students(Resource):
    def get(self):
        """取得所有學生"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
                students = cursor.fetchall()
                
                # 轉換 datetime 和 date 物件為字串
                for student in students:
                    # 處理 datetime 欄位
                    for field in ['created_at', 'updated_at']:
                        if student.get(field) and isinstance(student[field], datetime):
                            student[field] = student[field].isoformat()
                    
                    # 處理 date 欄位
                    if student.get('membership_expiry') and isinstance(student['membership_expiry'], date):
                        student['membership_expiry'] = student['membership_expiry'].isoformat()
                
                return {
                    'success': True,
                    'students': students,
                    'total': len(students)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢學生錯誤: {err}")
                return {'error': '查詢學生失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢學生錯誤: {str(e)}")
            return {'error': '查詢學生失敗'}, 500
    
    def post(self):
        """新增學生"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺少必要欄位：姓名'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO students 
                (name, email, phone, age, emergency_contact, emergency_phone, medical_notes, remaining_classes, membership_expiry)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('age'),
                    data.get('emergency_contact'),
                    data.get('emergency_phone'),
                    data.get('medical_notes'),
                    data.get('remaining_classes', 0),
                    data.get('membership_expiry')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                student_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '學生新增成功！',
                    'student_id': student_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增學生錯誤: {err}")
                return {'error': '新增學生失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增學生錯誤: {str(e)}")
            return {'error': '新增學生失敗'}, 500

class Teachers(Resource):
    def get(self):
        """取得所有老師及其風格"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                # 查詢所有老師
                cursor.execute("SELECT * FROM teachers ORDER BY created_at DESC")
                teachers = cursor.fetchall()
                
                # 查詢所有老師的風格
                teacher_ids = [teacher['id'] for teacher in teachers]
                if teacher_ids:
                    style_query = """
                    SELECT ts.teacher_id, s.id as style_id, s.name as style_name
                    FROM teacher_styles ts
                    JOIN styles s ON ts.style_id = s.id
                    WHERE ts.teacher_id IN (%s)
                    """ % ', '.join(['%s'] * len(teacher_ids))
                    
                    cursor.execute(style_query, teacher_ids)
                    styles = cursor.fetchall()
                    
                    # 將風格整理到對應的老師物件中
                    teacher_styles = {teacher_id: [] for teacher_id in teacher_ids}
                    for style in styles:
                        teacher_styles[style['teacher_id']].append({
                            'id': style['style_id'],
                            'name': style['style_name']
                        })
                    
                    # 將風格加入老師物件
                    for teacher in teachers:
                        teacher['styles'] = teacher_styles.get(teacher['id'], [])

                # 轉換 datetime 和 Decimal 物件為 ISO 格式字串
                for teacher in teachers:
                    if teacher.get('hourly_rate'):
                        teacher['hourly_rate'] = str(teacher['hourly_rate'])
                    for field in ['created_at', 'updated_at']:
                        if teacher.get(field) and isinstance(teacher[field], datetime):
                            teacher[field] = teacher[field].isoformat()
                
                return {
                    'success': True,
                    'teachers': teachers,
                    'total': len(teachers)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢老師錯誤: {err}")
                return {'error': '查詢老師失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢老師錯誤: {str(e)}")
            return {'error': '查詢老師失敗'}, 500
    
    def post(self):
        """新增老師"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺少必要欄位：姓名'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                # 插入老師基本資料
                insert_teacher_query = """
                INSERT INTO teachers 
                (name, email, phone, experience_years, bio, hourly_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                teacher_values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('experience_years'),
                    data.get('bio'),
                    data.get('hourly_rate')
                )
                
                cursor.execute(insert_teacher_query, teacher_values)
                teacher_id = cursor.lastrowid
                
                # 處理老師與風格的關聯
                style_ids = data.get('style_ids', [])
                if style_ids:
                    insert_style_query = """
                    INSERT INTO teacher_styles (teacher_id, style_id)
                    VALUES (%s, %s)
                    """
                    style_values = [(teacher_id, style_id) for style_id in style_ids]
                    cursor.executemany(insert_style_query, style_values)

                connection.commit()
                
                return {
                    'success': True,
                    'message': '老師新增成功！',
                    'teacher_id': teacher_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增老師錯誤: {err}")
                return {'error': '新增老師失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增老師錯誤: {str(e)}")
            return {'error': '新增老師失敗'}, 500

class Courses(Resource):
    def get(self):
        """取得所有課程（包含老師資訊）"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                SELECT c.*, t.name as teacher_name, t.email as teacher_email, s.name as style_name
                FROM courses c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                LEFT JOIN styles s ON c.style_id = s.id
                ORDER BY c.created_at DESC
                """
                cursor.execute(query)
                courses = cursor.fetchall()
                
                # 轉換 Decimal 和 datetime 物件為可 JSON 序列化的格式
                for course in courses:
                    # 將 price 欄位轉為字串
                    if 'price' in course and course['price'] is not None:
                        course['price'] = str(course['price'])
                    # 轉換 datetime 物件為 ISO 格式字串
                    for field in ['created_at', 'updated_at']:
                        if course.get(field) and isinstance(course[field], datetime):
                            course[field] = course[field].isoformat()
                
                return {
                    'success': True,
                    'courses': courses,
                    'total': len(courses)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢課程錯誤: {err}")
                return {'error': f'查詢課程失敗: {err}'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢課程錯誤: {str(e)}")
            return {'error': '查詢課程失敗'}, 500
    
    def post(self):
        """新增課程"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'level' not in data:
                return {'error': '缺少必要欄位：課程名稱、難度級別'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO courses 
                (name, description, level, style_id, duration_minutes, max_students, price, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('description'),
                    data.get('level'),
                    data.get('style_id'),
                    data.get('duration_minutes', 60),
                    data.get('max_students', 15),
                    data.get('price'),
                    data.get('teacher_id')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                course_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '課程新增成功！',
                    'course_id': course_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增課程錯誤: {err}")
                return {'error': '新增課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增課程錯誤: {str(e)}")
            return {'error': '新增課程失敗'}, 500

class CourseSchedules(Resource):
    def get(self):
        """取得所有課程時間表，支援日期範圍過濾"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500

            try:
                cursor = connection.cursor(dictionary=True)

                # 取得查詢參數
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')

                # 基本查詢語句
                query = """
                SELECT cs.*, c.name as course_name, c.level, s.name as style_name, 
                       t.name as teacher_name, r.name as room_name, 
                       r.capacity as room_capacity
                FROM course_schedules cs
                JOIN courses c ON cs.course_id = c.id
                LEFT JOIN teachers t ON c.teacher_id = t.id
                LEFT JOIN styles s ON c.style_id = s.id
                LEFT JOIN rooms r ON cs.room_id = r.id
                WHERE cs.is_active = TRUE
                """

                # 添加日期範圍過濾條件
                params = []
                if start_date:
                    query += " AND cs.schedule_date >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND cs.schedule_date <= %s"
                    params.append(end_date)

                query += " ORDER BY cs.schedule_date, cs.start_time"

                cursor.execute(query, params)
                schedules = cursor.fetchall()

                # 轉換時間物件為字串
                for schedule in schedules:
                    if schedule.get('schedule_date'):
                        schedule['schedule_date'] = str(schedule['schedule_date'])
                    if schedule.get('start_time'):
                        schedule['start_time'] = str(schedule['start_time'])
                    if schedule.get('end_time'):
                        schedule['end_time'] = str(schedule['end_time'])
                    if schedule.get('created_at') and isinstance(schedule['created_at'], datetime):
                        schedule['created_at'] = schedule['created_at'].isoformat()

                return {
                    'success': True,
                    'schedules': schedules,
                    'total': len(schedules)
                }, 200

            except mysql.connector.Error as err:
                print(f"查詢課程時間表錯誤: {err}")
                return {'error': f'查詢課程時間表失敗: {err}'}, 500
            finally:
                cursor.close()
                connection.close()

        except Exception as e:
            print(f"查詢課程時間表錯誤: {str(e)}")
            return {'error': f'查詢課程時間表失敗: {str(e)}'}, 500

    def post(self):
        """新增課程時間表"""
        try:
            data = request.get_json()
            
            required_fields = ['course_id', 'schedule_date', 'start_time', 'end_time']
            if not data or not all(field in data for field in required_fields):
                return {'error': '缺少必要欄位：course_id, schedule_date, start_time, end_time'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                # 從日期推算星期幾
                from datetime import datetime
                date_obj = datetime.strptime(data['schedule_date'], '%Y-%m-%d')
                day_of_week = date_obj.strftime('%A')  # Monday, Tuesday, etc.
                
                insert_query = """
                INSERT INTO course_schedules 
                (course_id, schedule_date, day_of_week, start_time, end_time, room_id, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('course_id'),
                    data.get('schedule_date'),
                    day_of_week,
                    data.get('start_time'),
                    data.get('end_time'),
                    data.get('room_id'),
                    data.get('is_active', True)
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                schedule_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '課程時間表新增成功！',
                    'schedule_id': schedule_id,
                    'day_of_week': day_of_week
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增課程時間表錯誤: {err}")
                return {'error': f'新增課程時間表失敗: {err}'}, 500
            except ValueError as e:
                print(f"日期格式錯誤: {e}")
                return {'error': '日期格式錯誤，請使用 YYYY-MM-DD 格式'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增課程時間表錯誤: {str(e)}")
            return {'error': '新增課程時間表失敗'}, 500

class Student(Resource):
    def get(self, student_id):
        """取得單一學生"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                student = cursor.fetchone()
                
                if not student:
                    return {'error': '學生未找到'}, 404
                
                # 轉換 datetime 和 date 物件為字串
                for field in ['created_at', 'updated_at']:
                    if student.get(field) and isinstance(student[field], datetime):
                        student[field] = student[field].isoformat()
                
                if student.get('membership_expiry') and isinstance(student['membership_expiry'], date):
                    student['membership_expiry'] = student['membership_expiry'].isoformat()
                
                return {
                    'success': True,
                    'student': student
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢學生錯誤: {err}")
                return {'error': '查詢學生失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢學生錯誤: {str(e)}")
            return {'error': '查詢學生失敗'}, 500

    def put(self, student_id):
        """更新學生資料"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺少更新資料'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'email', 'phone', 'age', 'emergency_contact', 'emergency_phone', 'medical_notes', 'remaining_classes', 'membership_expiry']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒有可更新的欄位'}, 400
                
                update_query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s"
                values.append(student_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '學生未找到或資料未改變'}, 404
                
                return {
                    'success': True,
                    'message': '學生資料更新成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"更新學生錯誤: {err}")
                return {'error': '更新學生失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"更新學生錯誤: {str(e)}")
            return {'error': '更新學生失敗'}, 500

    def delete(self, student_id):
        """刪除學生"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '學生未找到'}, 404
                
                return {
                    'success': True,
                    'message': '學生刪除成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"刪除學生錯誤: {err}")
                return {'error': '刪除學生失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"刪除學生錯誤: {str(e)}")
            return {'error': '刪除學生失敗'}, 500

class Teacher(Resource):
    def get(self, teacher_id):
        """取得單一老師"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
                teacher = cursor.fetchone()
                
                if not teacher:
                    return {'error': '老師未找到'}, 404
                
                # 查詢老師的風格
                style_query = """
                SELECT s.id, s.name
                FROM teacher_styles ts
                JOIN styles s ON ts.style_id = s.id
                WHERE ts.teacher_id = %s
                """
                cursor.execute(style_query, (teacher_id,))
                styles = cursor.fetchall()
                teacher['styles'] = styles
                
                # 轉換 datetime 和 Decimal 物件為字串
                if teacher.get('hourly_rate'):
                    teacher['hourly_rate'] = str(teacher['hourly_rate'])
                for field in ['created_at', 'updated_at']:
                    if teacher.get(field) and isinstance(teacher[field], datetime):
                        teacher[field] = teacher[field].isoformat()
                
                return {
                    'success': True,
                    'teacher': teacher
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢老師錯誤: {err}")
                return {'error': '查詢老師失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢老師錯誤: {str(e)}")
            return {'error': '查詢老師失敗'}, 500

    def put(self, teacher_id):
        """更新老師資料"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺少更新資料'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'email', 'phone', 'experience_years', 'bio', 'hourly_rate']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if update_fields:
                    update_query = f"UPDATE teachers SET {', '.join(update_fields)} WHERE id = %s"
                    update_values = tuple(values) + (teacher_id,)
                    cursor.execute(update_query, update_values)
                
                # 更新老師與風格的關聯
                if 'style_ids' in data:
                    style_ids = data['style_ids']
                    # 先刪除舊的關聯
                    cursor.execute("DELETE FROM teacher_styles WHERE teacher_id = %s", (teacher_id,))
                    # 新增新的關聯
                    if style_ids:
                        insert_style_query = """
                        INSERT INTO teacher_styles (teacher_id, style_id)
                        VALUES (%s, %s)
                        """
                        style_values = [(teacher_id, style_id) for style_id in style_ids]
                        cursor.executemany(insert_style_query, style_values)

                connection.commit()
                
                return {
                    'success': True,
                    'message': '老師資料更新成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"更新老師錯誤: {err}")
                return {'error': '更新老師失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"更新老師錯誤: {str(e)}")
            return {'error': '更新老師失敗'}, 500

    def delete(self, teacher_id):
        """刪除老師"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '老師未找到'}, 404
                
                return {
                    'success': True,
                    'message': '老師刪除成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"刪除老師錯誤: {err}")
                return {'error': '刪除老師失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"刪除老師錯誤: {str(e)}")
            return {'error': '刪除老師失敗'}, 500

class Course(Resource):
    def get(self, course_id):
        """取得單一課程"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                SELECT c.*, t.name as teacher_name, s.name as style_name
                FROM courses c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                LEFT JOIN styles s ON c.style_id = s.id
                WHERE c.id = %s
                """
                cursor.execute(query, (course_id,))
                course = cursor.fetchone()
                
                if not course:
                    return {'error': '課程未找到'}, 404
                
                # 轉換 Decimal 和 datetime 物件為可 JSON 序列化的格式
                if 'price' in course and course['price'] is not None:
                    course['price'] = str(course['price'])
                for field in ['created_at', 'updated_at']:
                    if course.get(field) and isinstance(course[field], datetime):
                        course[field] = course[field].isoformat()
                
                return {
                    'success': True,
                    'course': course
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢課程錯誤: {err}")
                return {'error': '查詢課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢課程錯誤: {str(e)}")
            return {'error': '查詢課程失敗'}, 500

    def put(self, course_id):
        """更新課程資料"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺少更新資料'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒有可更新的欄位'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課程未找到或資料未改變'}, 404
                
                return {
                    'success': True,
                    'message': '課程資料更新成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"更新課程錯誤: {err}")
                return {'error': '更新課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"更新課程錯誤: {str(e)}")
            return {'error': '更新課程失敗'}, 500

    def delete(self, course_id):
        """刪除課程"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課程未找到'}, 404
                
                return {
                    'success': True,
                    'message': '課程刪除成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"刪除課程錯誤: {err}")
                return {'error': '刪除課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"刪除課程錯誤: {str(e)}")
            return {'error': '刪除課程失敗'}, 500

class Course(Resource):
    def get(self, course_id):
        """取得單一課程"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                SELECT c.*, t.name as teacher_name, s.name as style_name
                FROM courses c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                LEFT JOIN styles s ON c.style_id = s.id
                WHERE c.id = %s
                """
                cursor.execute(query, (course_id,))
                course = cursor.fetchone()
                
                if not course:
                    return {'error': '課程未找到'}, 404
                
                # 轉換 Decimal 和 datetime 物件為可 JSON 序列化的格式
                if 'price' in course and course['price'] is not None:
                    course['price'] = str(course['price'])
                for field in ['created_at', 'updated_at']:
                    if course.get(field) and isinstance(course[field], datetime):
                        course[field] = course[field].isoformat()
                
                return {
                    'success': True,
                    'course': course
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢課程錯誤: {err}")
                return {'error': '查詢課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢課程錯誤: {str(e)}")
            return {'error': '查詢課程失敗'}, 500

    def put(self, course_id):
        """更新課程資料"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺少更新資料'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒有可更新的欄位'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課程未找到或資料未改變'}, 404
                
                return {
                    'success': True,
                    'message': '課程資料更新成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"更新課程錯誤: {err}")
                return {'error': '更新課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"更新課程錯誤: {str(e)}")
            return {'error': '更新課程失敗'}, 500

    def delete(self, course_id):
        """刪除課程"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課程未找到'}, 404
                
                return {
                    'success': True,
                    'message': '課程刪除成功！'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"刪除課程錯誤: {err}")
                return {'error': '刪除課程失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"刪除課程錯誤: {str(e)}")
            return {'error': '刪除課程失敗'}, 500

api.add_resource(HelloWorld, '/')
api.add_resource(Enrollment, '/api/enrollment')
api.add_resource(Students, '/api/students')
api.add_resource(Student, '/api/students/<int:student_id>') # 新增的學生單一資源
api.add_resource(Teachers, '/api/teachers')
api.add_resource(Teacher, '/api/teachers/<int:teacher_id>')
api.add_resource(Courses, '/api/courses')
api.add_resource(Course, '/api/courses/<int:course_id>')
api.add_resource(CourseSchedules, '/api/schedules')

class Styles(Resource):
    def get(self):
        """取得所有風格"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM styles ORDER BY id DESC")
                styles = cursor.fetchall()
                
                return {
                    'success': True,
                    'styles': styles,
                    'total': len(styles)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢風格錯誤: {err}")
                return {'error': '查詢風格失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢風格錯誤: {str(e)}")
            return {'error': '查詢風格失敗'}, 500
    
    def post(self):
        """新增風格"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺少必要欄位：風格名稱'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO styles (name, description)
                VALUES (%s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('description')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                style_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '風格新增成功！',
                    'style_id': style_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增風格錯誤: {err}")
                return {'error': '新增風格失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增風格錯誤: {str(e)}")
            return {'error': '新增風格失敗'}, 500

api.add_resource(Styles, '/api/styles')

class Rooms(Resource):
    def get(self):
        """取得所有教室"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '查詢教室失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms ORDER BY id DESC")
                rooms = cursor.fetchall()

                # 轉換 Decimal 物件為字串
                for room in rooms:
                    if room.get('hourly_rate'):
                        room['hourly_rate'] = str(room['hourly_rate'])
                    # 轉換 datetime 物件為 ISO 格式字串
                    for field in ['created_at', 'updated_at']:
                        if room.get(field) and isinstance(room[field], datetime):
                            room[field] = room[field].isoformat()
                
                return {
                    'success': True,
                    'rooms': rooms,
                    'total': len(rooms)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"查詢教室錯誤: {err}")
                return {'error': '查詢教室失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"查詢教室錯誤: {str(e)}")
            return {'error': '查詢教室失敗'}, 500

    def post(self):
        """新增教室"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺少必要欄位：教室名稱'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO rooms (name, capacity, equipment, description, hourly_rate, is_available)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('capacity'),
                    data.get('equipment'),
                    data.get('description'),
                    data.get('hourly_rate'),
                    data.get('is_available', True)
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                room_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '教室新增成功！',
                    'room_id': room_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"新增教室錯誤: {err}")
                return {'error': '新增教室失敗'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增教室錯誤: {str(e)}")
            return {'error': '新增教室失敗'}, 500

api.add_resource(Rooms, '/api/rooms')



if __name__ == '__main__':
    # 初始化資料庫表格
    init_database_tables()
    app.run(debug=True, host='0.0.0.0', port=8001)