-- 建立學生表格
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
);

-- 建立教室表格
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
);

-- 建立老師表格
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
);

-- 建立風格表格
CREATE TABLE IF NOT EXISTS styles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- 建立老師-風格關聯表
CREATE TABLE IF NOT EXISTS teacher_styles (
    teacher_id INT NOT NULL,
    style_id INT NOT NULL,
    PRIMARY KEY (teacher_id, style_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);
    hourly_rate DECIMAL(10,2),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 建立課程表格
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
);

-- 建立課程時間表格
CREATE TABLE IF NOT EXISTS course_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    schedule_date DATE NOT NULL, -- 具體日期 (YYYY-MM-DD)
    day_of_week VARCHAR(20) NOT NULL, -- Monday, Tuesday, etc.
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
);

-- 修改現有的報名表格，添加外鍵關聯
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
);

-- 插入範例教室資料
INSERT INTO rooms (name, capacity, equipment, description, hourly_rate, is_available) VALUES
('Studio A', 20, 'Sound System, Mirrors, Ballet Barre', '大型練習室，適合芭蕾和現代舞', 500.00, TRUE),
('Studio B', 15, 'Sound System, Mirrors', '中型練習室，適合各種舞蹈類型', 400.00, TRUE),
('Studio C', 25, 'Professional Sound System, LED Lighting, Mirrors', '專業表演練習室，設備齊全', 800.00, TRUE),
('Studio D', 10, 'Basic Sound System, Mirrors', '小型練習室，適合私人課程', 300.00, TRUE);

-- 插入範例風格資料
INSERT INTO styles (name, description) VALUES
('Ballet', '古典芭蕾舞'),
('Jazz', '爵士舞'),
('Hip-Hop', '嘻哈街舞'),
('Contemporary', '現代舞'),
('Modern', '現代舞'),
('Street Dance', '街舞');

-- 插入範例老師資料
INSERT INTO teachers (name, email, phone, experience_years, bio, hourly_rate) VALUES
('張美麗', 'zhang@dancestudio.com', '0912-345-678', 8, '專業芭蕾舞老師，畢業於國立台北藝術大學', 1200.00),
('李強', 'li@dancestudio.com', '0923-456-789', 5, '街舞冠軍，擅長各種流行舞蹈', 1000.00),
('王雅文', 'wang@dancestudio.com', '0934-567-890', 10, '爵士舞專家，具有豐富的表演經驗', 1300.00);

-- 插入老師-風格關聯資料
INSERT INTO teacher_styles (teacher_id, style_id) VALUES
(1, 1), -- 張美麗 - Ballet
(1, 4), -- 張美麗 - Contemporary
(2, 3), -- 李強 - Hip-Hop
(2, 6), -- 李強 - Street Dance
(3, 2), -- 王雅文 - Jazz
(3, 5); -- 王雅文 - Modern

-- 插入範例課程資料
INSERT INTO courses (name, description, level, style_id, duration_minutes, max_students, price, teacher_id) VALUES
('初級芭蕾', '適合零基礎學員的芭蕾課程', 'beginner', 1, 90, 12, 800.00, 1),
('中級芭蕾', '具有基礎的學員進階課程', 'intermediate', 1, 90, 10, 1000.00, 1),
('街舞入門', '流行街舞基礎教學', 'beginner', 3, 60, 15, 600.00, 2),
('爵士舞精修', '爵士舞進階技巧訓練', 'advanced', 2, 75, 8, 1200.00, 3),
('現代舞基礎', '現代舞基本動作與表達', 'beginner', 5, 75, 12, 700.00, 3);

-- 插入範例課程時間表
INSERT INTO course_schedules (course_id, schedule_date, day_of_week, start_time, end_time, room_id) VALUES
(1, '2025-01-06', 'Monday', '18:00:00', '19:30:00', 1),
(1, '2025-01-08', 'Wednesday', '18:00:00', '19:30:00', 1),
(1, '2025-01-13', 'Monday', '18:00:00', '19:30:00', 1),
(1, '2025-01-15', 'Wednesday', '18:00:00', '19:30:00', 1),
(2, '2025-01-07', 'Tuesday', '19:00:00', '20:30:00', 1),
(2, '2025-01-09', 'Thursday', '19:00:00', '20:30:00', 1),
(2, '2025-01-14', 'Tuesday', '19:00:00', '20:30:00', 1),
(2, '2025-01-16', 'Thursday', '19:00:00', '20:30:00', 1),
(3, '2025-01-06', 'Monday', '20:00:00', '21:00:00', 2),
(3, '2025-01-10', 'Friday', '19:00:00', '20:00:00', 2),
(3, '2025-01-13', 'Monday', '20:00:00', '21:00:00', 2),
(3, '2025-01-17', 'Friday', '19:00:00', '20:00:00', 2),
(4, '2025-01-08', 'Wednesday', '20:00:00', '21:15:00', 3),
(4, '2025-01-15', 'Wednesday', '20:00:00', '21:15:00', 3),
(5, '2025-01-11', 'Saturday', '10:00:00', '11:15:00', 1),
(5, '2025-01-18', 'Saturday', '10:00:00', '11:15:00', 1);