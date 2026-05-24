-- ============================================================
-- 统计查询 SQL（管理员）
-- 对应开发文档第十一章
-- ============================================================

-- ----------------------------------------------------------
-- 11.1 医生工作量统计（R30）
--     按医生聚合已就诊挂号数 + 门诊处方数，支持时间段过滤
-- ----------------------------------------------------------
SELECT d.doctor_id, d.name, d.title, dep.dept_name,
       COUNT(DISTINCT r.reg_id) AS visit_count,
       COUNT(DISTINCT op.presc_id) AS prescription_count
FROM doctor d
JOIN department dep ON d.dept_id = dep.dept_id
LEFT JOIN registration r ON d.doctor_id = r.doctor_id AND r.reg_status = '已就诊'
  AND r.reg_date BETWEEN ? AND ?
LEFT JOIN outpatient_prescription op ON d.doctor_id = op.doctor_id
  AND op.presc_time BETWEEN ? AND ?
GROUP BY d.doctor_id, d.name, d.title, dep.dept_name
ORDER BY visit_count DESC;


-- ----------------------------------------------------------
-- 11.2 排班统计（按日期范围）
-- ----------------------------------------------------------
SELECT d.name AS doctor_name, dep.dept_name,
       s.sched_date, s.sched_type, s.start_time, s.end_time, s.clinic
FROM schedule s
JOIN doctor d ON s.doctor_id = d.doctor_id
JOIN department dep ON d.dept_id = dep.dept_id
WHERE s.sched_date BETWEEN ? AND ?
ORDER BY s.sched_date, s.start_time;


-- ----------------------------------------------------------
-- 11.3 科室工作量统计
-- ----------------------------------------------------------
SELECT dep.dept_id, dep.dept_name,
       COUNT(DISTINCT r.reg_id) AS total_registrations,
       COUNT(DISTINCT op.presc_id) AS total_prescriptions,
       COUNT(DISTINCT af.file_no) AS total_admissions
FROM department dep
LEFT JOIN doctor d ON dep.dept_id = d.dept_id
LEFT JOIN registration r ON d.doctor_id = r.doctor_id AND r.reg_status = '已就诊'
LEFT JOIN outpatient_prescription op ON d.doctor_id = op.doctor_id
LEFT JOIN admission_file af ON d.doctor_id = af.doctor_id
GROUP BY dep.dept_id, dep.dept_name
ORDER BY total_registrations DESC;


-- ----------------------------------------------------------
-- 11.4 药品使用统计
-- ----------------------------------------------------------
SELECT m.medicine_id, m.med_name, m.specification, m.unit,
       SUM(pd.qty) AS total_qty_used,
       SUM(pd.qty * m.unit_price) AS total_revenue,
       COUNT(DISTINCT pd.presc_id) AS prescription_count
FROM medicine m
JOIN prescription_detail pd ON m.medicine_id = pd.medicine_id
GROUP BY m.medicine_id, m.med_name, m.specification, m.unit
ORDER BY total_qty_used DESC;


-- ----------------------------------------------------------
-- 11.5 住院统计（在院人数、床位使用率）
-- ----------------------------------------------------------
SELECT dep.dept_id, dep.dept_name,
       COUNT(DISTINCT w.ward_id) AS ward_count,
       SUM(w.total_beds) AS total_beds,
       SUM(w.occupied_cnt) AS occupied_beds,
       ROUND(SUM(w.occupied_cnt) / SUM(w.total_beds) * 100, 1) AS occupancy_rate
FROM department dep
JOIN ward w ON dep.dept_id = w.dept_id
GROUP BY dep.dept_id, dep.dept_name
ORDER BY occupancy_rate DESC;
