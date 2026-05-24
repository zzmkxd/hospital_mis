-- ============================================================
-- M4 病人挂号 SQL
-- 对应开发文档第五章
-- ============================================================

-- ----------------------------------------------------------
-- 5.1 选择科室 → 查询该科室当日门诊坐诊医生列表
-- ----------------------------------------------------------
SELECT d.doctor_id, d.name, d.title, d.consultation_fee,
       s.schedule_id, s.sched_date, s.start_time, s.end_time, s.clinic
FROM schedule s
JOIN doctor d ON s.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
WHERE dep.dept_id = ?
  AND s.sched_type = '门诊坐诊'
  AND s.sched_date = ?
ORDER BY s.start_time;


-- ----------------------------------------------------------
-- 5.2 判定初诊/复诊
-- ----------------------------------------------------------
SELECT COUNT(*) AS history_cnt
FROM registration
WHERE case_no = ? AND reg_status = '已就诊';
-- count > 0 → '复诊'，否则 '初诊'


-- ----------------------------------------------------------
-- 5.3 创建挂号
-- ----------------------------------------------------------
INSERT INTO registration (case_no, doctor_id, schedule_id, reg_type, reg_status)
VALUES (?, ?, ?, ?, '待就诊');


-- ----------------------------------------------------------
-- 5.4 查看我的挂号列表（病人视角）
-- ----------------------------------------------------------
SELECT r.reg_id, r.reg_date, r.reg_type, r.reg_status,
       d.name AS doctor_name, d.title,
       dep.dept_name, s.sched_date, s.start_time, s.end_time, s.clinic
FROM registration r
JOIN doctor d ON r.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
JOIN schedule s ON r.schedule_id = s.schedule_id
WHERE r.case_no = ?
ORDER BY r.reg_date DESC;


-- ----------------------------------------------------------
-- 5.5 取消挂号
-- ----------------------------------------------------------
UPDATE registration
SET reg_status = '已取消'
WHERE reg_id = ? AND reg_status = '待就诊';


-- ----------------------------------------------------------
-- 5.6（可扩展）容量检测 — schedule 表需先增加 max_registrations 字段
-- ----------------------------------------------------------
-- SELECT COUNT(*) AS current_cnt
-- FROM registration
-- WHERE schedule_id = ? AND reg_status != '已取消';
-- 超过上限则拒绝
