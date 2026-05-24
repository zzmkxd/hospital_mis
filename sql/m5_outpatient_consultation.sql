-- ============================================================
-- M5 医生门诊接诊与处方 SQL
-- 对应开发文档第六章
-- ============================================================

-- ----------------------------------------------------------
-- 6.1 接诊队列（医生视角：待就诊病人列表）
-- ----------------------------------------------------------
SELECT r.reg_id, r.case_no, r.reg_type, r.reg_date,
       p.name AS patient_name, p.gender, p.age
FROM registration r
JOIN patient p ON r.case_no = p.case_no
WHERE r.doctor_id = ?
  AND r.reg_status = '待就诊'
ORDER BY r.reg_date;


-- ----------------------------------------------------------
-- 6.2 接诊动作：更新挂号状态
-- ----------------------------------------------------------
UPDATE registration
SET reg_status = '已就诊'
WHERE reg_id = ?;


-- ----------------------------------------------------------
-- 6.3 查询可用药品列表（库存 > 0，R12）
-- ----------------------------------------------------------
SELECT medicine_id, med_name, specification, unit, unit_price, stock_qty
FROM medicine
WHERE stock_qty > 0
ORDER BY med_name;


-- ----------------------------------------------------------
-- 6.4 开具门诊处方（事务）
-- ----------------------------------------------------------

-- 事务开始

-- Step A：创建处方主记录
-- presc_id 为 AUTO_INCREMENT，presc_time 为 DEFAULT CURRENT_TIMESTAMP
INSERT INTO outpatient_prescription (reg_id, doctor_id, symptom_desc, pay_status)
VALUES (?, ?, ?, '待支付');
-- 获取 LAST_INSERT_ID() 作为 presc_id

-- Step B：逐条添加处方明细
-- presc_type 固定为 '门诊'
INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst)
VALUES (?, '门诊', ?, ?, ?);
-- 可循环执行多条

-- Step C（可选）：扣减库存
UPDATE medicine
SET stock_qty = stock_qty - ?
WHERE medicine_id = ? AND stock_qty >= ?;

-- 事务提交


-- ----------------------------------------------------------
-- 6.5 查询门诊处方明细
-- ----------------------------------------------------------
SELECT pd.detail_id, pd.qty, pd.usage_inst,
       m.med_name, m.specification, m.unit, m.unit_price,
       (pd.qty * m.unit_price) AS line_total
FROM prescription_detail pd
JOIN medicine m ON pd.medicine_id = m.medicine_id
WHERE pd.presc_type = '门诊'
  AND pd.presc_id = ?;


-- ----------------------------------------------------------
-- 6.6 计算门诊处方总费用（R14）
--    诊疗费 + Σ(明细数量 × 药品单价)
-- ----------------------------------------------------------
SELECT d.consultation_fee
     + COALESCE(SUM(pd.qty * m.unit_price), 0) AS total_fee
FROM outpatient_prescription op
JOIN doctor d ON op.doctor_id = d.doctor_id
LEFT JOIN prescription_detail pd ON pd.presc_id = op.presc_id AND pd.presc_type = '门诊'
LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id
WHERE op.presc_id = ?
GROUP BY op.presc_id, d.consultation_fee;
