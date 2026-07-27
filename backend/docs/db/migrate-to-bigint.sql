-- PostgreSQL 主外键升级脚本：INTEGER/SERIAL -> BIGINT/BIGSERIAL
-- 适用场景：已存在 users/notes 表，需要保留数据并升级 ID 容量
-- 执行方式（示例）：
--   psql "$DATABASE_URL" -f backend/docs/db/migrate-to-bigint.sql

BEGIN;

-- 1) 暂时移除外键，避免类型修改时依赖冲突
ALTER TABLE notes DROP CONSTRAINT IF EXISTS notes_user_id_fkey;

-- 2) 升级主键与关联字段到 BIGINT
ALTER TABLE users ALTER COLUMN id TYPE BIGINT;
ALTER TABLE notes ALTER COLUMN id TYPE BIGINT;
ALTER TABLE notes ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE notes ALTER COLUMN parent_id TYPE BIGINT;

-- 3) 确保自增序列为 BIGINT（PostgreSQL sequence 默认即 bigint，此处显式声明）
ALTER SEQUENCE IF EXISTS users_id_seq AS BIGINT;
ALTER SEQUENCE IF EXISTS notes_id_seq AS BIGINT;

-- 4) 重新绑定默认值（防止历史环境中 default 丢失）
ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);
ALTER TABLE notes ALTER COLUMN id SET DEFAULT nextval('notes_id_seq'::regclass);

-- 5) 恢复外键约束
ALTER TABLE notes
  ADD CONSTRAINT notes_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES users(id)
  ON UPDATE RESTRICT ON DELETE RESTRICT;

COMMIT;
