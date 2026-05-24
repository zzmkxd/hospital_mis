-- ============================================================
-- M1 登录认证 SQL
-- 对应开发文档第二章
-- ============================================================

-- 1. 验证登录
-- 输入：ref_id (医生ID或病案号), role
-- 输出：account_id, ref_id, role, password_hash
-- 应用层比对 password_hash，匹配则登录成功
SELECT account_id, ref_id, role, password_hash
FROM account
WHERE ref_id = ? AND role = ?;
