-- ============================================================
-- M9 出院结算 SQL
-- 对应开发文档第十章
-- ============================================================

-- ----------------------------------------------------------
-- 10.1 出院结算（事务）
-- ----------------------------------------------------------

-- 事务开始

-- Step A：锁定档案并获取关键信息
SELECT file_no, case_no, ward_id, bed_id, admit_time, deposit_balance
FROM admission_file
WHERE file_no = ?
FOR UPDATE;
-- 若 discharge_time IS NOT NULL → 已出院，拒绝重复操作

-- Step B：校验出院时间必须晚于入院时间（R25）
-- 应用层判断：NOW() > admit_time，否则拒绝

-- Step C：汇总住院总费用（R26）
SELECT COALESCE(SUM(daily_fee), 0) AS total_cost
FROM inpatient_record
WHERE file_no = ?;

-- Step D：计算结算金额（R27）
-- 结算金额 = deposit_balance - total_cost
-- 正数 → 退还病人；负数 → 病人需补缴
-- 应用层计算并展示

-- Step E：填写出院时间
UPDATE admission_file
SET discharge_time = NOW()
WHERE file_no = ?;

-- Step F：释放资源（R28）
-- 更新病人状态
UPDATE patient
SET is_inpatient = '否', ward_id = NULL, bed_id = NULL
WHERE case_no = ?;

-- 更新床位状态
UPDATE bed
SET bed_status = '空闲'
WHERE bed_id = ?;

-- 更新病房入住人数
UPDATE ward
SET occupied_cnt = occupied_cnt - 1
WHERE ward_id = ?;

-- 事务提交


-- ----------------------------------------------------------
-- 10.2 出院后：查询某次住院的费用汇总
-- ----------------------------------------------------------
SELECT af.file_no, af.admit_time, af.discharge_time,
       af.deposit_balance AS final_balance,
       DATEDIFF(af.discharge_time, af.admit_time) AS stay_days,
       COALESCE(SUM(ir.daily_fee), 0) AS total_cost
FROM admission_file af
LEFT JOIN inpatient_record ir ON af.file_no = ir.file_no
WHERE af.file_no = ?
GROUP BY af.file_no, af.admit_time, af.discharge_time, af.deposit_balance;
