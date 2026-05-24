-- ============================================================
-- M3 排班管理 SQL
-- 对应开发文档第四章
-- 注意：时间段重叠判定 = A.start_time < B.end_time AND A.end_time > B.start_time
-- ============================================================

-- ----------------------------------------------------------
-- 4.1 查看排班列表（管理员视角，含医生和科室信息）
-- ----------------------------------------------------------
SELECT s.schedule_id, s.sched_date, s.start_time, s.end_time,
       s.sched_type, s.clinic,
       d.doctor_id, d.name AS doctor_name, d.title,
       dep.dept_name
FROM schedule s
JOIN doctor d ON s.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
ORDER BY s.sched_date DESC, s.start_time;


-- ----------------------------------------------------------
-- 4.2 冲突检测（创建 / 编辑排班前执行）
-- ----------------------------------------------------------

-- 检测1：R03 — 同一医生同日时间段不得重叠
-- 编辑时需额外排除自身：AND schedule_id != ?
SELECT COUNT(*) AS conflict_cnt
FROM schedule
WHERE doctor_id = ?
  AND sched_date = ?
  AND start_time < ?   -- 新记录的 end_time
  AND end_time > ?;    -- 新记录的 start_time

-- 检测2：R04 — 同一诊室同一时段不得安排两位医生（仅门诊坐诊）
-- 仅当 sched_type = '门诊坐诊' 时执行
SELECT COUNT(*) AS conflict_cnt
FROM schedule
WHERE clinic = ?
  AND sched_date = ?
  AND sched_type = '门诊坐诊'
  AND start_time < ?
  AND end_time > ?;


-- ----------------------------------------------------------
-- 4.3 创建排班（R05：门诊坐诊 clinic 必填，住院巡诊 clinic 为 NULL）
-- ----------------------------------------------------------
INSERT INTO schedule (doctor_id, sched_date, start_time, end_time, sched_type, clinic)
VALUES (?, ?, ?, ?, ?, ?);

-- ----------------------------------------------------------
-- 4.4 修改排班
-- ----------------------------------------------------------
UPDATE schedule
SET doctor_id = ?, sched_date = ?, start_time = ?, end_time = ?,
    sched_type = ?, clinic = ?
WHERE schedule_id = ?;

-- ----------------------------------------------------------
-- 4.5 删除排班
-- ----------------------------------------------------------
DELETE FROM schedule WHERE schedule_id = ?;
