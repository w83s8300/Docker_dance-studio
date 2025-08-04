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

def init_enrollment_table():
    """初始化報名表格，包含重試機制"""
    print("正在初始化資料庫表格...")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_name VARCHAR(100) NOT NULL,
                lesson_name VARCHAR(100) NOT NULL,
                lesson_time VARCHAR(50) NOT NULL,
                lesson_day VARCHAR(20) NOT NULL,
                lesson_teacher VARCHAR(50) NOT NULL,
                lesson_level VARCHAR(20) NOT NULL,
                lesson_type VARCHAR(50) NOT NULL,
                enrollment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'confirmed'
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            print("報名表格初始化成功")
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

api.add_resource(HelloWorld, '/')
api.add_resource(Enrollment, '/api/enrollment')

if __name__ == '__main__':
    # 初始化資料庫表格
    init_enrollment_table()
    app.run(debug=True, host='0.0.0.0', port=8001)