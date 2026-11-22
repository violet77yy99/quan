-- 在 MySQL 8.x 中执行本文件（用 root 或管理员账号）：
--   mysql -u root -p < scripts/init_mysql.sql
-- 然后确认 backend/.env 里的 DATABASE_URL 与下面一致。

CREATE DATABASE IF NOT EXISTS pawpedia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'pawpedia'@'localhost' IDENTIFIED BY 'pawpedia123';
CREATE USER IF NOT EXISTS 'pawpedia'@'127.0.0.1' IDENTIFIED BY 'pawpedia123';
GRANT ALL PRIVILEGES ON pawpedia.* TO 'pawpedia'@'localhost';
GRANT ALL PRIVILEGES ON pawpedia.* TO 'pawpedia'@'127.0.0.1';
FLUSH PRIVILEGES;

-- 表由 SQLAlchemy 在启动时自动创建，无需手动建表。