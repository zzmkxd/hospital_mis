-- ============================================================
-- M8 医生每日查房 SQL
-- 对应开发文档第九章
-- 住院记录 + 住院处方 + 处方明细 + 费用计算 + 预交金扣减在一个事务中
-- ============================================================

-- ----------------------------------------------------------
-- 9.1 查房入口：查看我的在院病人列表
-- ----------------------------------------------------------
SELECT af.file_no, af.case_no, af.admit_time, af.deposit_balance,
       p.name AS patient_name, p.gender, p.age,
       w.ward_no, b.bed_no
FROM admission_file af
JOIN patient p ON af.case_no = p.case_no
JOIN ward w ON af.ward_id = w.ward_id
JOIN bed b ON af.bed_id = b.bed_id
WHERE af.doctor_id = ?
  AND af.discharge_time IS NULL
ORDER BY af.admit_time;


-- ----------------------------------------------------------
-- 9.2 创建每日住院记录 + 处方（事务）
-- ----------------------------------------------------------

-- 事务开始

-- Step A：检查当日是否已有记录（R21）
SELECT COUNT(*) AS cnt
FROM inpatient_record
WHERE file_no = ? AND record_date = CURDATE();
-- cnt > 0 → 拒绝，提示"今日已查房"

-- Step B：获取档案信息（病房床位费 + 预交金余额）
SELECT af.deposit_balance, w.charge_rate
FROM admission_file af
JOIN ward w ON af.ward_id = w.ward_id
WHERE af.file_no = ?
FOR UPDATE;
-- 若 deposit_balance <= 0 → 直接拒绝（已完全欠费）
-- 若余额 > 0 但不足以支付当日费用 → Step H 会因 WHERE deposit_balance >= ? 而回滚
-- charge_rate 用于 Step F 费用计算

-- Step C：创建当日住院记录
-- record_id 为 AUTO_INCREMENT，daily_fee 初始为 0（Step F 再更新）
INSERT INTO inpatient_record (file_no, record_date, treatment_desc)
VALUES (?, CURDATE(), ?);
-- 获取 LAST_INSERT_ID() 作为 record_id

-- Step D：创建住院处方（一天一张，挂载在当日住院记录下）
-- presc_id 为 AUTO_INCREMENT，presc_time 为 DEFAULT CURRENT_TIMESTAMP
INSERT INTO inpatient_prescription (record_id, doctor_id)
VALUES (?, ?);
-- 获取 LAST_INSERT_ID() 作为 presc_id

-- Step E：逐条添加处方明细（一张处方含多条用药明细）
-- presc_type 固定为 '住院'
INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst)
VALUES (?, '住院', ?, ?, ?);
-- 循环执行，每条一种药

-- Step F：计算当日药费
-- 通过 inpatient_prescription JOIN prescription_detail 聚合当日所有用药
SELECT COALESCE(SUM(pd.qty * m.unit_price), 0) AS total_drug_fee
FROM inpatient_prescription ip
JOIN prescription_detail pd ON pd.presc_id = ip.presc_id AND pd.presc_type = '住院'
JOIN medicine m ON pd.medicine_id = m.medicine_id
WHERE ip.record_id = ?;

-- 当日费用 = 床位费(charge_rate) + 药费(total_drug_fee)

-- Step G：写入当日费用（R23）
UPDATE inpatient_record
SET daily_fee = ?
WHERE record_id = ?;

-- Step H：扣减预交金（R23）
UPDATE admission_file
SET deposit_balance = deposit_balance - ?
WHERE file_no = ? AND deposit_balance >= ?;
-- 受影响行数 = 0 说明余额不足，回滚

-- 事务提交


-- ----------------------------------------------------------
-- 9.3 查看历史查房记录（某档案的每日记录）
-- ----------------------------------------------------------
SELECT ir.record_id, ir.record_date, ir.treatment_desc, ir.daily_fee,
       ip.presc_id, ip.presc_time
FROM inpatient_record ir
LEFT JOIN inpatient_prescription ip ON ir.record_id = ip.record_id
WHERE ir.file_no = ?
ORDER BY ir.record_date DESC, ip.presc_time;
