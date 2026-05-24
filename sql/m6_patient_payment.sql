-- ============================================================
-- M6 病人缴费与查看 SQL
-- 对应开发文档第七章
-- ============================================================

-- ----------------------------------------------------------
-- 7.1 查看待支付处方列表
-- ----------------------------------------------------------
SELECT op.presc_id, op.presc_time, op.symptom_desc, op.pay_status,
       d.name AS doctor_name, d.consultation_fee,
       dep.dept_name
FROM outpatient_prescription op
JOIN registration r ON op.reg_id = r.reg_id
JOIN doctor d ON op.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
WHERE r.case_no = ?
  AND op.pay_status = '待支付'
ORDER BY op.presc_time DESC;


-- ----------------------------------------------------------
-- 7.2 单张处方费用汇总（诊疗费 + 药费）
-- ----------------------------------------------------------
SELECT d.consultation_fee
     + COALESCE(SUM(pd.qty * m.unit_price), 0) AS total_fee
FROM outpatient_prescription op
JOIN doctor d ON op.doctor_id = d.doctor_id
LEFT JOIN prescription_detail pd ON pd.presc_id = op.presc_id AND pd.presc_type = '门诊'
LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id
WHERE op.presc_id = ?
GROUP BY op.presc_id, d.consultation_fee;


-- ----------------------------------------------------------
-- 7.3 执行支付
-- ----------------------------------------------------------
UPDATE outpatient_prescription
SET pay_status = '已支付'
WHERE presc_id = ? AND pay_status = '待支付';
-- 受影响行数 = 0 说明已被支付或不存在，需报错


-- ----------------------------------------------------------
-- 7.4 病人门诊历史全景查询（R31 — 门诊部分）
-- ----------------------------------------------------------
SELECT '门诊' AS record_type,
       r.reg_date AS time,
       op.presc_time,
       d.name AS doctor_name,
       dep.dept_name,
       op.symptom_desc,
       op.pay_status
FROM registration r
LEFT JOIN outpatient_prescription op ON r.reg_id = op.reg_id
JOIN doctor d ON r.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
WHERE r.case_no = ?
ORDER BY r.reg_date DESC;


-- ----------------------------------------------------------
-- 7.5 病人住院历史全景查询（R31 — 住院部分）
-- ----------------------------------------------------------
SELECT '住院' AS record_type,
       af.admit_time,
       af.discharge_time,
       d.name AS doctor_name,
       w.ward_no,
       b.bed_no,
       af.deposit_balance
FROM admission_file af
JOIN doctor d ON af.doctor_id = d.doctor_id
JOIN ward w ON af.ward_id = w.ward_id
JOIN bed b ON af.bed_id = b.bed_id
WHERE af.case_no = ?
ORDER BY af.admit_time DESC;


-- ----------------------------------------------------------
-- 7.6 住院费用明细查询（某次住院的每日费用明细）
-- ----------------------------------------------------------
SELECT ir.record_date, ir.treatment_desc, ir.daily_fee,
       ip.presc_id, ip.presc_time,
       pd.qty, pd.usage_inst,
       m.med_name, m.unit_price, (pd.qty * m.unit_price) AS drug_cost
FROM inpatient_record ir
LEFT JOIN inpatient_prescription ip ON ir.record_id = ip.record_id
LEFT JOIN prescription_detail pd ON pd.presc_id = ip.presc_id AND pd.presc_type = '住院'
LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id
WHERE ir.file_no = ?
ORDER BY ir.record_date DESC, ip.presc_time;
