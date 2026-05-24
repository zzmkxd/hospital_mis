-- ============================================================
-- M7 住院登记（入院）SQL
-- 对应开发文档第八章
-- 一次入院涉及 6 张表的原子更新，必须在事务中执行
-- ============================================================

-- ----------------------------------------------------------
-- 8.1 查询可选病房（有空床 + 科室对口）
-- ----------------------------------------------------------
SELECT w.ward_id, w.ward_no, w.location, w.charge_rate,
       w.total_beds, w.occupied_cnt,
       (w.total_beds - w.occupied_cnt) AS available_beds
FROM ward w
WHERE w.dept_id = ?
  AND w.occupied_cnt < w.total_beds;


-- ----------------------------------------------------------
-- 8.2 查询可选床位（选定病房后，仅空闲床位）
-- ----------------------------------------------------------
SELECT bed_id, bed_no
FROM bed
WHERE ward_id = ?
  AND bed_status = '空闲';


-- ----------------------------------------------------------
-- 8.3 执行入院（事务）
-- ----------------------------------------------------------

-- 事务开始

-- Step A：锁定床位，防止并发分配
SELECT bed_id, bed_status
FROM bed
WHERE bed_id = ?
FOR UPDATE;
-- 若 bed_status != '空闲'，回滚

-- Step B：创建住院档案
-- file_no 为 AUTO_INCREMENT，admit_time 为 DEFAULT CURRENT_TIMESTAMP
-- discharge_time 保持 NULL 表示仍在院
INSERT INTO admission_file (case_no, doctor_id, ward_id, bed_id, deposit_balance)
VALUES (?, ?, ?, ?, ?);
-- 获取 LAST_INSERT_ID() 作为 file_no

-- Step C：更新病人状态（R20）
UPDATE patient
SET is_inpatient = '是', ward_id = ?, bed_id = ?
WHERE case_no = ?;

-- Step D：更新床位状态
UPDATE bed
SET bed_status = '占用'
WHERE bed_id = ?;

-- Step E：更新病房入住人数
UPDATE ward
SET occupied_cnt = occupied_cnt + 1
WHERE ward_id = ?;

-- 事务提交


-- ----------------------------------------------------------
-- 8.4 查询在院病人列表（管理员/医生视角）
-- ----------------------------------------------------------
SELECT af.file_no, af.case_no, af.admit_time, af.deposit_balance,
       p.name AS patient_name, p.gender, p.age,
       d.name AS doctor_name,
       w.ward_no, b.bed_no
FROM admission_file af
JOIN patient p ON af.case_no = p.case_no
JOIN doctor d ON af.doctor_id = d.doctor_id
JOIN ward w ON af.ward_id = w.ward_id
JOIN bed b ON af.bed_id = b.bed_id
WHERE af.discharge_time IS NULL
ORDER BY af.admit_time;
