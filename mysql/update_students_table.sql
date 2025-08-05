-- 更新學生表格，添加剩餘堂數和會員到期日欄位

-- 檢查並添加 remaining_classes 欄位
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'testdb' 
  AND TABLE_NAME = 'students' 
  AND COLUMN_NAME = 'remaining_classes';

SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE students ADD COLUMN remaining_classes INT DEFAULT 0 COMMENT ''剩餘堂數''',
    'SELECT ''Column remaining_classes already exists'' as message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並添加 membership_expiry 欄位
SET @column_exists = 0;
SELECT COUNT(*) INTO @column_exists 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'testdb' 
  AND TABLE_NAME = 'students' 
  AND COLUMN_NAME = 'membership_expiry';

SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE students ADD COLUMN membership_expiry DATE COMMENT ''會員到期日''',
    'SELECT ''Column membership_expiry already exists'' as message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 顯示更新後的表格結構
DESCRIBE students;
