from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date
import os
import time

app = Flask(__name__)
CORS(app)  # ?è¨±è·¨å?è«‹æ?
api = Api(app)

# è³‡æ?åº«é€?¥?ç½®
DB_CONFIG = {
    'host': 'db',  # Docker Compose ä¸­ç??å??ç¨±
    'port': 3306,
    'user': 'user',
    'password': 'userpass',
    'database': 'testdb',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """?–å?è³‡æ?åº«é€?¥ï¼Œå??«é?è©¦æ???""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            return connection
        except mysql.connector.Error as err:
            print(f"è³‡æ?åº«é€?¥?—è©¦ {attempt + 1}/{max_retries} å¤±æ?: {err}")
            if attempt < max_retries - 1:
                print(f"ç­‰å? {retry_delay} ç§’å??è©¦...")
                time.sleep(retry_delay)
            else:
                print("è³‡æ?åº«é€?¥å¤±æ?ï¼Œå·²?”æ?å¤§é?è©¦æ¬¡??)
                return None

def init_database_tables():
    """?å??–æ??‰è??™åº«è¡¨æ ¼ï¼Œå??«é?è©¦æ???""
    print("æ­?œ¨?å??–è??™åº«è¡¨æ ¼...")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # å­¸ç?è¡¨æ ¼
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
                remaining_classes INT DEFAULT 0 COMMENT '?©é??‚æ•¸',
                membership_expiry DATE COMMENT '?ƒå“¡?°æ???,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # ?™å®¤è¡¨æ ¼
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
            
            # ?å¸«è¡¨æ ¼ï¼ˆç§»??specialties æ¬„ä?ï¼?            teachers_table = """
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

            # é¢¨æ ¼è¡¨æ ¼
            styles_table = """
            CREATE TABLE IF NOT EXISTS styles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT
            )
            """

            # ?å¸«-é¢¨æ ¼?œè¯è¡?            teacher_styles_table = """
            CREATE TABLE IF NOT EXISTS teacher_styles (
                teacher_id INT NOT NULL,
                style_id INT NOT NULL,
                PRIMARY KEY (teacher_id, style_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
            )
            """
            
            # èª²ç?è¡¨æ ¼
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
            
            # ?´æ–°èª²ç??‚é?è¡¨æ ¼
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
            
            # ?±å?è¡¨æ ¼
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
            
            # ?·è?è¡¨æ ¼å»ºç?
            cursor.execute(students_table)
            cursor.execute(rooms_table)
            cursor.execute(teachers_table)
            cursor.execute(styles_table)
            cursor.execute(teacher_styles_table)
            cursor.execute(courses_table)
            cursor.execute(schedules_table)
            cursor.execute(enrollments_table)
            connection.commit()
            print("?€?‰è??™åº«è¡¨æ ¼?å??–æ???)
            
        except mysql.connector.Error as err:
            print(f"å»ºç?è¡¨æ ¼?¯èª¤: {err}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("?¡æ??å??–è??™åº«è¡¨æ ¼ - å°‡åœ¨?·è??‚é?è©?)

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class Enrollment(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # é©—è?å¿…è?æ¬„ä?
            if not data or 'studentName' not in data or 'lesson' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?'}, 400
            
            student_name = data['studentName'].strip()
            lesson = data['lesson']
            
            if not student_name:
                return {'error': 'è«‹è¼¸?¥æ??ˆç?å§“å?'}, 400
            
            # ??¥è³‡æ?åº?            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                # ?ˆæŸ¥è©¢å­¸?Ÿæ˜¯?¦å??¨ä¸¦?–å??©é??‚æ•¸
                student_query = "SELECT id, name, remaining_classes FROM students WHERE name = %s"
                cursor.execute(student_query, (student_name,))
                student = cursor.fetchone()
                
                if not student:
                    return {'error': f'?¥ç„¡å­¸ç??Œ{student_name}?ï?è«‹è‡³æ«ƒæª¯è¾¦ç??ƒå“¡å¾Œå??²è??±å?'}, 400
                
                # æª¢æŸ¥?©é??‚æ•¸
                remaining_classes = student['remaining_classes'] or 0
                if remaining_classes <= 0:
                    return {'error': f'?¨ç??©é??‚æ•¸ä¸è¶³ï¼ˆç›®?å‰©é¤˜ï?{remaining_classes}?‚ï?ï¼Œè??³æ?æª¯å„²?¼å??é€²è??±å?'}, 400
                
                # ?‹å?äº‹å?
                cursor.execute("START TRANSACTION")
                
                # ??™¤ä¸€?‚èª²
                new_remaining_classes = remaining_classes - 1
                update_query = "UPDATE students SET remaining_classes = %s WHERE id = %s"
                cursor.execute(update_query, (new_remaining_classes, student['id']))
                
                # ?’å…¥?±å?è¨˜é?
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
                
                # ?äº¤äº‹å?
                connection.commit()
                
                enrollment_id = cursor.lastrowid
                
                print(f"=== ?°ç?èª²ç??±å? ===")
                print(f"?±å?ç·¨è?: {enrollment_id}")
                print(f"å­¸ç?å§“å?: {student_name}")
                print(f"èª²ç??ç¨±: {lesson.get('name')}")
                print(f"ä¸Šèª²?‚é?: {lesson.get('day')} {lesson.get('time')}")
                print(f"?ˆèª²?å¸«: {lesson.get('teacher')}")
                print(f"??™¤?å??? {remaining_classes}")
                print(f"??™¤å¾Œå??? {new_remaining_classes}")
                print("==================")
                
                return {
                    'success': True,
                    'message': '?±å??å?ï¼?,
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
                print(f"è³‡æ?åº«æ?ä½œéŒ¯èª? {err}")
                # ?æ»¾äº‹å?
                connection.rollback()
                return {'error': '?±å??•ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?±å??•ç??¯èª¤: {str(e)}")
            return {'error': '?±å??•ç?å¤±æ?ï¼Œè?ç¨å??è©¦'}, 500
    
    def get(self):
        """?–å??€?‰å ±?è???""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM enrollments ORDER BY enrollment_time DESC")
                enrollments = cursor.fetchall()
                
                # è½‰æ? datetime ?©ä»¶??ISO ?¼å?å­—ä¸²
                for enrollment in enrollments:
                    if enrollment.get('enrollment_time') and isinstance(enrollment['enrollment_time'], datetime):
                        enrollment['enrollment_time'] = enrollment['enrollment_time'].isoformat()
                
                return {
                    'success': True,
                    'enrollments': enrollments,
                    'total': len(enrollments)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢?¯èª¤: {err}")
                return {'error': '?¥è©¢å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢å¤±æ?'}, 500

class Students(Resource):
    def get(self):
        """?–å??€?‰å­¸??""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                
                # è½‰æ? datetime ??date ?©ä»¶?ºå?ä¸?                for student in students:
                    # ?•ç? datetime æ¬„ä?
                    for field in ['created_at', 'updated_at']:
                        if student.get(field) and isinstance(student[field], datetime):
                            student[field] = student[field].isoformat()
                    
                    # ?•ç? date æ¬„ä?
                    for field in ['membership_expiry', 'date_of_birth']:
                        if student.get(field) and isinstance(student[field], date):
                            student[field] = student[field].isoformat()
                
                return {
                    'success': True,
                    'students': students,
                    'total': len(students)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢å­¸ç??¯èª¤: {err}")
                return {'error': '?¥è©¢å­¸ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢å­¸ç??¯èª¤: {str(e)}")
            return {'error': '?¥è©¢å­¸ç?å¤±æ?'}, 500
    
    def post(self):
        """?°å?å­¸ç?"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šå???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    'message': 'å­¸ç??°å??å?ï¼?,
                    'student_id': student_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å?å­¸ç??¯èª¤: {err}")
                return {'error': '?°å?å­¸ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å?å­¸ç??¯èª¤: {str(e)}")
            return {'error': '?°å?å­¸ç?å¤±æ?'}, 500

class Teachers(Resource):
    def get(self):
        """?–å??€?‰è€å¸«?Šå…¶é¢¨æ ¼"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                search_name = request.args.get('name')
                
                # ?¥è©¢?€?‰è€å¸«
                query = "SELECT * FROM teachers"
                params = []
                
                if search_name:
                    query += " WHERE name LIKE %s"
                    params.append(f"%{search_name}%")
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                teachers = cursor.fetchall()
                
                # ?¥è©¢?€?‰è€å¸«?„é¢¨??                teacher_ids = [teacher['id'] for teacher in teachers]
                if teacher_ids:
                    style_query = """
                    SELECT ts.teacher_id, s.id as style_id, s.name as style_name
                    FROM teacher_styles ts
                    JOIN styles s ON ts.style_id = s.id
                    WHERE ts.teacher_id IN (%s)
                    """ % ', '.join(['%s'] * len(teacher_ids))
                    
                    cursor.execute(style_query, teacher_ids)
                    styles = cursor.fetchall()
                    
                    # å°‡é¢¨?¼æ•´?†åˆ°å°æ??„è€å¸«?©ä»¶ä¸?                    teacher_styles = {teacher_id: [] for teacher_id in teacher_ids}
                    for style in styles:
                        teacher_styles[style['teacher_id']].append({
                            'id': style['style_id'],
                            'name': style['style_name']
                        })
                    
                    # å°‡é¢¨?¼å??¥è€å¸«?©ä»¶
                    for teacher in teachers:
                        teacher['styles'] = teacher_styles.get(teacher['id'], [])

                # è½‰æ? datetime ??Decimal ?©ä»¶??ISO ?¼å?å­—ä¸²
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
                print(f"?¥è©¢?å¸«?¯èª¤: {err}")
                return {'error': '?¥è©¢?å¸«å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢?å¸«?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢?å¸«å¤±æ?'}, 500
    
    def post(self):
        """?°å??å¸«"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šå???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                # ?’å…¥?å¸«?ºæœ¬è³‡æ?
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
                
                # ?•ç??å¸«?‡é¢¨?¼ç??œè¯
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
                    'message': '?å¸«?°å??å?ï¼?,
                    'teacher_id': teacher_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å??å¸«?¯èª¤: {err}")
                return {'error': '?°å??å¸«å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å??å¸«?¯èª¤: {str(e)}")
            return {'error': '?°å??å¸«å¤±æ?'}, 500

class Courses(Resource):
    def get(self):
        """?–å??€?‰èª²ç¨‹ï??…å«?å¸«è³‡è?ï¼?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                
                # è½‰æ? Decimal ??datetime ?©ä»¶?ºå¯ JSON åºå??–ç??¼å?
                for course in courses:
                    # å°?price æ¬„ä?è½‰ç‚ºå­—ä¸²
                    if 'price' in course and course['price'] is not None:
                        course['price'] = str(course['price'])
                    # è½‰æ? datetime ?©ä»¶??ISO ?¼å?å­—ä¸²
                    for field in ['created_at', 'updated_at']:
                        if course.get(field) and isinstance(course[field], datetime):
                            course[field] = course[field].isoformat()
                
                return {
                    'success': True,
                    'courses': courses,
                    'total': len(courses)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢èª²ç??¯èª¤: {err}")
                return {'error': f'?¥è©¢èª²ç?å¤±æ?: {err}'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢èª²ç??¯èª¤: {str(e)}")
            return {'error': '?¥è©¢èª²ç?å¤±æ?'}, 500
    
    def post(self):
        """?°å?èª²ç?"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'level' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šèª²ç¨‹å?ç¨±ã€é›£åº¦ç???}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    'message': 'èª²ç??°å??å?ï¼?,
                    'course_id': course_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å?èª²ç??¯èª¤: {err}")
                return {'error': '?°å?èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å?èª²ç??¯èª¤: {str(e)}")
            return {'error': '?°å?èª²ç?å¤±æ?'}, 500

class CourseSchedules(Resource):
    def get(self):
        """?–å??€?‰èª²ç¨‹æ??“è¡¨ï¼Œæ”¯?´æ—¥?Ÿç??é?æ¿?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500

            try:
                cursor = connection.cursor(dictionary=True)

                # ?–å??¥è©¢?ƒæ•¸
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')

                # ?ºæœ¬?¥è©¢èªå¥
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

                # æ·»å??¥æ?ç¯„å??æ¿¾æ¢ä»¶
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

                # è½‰æ??‚é??©ä»¶?ºå?ä¸?                for schedule in schedules:
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
                print(f"?¥è©¢èª²ç??‚é?è¡¨éŒ¯èª? {err}")
                return {'error': f'?¥è©¢èª²ç??‚é?è¡¨å¤±?? {err}'}, 500
            finally:
                cursor.close()
                connection.close()

        except Exception as e:
            print(f"?¥è©¢èª²ç??‚é?è¡¨éŒ¯èª? {str(e)}")
            return {'error': f'?¥è©¢èª²ç??‚é?è¡¨å¤±?? {str(e)}'}, 500

    def post(self):
        """?°å?èª²ç??‚é?è¡?""
        try:
            data = request.get_json()
            
            required_fields = ['course_id', 'schedule_date', 'start_time', 'end_time']
            if not data or not all(field in data for field in required_fields):
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šcourse_id, schedule_date, start_time, end_time'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                # å¾æ—¥?Ÿæ¨ç®—æ??Ÿå¹¾
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
                    'message': 'èª²ç??‚é?è¡¨æ–°å¢æ??Ÿï?',
                    'schedule_id': schedule_id,
                    'day_of_week': day_of_week
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å?èª²ç??‚é?è¡¨éŒ¯èª? {err}")
                return {'error': f'?°å?èª²ç??‚é?è¡¨å¤±?? {err}'}, 500
            except ValueError as e:
                print(f"?¥æ??¼å??¯èª¤: {e}")
                return {'error': '?¥æ??¼å??¯èª¤ï¼Œè?ä½¿ç”¨ YYYY-MM-DD ?¼å?'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å?èª²ç??‚é?è¡¨éŒ¯èª? {str(e)}")
            return {'error': '?°å?èª²ç??‚é?è¡¨å¤±??}, 500

class Student(Resource):
    def get(self, student_id):
        """?–å??®ä?å­¸ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                student = cursor.fetchone()
                
                if not student:
                    return {'error': 'å­¸ç??ªæ‰¾??}, 404
                
                # è½‰æ? datetime ??date ?©ä»¶?ºå?ä¸?                for field in ['created_at', 'updated_at']:
                    if student.get(field) and isinstance(student[field], datetime):
                        student[field] = student[field].isoformat()
                
                if student.get('membership_expiry') and isinstance(student['membership_expiry'], date):
                    student['membership_expiry'] = student['membership_expiry'].isoformat()
                
                return {
                    'success': True,
                    'student': student
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢å­¸ç??¯èª¤: {err}")
                return {'error': '?¥è©¢å­¸ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢å­¸ç??¯èª¤: {str(e)}")
            return {'error': '?¥è©¢å­¸ç?å¤±æ?'}, 500

    def put(self, student_id):
        """?´æ–°å­¸ç?è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'email', 'phone', 'date_of_birth', 'emergency_contact', 'emergency_phone', 'medical_notes', 'remaining_classes', 'membership_expiry']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                update_query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s"
                values.append(student_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'å­¸ç??ªæ‰¾?°æ?è³‡æ??ªæ”¹è®?}, 404
                
                return {
                    'success': True,
                    'message': 'å­¸ç?è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°å­¸ç??¯èª¤: {err}")
                return {'error': '?´æ–°å­¸ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°å­¸ç??¯èª¤: {str(e)}")
            return {'error': '?´æ–°å­¸ç?å¤±æ?'}, 500

    def delete(self, student_id):
        """?ªé™¤å­¸ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'å­¸ç??ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': 'å­¸ç??ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤å­¸ç??¯èª¤: {err}")
                return {'error': '?ªé™¤å­¸ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤å­¸ç??¯èª¤: {str(e)}")
            return {'error': '?ªé™¤å­¸ç?å¤±æ?'}, 500

class Teacher(Resource):
    def get(self, teacher_id):
        """?–å??®ä??å¸«"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
                teacher = cursor.fetchone()
                
                if not teacher:
                    return {'error': '?å¸«?ªæ‰¾??}, 404
                
                # ?¥è©¢?å¸«?„é¢¨??                style_query = """
                SELECT s.id, s.name
                FROM teacher_styles ts
                JOIN styles s ON ts.style_id = s.id
                WHERE ts.teacher_id = %s
                """
                cursor.execute(style_query, (teacher_id,))
                styles = cursor.fetchall()
                teacher['styles'] = styles
                
                # è½‰æ? datetime ??Decimal ?©ä»¶?ºå?ä¸?                if teacher.get('hourly_rate'):
                    teacher['hourly_rate'] = str(teacher['hourly_rate'])
                for field in ['created_at', 'updated_at']:
                    if teacher.get(field) and isinstance(teacher[field], datetime):
                        teacher[field] = teacher[field].isoformat()
                
                return {
                    'success': True,
                    'teacher': teacher
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢?å¸«?¯èª¤: {err}")
                return {'error': '?¥è©¢?å¸«å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢?å¸«?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢?å¸«å¤±æ?'}, 500

    def put(self, teacher_id):
        """?´æ–°?å¸«è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                
                # ?´æ–°?å¸«?‡é¢¨?¼ç??œè¯
                if 'style_ids' in data:
                    style_ids = data['style_ids']
                    # ?ˆåˆª?¤è??„é???                    cursor.execute("DELETE FROM teacher_styles WHERE teacher_id = %s", (teacher_id,))
                    # ?°å??°ç??œè¯
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
                    'message': '?å¸«è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°?å¸«?¯èª¤: {err}")
                return {'error': '?´æ–°?å¸«å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°?å¸«?¯èª¤: {str(e)}")
            return {'error': '?´æ–°?å¸«å¤±æ?'}, 500

    def delete(self, teacher_id):
        """?ªé™¤?å¸«"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?å¸«?ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': '?å¸«?ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤?å¸«?¯èª¤: {err}")
                return {'error': '?ªé™¤?å¸«å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤?å¸«?¯èª¤: {str(e)}")
            return {'error': '?ªé™¤?å¸«å¤±æ?'}, 500

class Course(Resource):
    def get(self, course_id):
        """?–å??®ä?èª²ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    return {'error': 'èª²ç??ªæ‰¾??}, 404
                
                # è½‰æ? Decimal ??datetime ?©ä»¶?ºå¯ JSON åºå??–ç??¼å?
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
                print(f"?¥è©¢èª²ç??¯èª¤: {err}")
                return {'error': '?¥è©¢èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢èª²ç??¯èª¤: {str(e)}")
            return {'error': '?¥è©¢èª²ç?å¤±æ?'}, 500

    def put(self, course_id):
        """?´æ–°èª²ç?è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'classes_required', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'èª²ç??ªæ‰¾?°æ?è³‡æ??ªæ”¹è®?}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç?è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°èª²ç??¯èª¤: {err}")
                return {'error': '?´æ–°èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°èª²ç??¯èª¤: {str(e)}")
            return {'error': '?´æ–°èª²ç?å¤±æ?'}, 500

    def delete(self, course_id):
        """?ªé™¤èª²ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'èª²ç??ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç??ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤èª²ç??¯èª¤: {err}")
                return {'error': '?ªé™¤èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤èª²ç??¯èª¤: {str(e)}")
            return {'error': '?ªé™¤èª²ç?å¤±æ?'}, 500

class Course(Resource):
    def get(self, course_id):
        """?–å??®ä?èª²ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    return {'error': 'èª²ç??ªæ‰¾??}, 404
                
                # è½‰æ? Decimal ??datetime ?©ä»¶?ºå¯ JSON åºå??–ç??¼å?
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
                print(f"?¥è©¢èª²ç??¯èª¤: {err}")
                return {'error': '?¥è©¢èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢èª²ç??¯èª¤: {str(e)}")
            return {'error': '?¥è©¢èª²ç?å¤±æ?'}, 500

    def put(self, course_id):
        """?´æ–°èª²ç?è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description', 'level', 'style_id', 'duration_minutes', 'max_students', 'price', 'classes_required', 'teacher_id']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                update_query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = %s"
                values.append(course_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'èª²ç??ªæ‰¾?°æ?è³‡æ??ªæ”¹è®?}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç?è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°èª²ç??¯èª¤: {err}")
                return {'error': '?´æ–°èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°èª²ç??¯èª¤: {str(e)}")
            return {'error': '?´æ–°èª²ç?å¤±æ?'}, 500

    def delete(self, course_id):
        """?ªé™¤èª²ç?"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'èª²ç??ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç??ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤èª²ç??¯èª¤: {err}")
                return {'error': '?ªé™¤èª²ç?å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤èª²ç??¯èª¤: {str(e)}")
            return {'error': '?ªé™¤èª²ç?å¤±æ?'}, 500

api.add_resource(HelloWorld, '/')
api.add_resource(Enrollment, '/api/enrollment')
api.add_resource(Students, '/api/students')
api.add_resource(Student, '/api/students/<int:student_id>') # ?°å??„å­¸?Ÿå–®ä¸€è³‡æ?
api.add_resource(Teachers, '/api/teachers')
api.add_resource(Teacher, '/api/teachers/<int:teacher_id>')
api.add_resource(Courses, '/api/courses')
api.add_resource(Course, '/api/courses/<int:course_id>')
api.add_resource(CourseSchedules, '/api/schedules')

class CourseSchedule(Resource):
    def get(self, schedule_id):
        """?–å??®ä?èª²ç??‚é?è¡?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    return {'error': 'èª²ç??‚é?è¡¨æœª?¾åˆ°'}, 404
                
                # è½‰æ??‚é??©ä»¶?ºå?ä¸?                if schedule.get('schedule_date'):
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
                print(f"?¥è©¢èª²ç??‚é?è¡¨éŒ¯èª? {err}")
                return {'error': '?¥è©¢èª²ç??‚é?è¡¨å¤±??}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢èª²ç??‚é?è¡¨éŒ¯èª? {str(e)}")
            return {'error': '?¥è©¢èª²ç??‚é?è¡¨å¤±??}, 500

    def put(self, schedule_id):
        """?´æ–°èª²ç??‚é?è¡¨è???""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['course_id', 'schedule_date', 'start_time', 'end_time', 'room_id', 'is_active']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                # å¾æ—¥?Ÿæ¨ç®—æ??Ÿå¹¾
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
                    return {'error': 'èª²ç??‚é?è¡¨æœª?¾åˆ°?–è??™æœª?¹è?'}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç??‚é?è¡¨è??™æ›´?°æ??Ÿï?'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°èª²ç??‚é?è¡¨éŒ¯èª? {err}")
                return {'error': '?´æ–°èª²ç??‚é?è¡¨å¤±??}, 500
            except ValueError as e:
                print(f"?¥æ??¼å??¯èª¤: {e}")
                return {'error': '?¥æ??¼å??¯èª¤ï¼Œè?ä½¿ç”¨ YYYY-MM-DD ?¼å?'}, 400
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°èª²ç??‚é?è¡¨éŒ¯èª? {str(e)}")
            return {'error': '?´æ–°èª²ç??‚é?è¡¨å¤±??}, 500

    def delete(self, schedule_id):
        """?ªé™¤èª²ç??‚é?è¡?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM course_schedules WHERE id = %s", (schedule_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'èª²ç??‚é?è¡¨æœª?¾åˆ°'}, 404
                
                return {
                    'success': True,
                    'message': 'èª²ç??‚é?è¡¨åˆª?¤æ??Ÿï?'
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤èª²ç??‚é?è¡¨éŒ¯èª? {err}")
                return {'error': '?ªé™¤èª²ç??‚é?è¡¨å¤±??}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤èª²ç??‚é?è¡¨éŒ¯èª? {str(e)}")
            return {'error': '?ªé™¤èª²ç??‚é?è¡¨å¤±??}, 500

api.add_resource(CourseSchedule, '/api/schedules/<int:schedule_id>')

class Styles(Resource):
    def get(self):
        """?–å??€?‰é¢¨??""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                print(f"?¥è©¢é¢¨æ ¼?¯èª¤: {err}")
                return {'error': '?¥è©¢é¢¨æ ¼å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢é¢¨æ ¼?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢é¢¨æ ¼å¤±æ?'}, 500
    
    def post(self):
        """?°å?é¢¨æ ¼"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šé¢¨?¼å?ç¨?}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    'message': 'é¢¨æ ¼?°å??å?ï¼?,
                    'style_id': style_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å?é¢¨æ ¼?¯èª¤: {err}")
                return {'error': '?°å?é¢¨æ ¼å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å?é¢¨æ ¼?¯èª¤: {str(e)}")
            return {'error': '?°å?é¢¨æ ¼å¤±æ?'}, 500

api.add_resource(Styles, '/api/styles')

class Style(Resource):
    def get(self, style_id):
        """?–å??®ä?é¢¨æ ¼"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM styles WHERE id = %s", (style_id,))
                style = cursor.fetchone()
                
                if not style:
                    return {'error': 'é¢¨æ ¼?ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'style': style
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢é¢¨æ ¼?¯èª¤: {err}")
                return {'error': '?¥è©¢é¢¨æ ¼å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢é¢¨æ ¼?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢é¢¨æ ¼å¤±æ?'}, 500

    def put(self, style_id):
        """?´æ–°é¢¨æ ¼è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'description']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                update_query = f"UPDATE styles SET {', '.join(update_fields)} WHERE id = %s"
                values.append(style_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'é¢¨æ ¼?ªæ‰¾?°æ?è³‡æ??ªæ”¹è®?}, 404
                
                return {
                    'success': True,
                    'message': 'é¢¨æ ¼è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°é¢¨æ ¼?¯èª¤: {err}")
                return {'error': '?´æ–°é¢¨æ ¼å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°é¢¨æ ¼?¯èª¤: {str(e)}")
            return {'error': '?´æ–°é¢¨æ ¼å¤±æ?'}, 500

    def delete(self, style_id):
        """?ªé™¤é¢¨æ ¼"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM styles WHERE id = %s", (style_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': 'é¢¨æ ¼?ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': 'é¢¨æ ¼?ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤é¢¨æ ¼?¯èª¤: {err}")
                return {'error': '?ªé™¤é¢¨æ ¼å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤é¢¨æ ¼?¯èª¤: {str(e)}")
            return {'error': '?ªé™¤é¢¨æ ¼å¤±æ?'}, 500

api.add_resource(Style, '/api/styles/<int:style_id>')

class Rooms(Resource):
    def get(self):
        """?–å??€?‰æ?å®?""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': '?¥è©¢?™å®¤å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms ORDER BY id DESC")
                rooms = cursor.fetchall()

                # è½‰æ? Decimal ?©ä»¶?ºå?ä¸?                for room in rooms:
                    if room.get('hourly_rate'):
                        room['hourly_rate'] = str(room['hourly_rate'])
                    # è½‰æ? datetime ?©ä»¶??ISO ?¼å?å­—ä¸²
                    for field in ['created_at', 'updated_at']:
                        if room.get(field) and isinstance(room[field], datetime):
                            room[field] = room[field].isoformat()
                
                return {
                    'success': True,
                    'rooms': rooms,
                    'total': len(rooms)
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?¥è©¢?™å®¤?¯èª¤: {err}")
                return {'error': '?¥è©¢?™å®¤å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢?™å®¤?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢?™å®¤å¤±æ?'}, 500

    def post(self):
        """?°å??™å®¤"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return {'error': 'ç¼ºå?å¿…è?æ¬„ä?ï¼šæ?å®¤å?ç¨?}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
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
                    'message': '?™å®¤?°å??å?ï¼?,
                    'room_id': room_id
                }, 201
                
            except mysql.connector.Error as err:
                print(f"?°å??™å®¤?¯èª¤: {err}")
                return {'error': '?°å??™å®¤å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?°å??™å®¤?¯èª¤: {str(e)}")
            return {'error': '?°å??™å®¤å¤±æ?'}, 500

api.add_resource(Rooms, '/api/rooms')

class Room(Resource):
    def get(self, room_id):
        """?–å??®ä??™å®¤"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
                room = cursor.fetchone()
                
                if not room:
                    return {'error': '?™å®¤?ªæ‰¾??}, 404
                
                # è½‰æ? Decimal ??datetime
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
                print(f"?¥è©¢?™å®¤?¯èª¤: {err}")
                return {'error': '?¥è©¢?™å®¤å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?¥è©¢?™å®¤?¯èª¤: {str(e)}")
            return {'error': '?¥è©¢?™å®¤å¤±æ?'}, 500

    def put(self, room_id):
        """?´æ–°?™å®¤è³‡æ?"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'ç¼ºå??´æ–°è³‡æ?'}, 400
            
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                
                update_fields = []
                values = []
                
                for key, value in data.items():
                    if key in ['name', 'capacity', 'equipment', 'description', 'hourly_rate', 'is_available']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return {'error': 'æ²’æ??¯æ›´?°ç?æ¬„ä?'}, 400
                
                update_query = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = %s"
                values.append(room_id)
                
                cursor.execute(update_query, tuple(values))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?™å®¤?ªæ‰¾?°æ?è³‡æ??ªæ”¹è®?}, 404
                
                return {
                    'success': True,
                    'message': '?™å®¤è³‡æ??´æ–°?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?´æ–°?™å®¤?¯èª¤: {err}")
                return {'error': '?´æ–°?™å®¤å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?´æ–°?™å®¤?¯èª¤: {str(e)}")
            return {'error': '?´æ–°?™å®¤å¤±æ?'}, 500

    def delete(self, room_id):
        """?ªé™¤?™å®¤"""
        try:
            connection = get_db_connection()
            if not connection:
                return {'error': 'è³‡æ?åº«é€?¥å¤±æ?'}, 500
            
            try:
                cursor = connection.cursor()
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
                connection.commit()
                
                if cursor.rowcount == 0:
                    return {'error': '?™å®¤?ªæ‰¾??}, 404
                
                return {
                    'success': True,
                    'message': '?™å®¤?ªé™¤?å?ï¼?
                }, 200
                
            except mysql.connector.Error as err:
                print(f"?ªé™¤?™å®¤?¯èª¤: {err}")
                return {'error': '?ªé™¤?™å®¤å¤±æ?'}, 500
            finally:
                cursor.close()
                connection.close()
                
        except Exception as e:
            print(f"?ªé™¤?™å®¤?¯èª¤: {str(e)}")
            return {'error': '?ªé™¤?™å®¤å¤±æ?'}, 500

api.add_resource(Room, '/api/rooms/<int:room_id>')



if __name__ == '__main__':
    # ?å??–è??™åº«è¡¨æ ¼
    init_database_tables()
    app.run(debug=True, host='0.0.0.0', port=8001)
