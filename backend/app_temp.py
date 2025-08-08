from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date
import os
import time

app = Flask(__name__)
CORS(app)  # ?�許跨�?請�?
api = Api(app)

# 資�?庫�?��?�置
DB_CONFIG = {
    'host': 'db',  # Docker Compose 中�??��??�稱
    'port': 3306,
    'user': 'user',
    'password': 'userpass',
    'database': 'testdb',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """?��?資�?庫�?��，�??��?試�???""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            return connection
        except mysql.connector.Error as err:
            print(f"資�?庫�?��?�試 {attempt + 1}/{max_retries} 失�?: {err}")
            if attempt < max_retries - 1:
                print(f"等�? {retry_delay} 秒�??�試...")
                time.sleep(retry_delay)
            else:
                print("資�?庫�?��失�?，已?��?大�?試次??)
                return None

def init_database_tables():
    """?��??��??��??�庫表格，�??��?試�???""
    print("�?��?��??��??�庫表格...")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # 學�?表格
            students_table = """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                date_of_birth DATE,
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                medical_notes TEXT,
                remaining_classes INT DEFAULT 0 COMMENT '?��??�數',
                membership_expiry DATE COMMENT '?�員?��???,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # ?�室表格
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
            
            # ?�師表格（移??specialties 欄�?�?            teachers_table = """
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
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

            # ?�師-風格?�聯�?            teacher_styles_table = """
            CREATE TABLE IF NOT EXISTS teacher_styles (
                teacher_id INT NOT NULL,
                style_id INT NOT NULL,
                PRIMARY KEY (teacher_id, style_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
            )
            """
            
            # 課�?表格
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
            
            # ?�新課�??��?表格
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
            
            # ?��?表格
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
            
            # ?��?表格建�?
            cursor.execute(students_table)
            cursor.execute(rooms_table)
            cursor.execute(teachers_table)
            cursor.execute(styles_table)
            cursor.execute(teacher_styles_table)
            cursor.execute(courses_table)
            cursor.execute(schedules_table)
            cursor.execute(enrollments_table)
            connection.commit()
            print("?�?��??�庫表格?��??��???)
            
        except mysql.connector.Error as err:
            print(f"建�?表格?�誤: {err}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("?��??��??��??�庫表格 - 將在?��??��?�?)

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class Enrollment(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # 驗�?必�?欄�?
            if not data or 'studentName' not in data or 'lesson' not in data:
                return {'error': '缺�?必�?欄�?'}, 400
            
            student_name = data['studentName'].strip()
            lesson = data['lesson']
            
            if not student_name:
                return {'error': '請輸?��??��?姓�?'}, 400
            
            # ??��資�?�?            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                # ?�查詢學?�是?��??�並?��??��??�數
                student_query = "SELECT id, name, remaining_classes FROM students WHERE name = %s"
                cursor.execute(student_query, (student_name,))
                student = cursor.fetchone()
                
                if not student:
                    return {'error': f'?�無學�??�{student_name}?��?請至櫃檯辦�??�員後�??��??��?'}, 400
                
                # 檢查?��??�數
                remaining_classes = student['remaining_classes'] or 0
                if remaining_classes <= 0:
                    return {'error': f'?��??��??�數不足（目?�剩餘�?{remaining_classes}?��?，�??��?檯儲?��??�進�??��?'}, 400
                
                # ?��?事�?
                cursor.execute("START TRANSACTION")
                
                # ??��一?�課
                new_remaining_classes = remaining_classes - 1
                update_query = "UPDATE students SET remaining_classes = %s WHERE id = %s"
                cursor.execute(update_query, (new_remaining_classes, student['id']))
                
                # ?�入?��?記�?
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
                
                # ?�交事�?
                connection.commit()
                
                enrollment_id = cursor.lastrowid
                
                print(f"=== ?��?課�??��? ===")
                print(f"?��?編�?: {enrollment_id}")
                print(f"學�?姓�?: {student_name}")
                print(f"課�??�稱: {lesson.get('name')}")
                print(f"上課?��?: {lesson.get('day')} {lesson.get('time')}")
                print(f"?�課?�師: {lesson.get('teacher')}")
                print(f"??��?��??? {remaining_classes}")
                print(f"??��後�??? {new_remaining_classes}")
                print("==================")
                
                return {
                    'success': True,
                    'message': '?��??��?�?,
                    'enrollment': {
                        'id': enrollment_id,
                        'studentName': student_name,
                        'lesson': lesson,
                        'enrollmentTime': datetime.now().isoformat(),
                        'remainingClasses': new_remaining_classes,
                        'usedClasses': 1
                    }
                }, 201
                
            except mysql.connector.Error as err:
                print(f"資�?庫�?作錯�? {err}")
                # ?�滾事�?
                connection.rollback()
                return {'error': '?��??��?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��??��??�誤: {str(e)}")
            return {'error': '?��??��?失�?，�?稍�??�試'}, 500
    
    def get(self):
        """?��??�?�報?��???""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM enrollments ORDER BY enrollment_time DESC")
                enrollments = cursor.fetchall()
                
                # 轉�? datetime ?�件??ISO ?��?字串
                for enrollment in enrollments:
                    if enrollment.get('enrollment_time') and isinstance(enrollment['enrollment_time'], datetime):
                        enrollment['enrollment_time'] = enrollment['enrollment_time'].isoformat()
                
                return {
                    'success': True,
                    'enrollments': enrollments,
                    'total': len(enrollments)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢?�誤: {err}")
                return {'error': '?�詢失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢?�誤: {str(e)}")
            return {'error': '?�詢失�?'}, 500

class Students(Resource):
    def get(self):
        """?��??�?�學??""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                search_name = request.args.get('name')
                
                query = "SELECT * FROM students"
                params = []
                
                if search_name:
                    query += " WHERE name LIKE %s"
                    params.append(f"%{search_name}%")
                    
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                students = cursor.fetchall()
                
                # 轉�? datetime ??date ?�件?��?�?                for student in students:
                    # ?��? datetime 欄�?
                    for field in ['created_at', 'updated_at']:
                        if student.get(field) and isinstance(student[field], datetime):
                            student[field] = student[field].isoformat()
                    
                    # ?��? date 欄�?
                    for field in ['membership_expiry', 'date_of_birth']:
                        if student.get(field) and isinstance(student[field], date):
                            student[field] = student[field].isoformat()
                
                return {
                    'success': True,
                    'students': students,
                    'total': len(students)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢學�??�誤: {err}")
                return {'error': '?�詢學�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢學�??�誤: {str(e)}")
            return {'error': '?�詢學�?失�?'}, 500
    
    def post(self):
        """?��?學�?"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺�?必�?欄�?：�???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO students 
                (name, email, phone, date_of_birth, emergency_contact, emergency_phone, medical_notes, remaining_classes, membership_expiry)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('date_of_birth'),
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
                    'message': '學�??��??��?�?,
                    'student_id': student_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��?學�??�誤: {err}")
                return {'error': '?��?學�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��?學�??�誤: {str(e)}")
            return {'error': '?��?學�?失�?'}, 500

class Teachers(Resource):
    def get(self):
        """?��??�?�老師?�其風格"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                search_name = request.args.get('name')
                
                # ?�詢?�?�老師
                query = "SELECT * FROM teachers"
                params = []
                
                if search_name:
                    query += " WHERE name LIKE %s"
                    params.append(f"%{search_name}%")
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                teachers = cursor.fetchall()
                
                # ?�詢?�?�老師?�風??                teacher_ids = [teacher['id'] for teacher in teachers]
                if teacher_ids:
                    style_query = """
                    SELECT ts.teacher_id, s.id as style_id, s.name as style_name
                    FROM teacher_styles ts
                    JOIN styles s ON ts.style_id = s.id
                    WHERE ts.teacher_id IN (%s)
                    """ % ', '.join(['%s'] * len(teacher_ids))
                    
                    cursor.execute(style_query, teacher_ids)
                    styles = cursor.fetchall()
                    
                    # 將風?�整?�到對�??�老師?�件�?                    teacher_styles = {teacher_id: [] for teacher_id in teacher_ids}
                    for style in styles:
                        teacher_styles[style['teacher_id']].append({
                            'id': style['style_id'],
                            'name': style['style_name']
                        })
                    
                    # 將風?��??�老師?�件
                    for teacher in teachers:
                        teacher['styles'] = teacher_styles.get(teacher['id'], [])

                # 轉�? datetime ??Decimal ?�件??ISO ?��?字串
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
                print(f"?�詢?�師?�誤: {err}")
                return {'error': '?�詢?�師失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢?�師?�誤: {str(e)}")
            return {'error': '?�詢?�師失�?'}, 500
    
    def post(self):
        """?��??�師"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺�?必�?欄�?：�???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                # ?�入?�師?�本資�?
                insert_teacher_query = """
                INSERT INTO teachers 
                (name, email, phone, bio, hourly_rate)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                teacher_values = (
                    data.get('name'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('bio'),
                    data.get('hourly_rate')
                )
                
                cursor.execute(insert_teacher_query, teacher_values)
                teacher_id = cursor.lastrowid
                
                # ?��??�師?�風?��??�聯
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
                    'message': '?�師?��??��?�?,
                    'teacher_id': teacher_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��??�師?�誤: {err}")
                return {'error': '?��??�師失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��??�師?�誤: {str(e)}")
            return {'error': '?��??�師失�?'}, 500

class Courses(Resource):
    def get(self):
        """?��??�?�課程�??�含?�師資�?�?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                
                # 轉�? Decimal ??datetime ?�件?�可 JSON 序�??��??��?
                for course in courses:
                    # �?price 欄�?轉為字串
                    if 'price' in course and course['price'] is not None:
                        course['price'] = str(course['price'])
                    # 轉�? datetime ?�件??ISO ?��?字串
                    for field in ['created_at', 'updated_at']:
                        if course.get(field) and isinstance(course[field], datetime):
                            course[field] = course[field].isoformat()
                
                return {
                    'success': True,
                    'courses': courses,
                    'total': len(courses)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢課�??�誤: {err}")
                return {'error': f'?�詢課�?失�?: {err}'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢課�??�誤: {str(e)}")
            return {'error': '?�詢課�?失�?'}, 500
    
    def post(self):
        """?��?課�?"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'level' not in data:
                return {'error': '缺�?必�?欄�?：課程�?稱、難度�???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                insert_query = """
                INSERT INTO courses 
                (name, description, level, style_id, duration_minutes, max_students, price, classes_required, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('description'),
                    data.get('level'),
                    data.get('style_id'),
                    data.get('duration_minutes', 60),
                    data.get('max_students', 15),
                    data.get('price'),
                    data.get('classes_required', 1),
                    data.get('teacher_id')
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                course_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '課�??��??��?�?,
                    'course_id': course_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��?課�??�誤: {err}")
                return {'error': '?��?課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��?課�??�誤: {str(e)}")
            return {'error': '?��?課�?失�?'}, 500

class CourseSchedules(Resource):
    def get(self):
        """?��??�?�課程�??�表，支?�日?��??��?�?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500

            try:
                cursor = connection.cursor(dictionary=True)

                # ?��??�詢?�數
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')

                # ?�本?�詢語句
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

                # 添�??��?範�??�濾條件
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

                # 轉�??��??�件?��?�?                for schedule in schedules:
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
                print(f"?�詢課�??��?表錯�? {err}")
                return {'error': f'?�詢課�??��?表失?? {err}'}, 500
            finally:
                cursor.close()
                connection.close()

        except Exception as e:
            print(f"?�詢課�??��?表錯�? {str(e)}")
            return {'error': f'?�詢課�??��?表失?? {str(e)}'}, 500

    def post(self):
        """?��?課�??��?�?""
        try:
            data = request.get_json()
            
            required_fields = ['course_id', 'schedule_date', 'start_time', 'end_time']
            if not data or not all(field in data for field in required_fields):
                return {'error': '缺�?必�?欄�?：course_id, schedule_date, start_time, end_time'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                # 從日?�推算�??�幾
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
                    'message': '課�??��?表新增�??��?',
                    'schedule_id': schedule_id,
                    'day_of_week': day_of_week
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��?課�??��?表錯�? {err}")
                return {'error': f'?��?課�??��?表失?? {err}'}, 500
            except ValueError as e:
                print(f"?��??��??�誤: {e}")
                return {'error': '?��??��??�誤，�?使用 YYYY-MM-DD ?��?'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��?課�??��?表錯�? {str(e)}")
            return {'error': '?��?課�??��?表失??}, 500

class Student(Resource):
    def get(self, student_id):
        """?��??��?學�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                student = cursor.fetchone()
                
                if not student:
                    return {'error': '學�??�找??}, 404
                
                # 轉�? datetime ??date ?�件?��?�?                for field in ['created_at', 'updated_at']:
                    if student.get(field) and isinstance(student[field], datetime):
                        student[field] = student[field].isoformat()
                
                if student.get('membership_expiry') and isinstance(student['membership_expiry'], date):
                    student['membership_expiry'] = student['membership_expiry'].isoformat()
                
                return {
                    'success': True,
                    'student': student
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢學�??�誤: {err}")
                return {'error': '?�詢學�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢學�??�誤: {str(e)}")
            return {'error': '?�詢學�?失�?'}, 500

    def put(self, student_id):
        """?�新學�?資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'email', 'phone', 'date_of_birth', 'emergency_contact', 'emergency_phone', 'medical_notes', 'remaining_classes', 'membership_expiry']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                update_query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s"
                values.append(student_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '學�??�找?��?資�??�改�?}, 404
                
                return {
                    'success': True,
                    'message': '學�?資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新學�??�誤: {err}")
                return {'error': '?�新學�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新學�??�誤: {str(e)}")
            return {'error': '?�新學�?失�?'}, 500

    def delete(self, student_id):
        """?�除學�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '學�??�找??}, 404
                
                return {
                    'success': True,
                    'message': '學�??�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除學�??�誤: {err}")
                return {'error': '?�除學�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除學�??�誤: {str(e)}")
            return {'error': '?�除學�?失�?'}, 500

class Teacher(Resource):
    def get(self, teacher_id):
        """?��??��??�師"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
                teacher = cursor.fetchone()
                
                if not teacher:
                    return {'error': '?�師?�找??}, 404
                
                # ?�詢?�師?�風??                style_query = """
                SELECT s.id, s.name
                FROM teacher_styles ts
                JOIN styles s ON ts.style_id = s.id
                WHERE ts.teacher_id = %s
                """
                cursor.execute(style_query, (teacher_id,))
                styles = cursor.fetchall()
                teacher['styles'] = styles
                
                # 轉�? datetime ??Decimal ?�件?��?�?                if teacher.get('hourly_rate'):
                    teacher['hourly_rate'] = str(teacher['hourly_rate'])
                for field in ['created_at', 'updated_at']:
                    if teacher.get(field) and isinstance(teacher[field], datetime):
                        teacher[field] = teacher[field].isoformat()
                
                return {
                    'success': True,
                    'teacher': teacher
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢?�師?�誤: {err}")
                return {'error': '?�詢?�師失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢?�師?�誤: {str(e)}")
            return {'error': '?�詢?�師失�?'}, 500

    def put(self, teacher_id):
        """?�新?�師資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'email', 'phone', 'bio', 'hourly_rate']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if update_fields:
                    update_query = f"UPDATE teachers SET {', '.join(update_fields)} WHERE id = %s"
                    update_values = tuple(values) + (teacher_id,)
                    cursor.execute(update_query, update_values)
                
                # ?�新?�師?�風?��??�聯
                if 'style_ids' in data:
                    style_ids = data['style_ids']
                    # ?�刪?��??��???                    cursor.execute("DELETE FROM teacher_styles WHERE teacher_id = %s", (teacher_id,))
                    # ?��??��??�聯
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
                    'message': '?�師資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新?�師?�誤: {err}")
                return {'error': '?�新?�師失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新?�師?�誤: {str(e)}")
            return {'error': '?�新?�師失�?'}, 500

    def delete(self, teacher_id):
        """?�除?�師"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?�師?�找??}, 404
                
                return {
                    'success': True,
                    'message': '?�師?�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除?�師?�誤: {err}")
                return {'error': '?�除?�師失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除?�師?�誤: {str(e)}")
            return {'error': '?�除?�師失�?'}, 500

class Course(Resource):
    def get(self, course_id):
        """?��??��?課�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                    return {'error': '課�??�找??}, 404
                
                # 轉�? Decimal ??datetime ?�件?�可 JSON 序�??��??��?
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
                print(f"?�詢課�??�誤: {err}")
                return {'error': '?�詢課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢課�??�誤: {str(e)}")
            return {'error': '?�詢課�?失�?'}, 500

    def put(self, course_id):
        """?�新課�?資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'classes_required', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??�找?��?資�??�改�?}, 404
                
                return {
                    'success': True,
                    'message': '課�?資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新課�??�誤: {err}")
                return {'error': '?�新課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新課�??�誤: {str(e)}")
            return {'error': '?�新課�?失�?'}, 500

    def delete(self, course_id):
        """?�除課�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??�找??}, 404
                
                return {
                    'success': True,
                    'message': '課�??�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除課�??�誤: {err}")
                return {'error': '?�除課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除課�??�誤: {str(e)}")
            return {'error': '?�除課�?失�?'}, 500

class Course(Resource):
    def get(self, course_id):
        """?��??��?課�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                    return {'error': '課�??�找??}, 404
                
                # 轉�? Decimal ??datetime ?�件?�可 JSON 序�??��??��?
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
                print(f"?�詢課�??�誤: {err}")
                return {'error': '?�詢課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢課�??�誤: {str(e)}")
            return {'error': '?�詢課�?失�?'}, 500

    def put(self, course_id):
        """?�新課�?資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'classes_required', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??�找?��?資�??�改�?}, 404
                
                return {
                    'success': True,
                    'message': '課�?資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新課�??�誤: {err}")
                return {'error': '?�新課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新課�??�誤: {str(e)}")
            return {'error': '?�新課�?失�?'}, 500

    def delete(self, course_id):
        """?�除課�?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??�找??}, 404
                
                return {
                    'success': True,
                    'message': '課�??�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除課�??�誤: {err}")
                return {'error': '?�除課�?失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除課�??�誤: {str(e)}")
            return {'error': '?�除課�?失�?'}, 500

api.add_resource(HelloWorld, '/')
api.add_resource(Enrollment, '/api/enrollment')
api.add_resource(Students, '/api/students')
api.add_resource(Student, '/api/students/<int:student_id>') # ?��??�學?�單一資�?
api.add_resource(Teachers, '/api/teachers')
api.add_resource(Teacher, '/api/teachers/<int:teacher_id>')
api.add_resource(Courses, '/api/courses')
api.add_resource(Course, '/api/courses/<int:course_id>')
api.add_resource(CourseSchedules, '/api/schedules')

class CourseSchedule(Resource):
    def get(self, schedule_id):
        """?��??��?課�??��?�?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                query = """
                SELECT cs.*, c.name as course_name, c.level, s.name as style_name, 
                       t.name as teacher_name, r.name as room_name, 
                       r.capacity as room_capacity
                FROM course_schedules cs
                JOIN courses c ON cs.course_id = c.id
                LEFT JOIN teachers t ON c.teacher_id = t.id
                LEFT JOIN styles s ON c.style_id = s.id
                LEFT JOIN rooms r ON cs.room_id = r.id
                WHERE cs.id = %s
                """
                cursor.execute(query, (schedule_id,))
                schedule = cursor.fetchone()
                
                if not schedule:
                    return {'error': '課�??��?表未?�到'}, 404
                
                # 轉�??��??�件?��?�?                if schedule.get('schedule_date'):
                    schedule['schedule_date'] = str(schedule['schedule_date'])
                if schedule.get('start_time'):
                    schedule['start_time'] = str(schedule['start_time'])
                if schedule.get('end_time'):
                    schedule['end_time'] = str(schedule['end_time'])
                if schedule.get('created_at') and isinstance(schedule['created_at'], datetime):
                    schedule['created_at'] = schedule['created_at'].isoformat()
                
                return {
                    'success': True,
                    'schedule': schedule
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢課�??��?表錯�? {err}")
                return {'error': '?�詢課�??��?表失??}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢課�??��?表錯�? {str(e)}")
            return {'error': '?�詢課�??��?表失??}, 500

    def put(self, schedule_id):
        """?�新課�??��?表�???""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['course_id', 'schedule_date', 'start_time', 'end_time', 'room_id', 'is_active']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                # 從日?�推算�??�幾
                if 'schedule_date' in data:
                    from datetime import datetime
                    date_obj = datetime.strptime(data['schedule_date'], '%Y-%m-%d')
                    day_of_week = date_obj.strftime('%A')
                    update_fields.append("day_of_week = %s")
                    values.append(day_of_week)

                update_query = f"UPDATE course_schedules SET {', '.join(update_fields)} WHERE id = %s"
                values.append(schedule_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??��?表未?�到?��??�未?��?'}, 404
                
                return {
                    'success': True,
                    'message': '課�??��?表�??�更?��??��?'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新課�??��?表錯�? {err}")
                return {'error': '?�新課�??��?表失??}, 500
            except ValueError as e:
                print(f"?��??��??�誤: {e}")
                return {'error': '?��??��??�誤，�?使用 YYYY-MM-DD ?��?'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新課�??��?表錯�? {str(e)}")
            return {'error': '?�新課�??��?表失??}, 500

    def delete(self, schedule_id):
        """?�除課�??��?�?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM course_schedules WHERE id = %s", (schedule_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '課�??��?表未?�到'}, 404
                
                return {
                    'success': True,
                    'message': '課�??��?表刪?��??��?'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除課�??��?表錯�? {err}")
                return {'error': '?�除課�??��?表失??}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除課�??��?表錯�? {str(e)}")
            return {'error': '?�除課�??��?表失??}, 500

api.add_resource(CourseSchedule, '/api/schedules/<int:schedule_id>')

class Styles(Resource):
    def get(self):
        """?��??�?�風??""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                print(f"?�詢風格?�誤: {err}")
                return {'error': '?�詢風格失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢風格?�誤: {str(e)}")
            return {'error': '?�詢風格失�?'}, 500
    
    def post(self):
        """?��?風格"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺�?必�?欄�?：風?��?�?}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                    'message': '風格?��??��?�?,
                    'style_id': style_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��?風格?�誤: {err}")
                return {'error': '?��?風格失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��?風格?�誤: {str(e)}")
            return {'error': '?��?風格失�?'}, 500

api.add_resource(Styles, '/api/styles')

class Style(Resource):
    def get(self, style_id):
        """?��??��?風格"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM styles WHERE id = %s", (style_id,))
                style = cursor.fetchone()
                
                if not style:
                    return {'error': '風格?�找??}, 404
                
                return {
                    'success': True,
                    'style': style
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢風格?�誤: {err}")
                return {'error': '?�詢風格失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢風格?�誤: {str(e)}")
            return {'error': '?�詢風格失�?'}, 500

    def put(self, style_id):
        """?�新風格資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                update_query = f"UPDATE styles SET {', '.join(update_fields)} WHERE id = %s"
                values.append(style_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '風格?�找?��?資�??�改�?}, 404
                
                return {
                    'success': True,
                    'message': '風格資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新風格?�誤: {err}")
                return {'error': '?�新風格失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新風格?�誤: {str(e)}")
            return {'error': '?�新風格失�?'}, 500

    def delete(self, style_id):
        """?�除風格"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM styles WHERE id = %s", (style_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '風格?�找??}, 404
                
                return {
                    'success': True,
                    'message': '風格?�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除風格?�誤: {err}")
                return {'error': '?�除風格失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除風格?�誤: {str(e)}")
            return {'error': '?�除風格失�?'}, 500

api.add_resource(Style, '/api/styles/<int:style_id>')

class Rooms(Resource):
    def get(self):
        """?��??�?��?�?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '?�詢?�室失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms ORDER BY id DESC")
                rooms = cursor.fetchall()

                # 轉�? Decimal ?�件?��?�?                for room in rooms:
                    if room.get('hourly_rate'):
                        room['hourly_rate'] = str(room['hourly_rate'])
                    # 轉�? datetime ?�件??ISO ?��?字串
                    for field in ['created_at', 'updated_at']:
                        if room.get(field) and isinstance(room[field], datetime):
                            room[field] = room[field].isoformat()
                
                return {
                    'success': True,
                    'rooms': rooms,
                    'total': len(rooms)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢?�室?�誤: {err}")
                return {'error': '?�詢?�室失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢?�室?�誤: {str(e)}")
            return {'error': '?�詢?�室失�?'}, 500

    def post(self):
        """?��??�室"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': '缺�?必�?欄�?：�?室�?�?}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
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
                    'message': '?�室?��??��?�?,
                    'room_id': room_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?��??�室?�誤: {err}")
                return {'error': '?��??�室失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?��??�室?�誤: {str(e)}")
            return {'error': '?��??�室失�?'}, 500

api.add_resource(Rooms, '/api/rooms')

class Room(Resource):
    def get(self, room_id):
        """?��??��??�室"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
                room = cursor.fetchone()
                
                if not room:
                    return {'error': '?�室?�找??}, 404
                
                # 轉�? Decimal ??datetime
                if room.get('hourly_rate') is not None:
                    room['hourly_rate'] = str(room['hourly_rate'])
                for field in ['created_at', 'updated_at']:
                    if room.get(field) and isinstance(room[field], datetime):
                        room[field] = room[field].isoformat()
                
                return {
                    'success': True,
                    'room': room
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�詢?�室?�誤: {err}")
                return {'error': '?�詢?�室失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�詢?�室?�誤: {str(e)}")
            return {'error': '?�詢?�室失�?'}, 500

    def put(self, room_id):
        """?�新?�室資�?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': '缺�??�新資�?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'capacity', 'equipment', 'description', 'hourly_rate', 'is_available']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': '沒�??�更?��?欄�?'}, 400
                
                update_query = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = %s"
                values.append(room_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?�室?�找?��?資�??�改�?}, 404
                
                return {
                    'success': True,
                    'message': '?�室資�??�新?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�新?�室?�誤: {err}")
                return {'error': '?�新?�室失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�新?�室?�誤: {str(e)}")
            return {'error': '?�新?�室失�?'}, 500

    def delete(self, room_id):
        """?�除?�室"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '資�?庫�?��失�?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?�室?�找??}, 404
                
                return {
                    'success': True,
                    'message': '?�室?�除?��?�?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?�除?�室?�誤: {err}")
                return {'error': '?�除?�室失�?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?�除?�室?�誤: {str(e)}")
            return {'error': '?�除?�室失�?'}, 500

api.add_resource(Room, '/api/rooms/<int:room_id>')



if __name__ == '__main__':
    # ?��??��??�庫表格
    init_database_tables()
    app.run(debug=True, host='0.0.0.0', port=8001)
