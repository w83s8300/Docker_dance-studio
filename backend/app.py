from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import mysql.connector
from datetime import datetime
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
            
            # 老師表格
            teachers_table = """
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                specialties TEXT,
                experience_years INT,
                bio TEXT,
                hourly_rate DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # 課程表格
            courses_table = """
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                level VARCHAR(20) NOT NULL,
                type VARCHAR(50) NOT NULL,
                duration_minutes INT DEFAULT 60,
                max_students INT DEFAULT 15,
                price DECIMAL(10,2),
                teacher_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
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
                
                # 轉換 datetime 物件為 ISO 格式字串
                for student in students:
                    for field in ['created_at', 'updated_at']:
                        if student.get(field) and isinstance(student[field], datetime):
                            student[field] = student[field].isoformat()
                
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
                (name, email, phone, age, emergency_contact, emergency_phone, medical_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('age'),
                    data.get('emergency_contact'),
                    data.get('emergency_phone'),
                    data.get('medical_notes')
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
        """取得所有老師"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM teachers ORDER BY created_at DESC")
                teachers = cursor.fetchall()
                
                # 轉換 datetime 物件為 ISO 格式字串
                for teacher in teachers:
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
                
                insert_query = """
                INSERT INTO teachers 
                (name, email, phone, specialties, experience_years, bio, hourly_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('specialties'),
                    data.get('experience_years'),
                    data.get('bio'),
                    data.get('hourly_rate')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                teacher_id = cursor.lastrowid
                
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
                SELECT c.*, t.name as teacher_name, t.email as teacher_email
                FROM courses c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                ORDER BY c.created_at DESC
                """
                cursor.execute(query)
                courses = cursor.fetchall()
                
                # 轉換 datetime 物件為 ISO 格式字串
                for course in courses:
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
                return {'error': '查詢課程失敗'}, 500
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
            
            if not data or 'name' not in data or 'level' not in data or 'type' not in data:
                return {'error': '缺少必要欄位：課程名稱、難度級別、課程類型'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資料庫連接失敗'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO courses 
                (name, description, level, type, duration_minutes, max_students, price, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('description'),
                    data.get('level'),
                    data.get('type'),
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
                SELECT cs.*, c.name as course_name, c.level, c.type, 
                       t.name as teacher_name, r.name as room_name, 
                       r.capacity as room_capacity
                FROM course_schedules cs
                JOIN courses c ON cs.course_id = c.id
                LEFT JOIN teachers t ON c.teacher_id = t.id
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
                return {'error': '查詢課程時間表失敗'}, 500
            finally:
                cursor.close()
                connection.close()

        except Exception as e:
            print(f"查詢課程時間表錯誤: {str(e)}")
            return {'error': '查詢課程時間表失敗'}, 500
    
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
                (course_id, schedule_date, day_of_week, start_time, end_time, room, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('course_id'),
                    data.get('schedule_date'),
                    day_of_week,
                    data.get('start_time'),
                    data.get('end_time'),
                    data.get('room', ''),
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
                return {'error': '新增課程時間表失敗'}, 500
            except ValueError as e:
                print(f"日期格式錯誤: {e}")
                return {'error': '日期格式錯誤，請使用 YYYY-MM-DD 格式'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"新增課程時間表錯誤: {str(e)}")
            return {'error': '新增課程時間表失敗'}, 500

api.add_resource(HelloWorld, '/')
api.add_resource(Enrollment, '/api/enrollment')
api.add_resource(Students, '/api/students')
api.add_resource(Teachers, '/api/teachers')
api.add_resource(Courses, '/api/courses')
api.add_resource(CourseSchedules, '/api/schedules')

if __name__ == '__main__':
    # 初始化資料庫表格
    init_database_tables()
    app.run(debug=True, host='0.0.0.0', port=8001)