-- ============================================================
-- M2 管理员基础数据维护 SQL
-- 对应开发文档第三章
-- ============================================================

-- ----------------------------------------------------------
-- 3.1 科室管理 (department)
-- ----------------------------------------------------------

-- 查询科室列表
SELECT dept_id, dept_name, dept_type, phone
FROM department
ORDER BY dept_id;

-- 新增科室
INSERT INTO department (dept_name, dept_type, phone)
VALUES (?, ?, ?);

-- 修改科室
UPDATE department
SET dept_name = ?, dept_type = ?, phone = ?
WHERE dept_id = ?;

-- 删除科室前置检查1：是否有归属医生
SELECT COUNT(*) AS cnt FROM doctor WHERE dept_id = ?;

-- 删除科室前置检查2：是否有归属病房
SELECT COUNT(*) AS cnt FROM ward WHERE dept_id = ?;

-- 两项均为 0 才可删除
DELETE FROM department WHERE dept_id = ?;


-- ----------------------------------------------------------
-- 3.2 医生管理 (doctor)
-- ----------------------------------------------------------

-- 查询医生列表（含科室名称）
SELECT d.doctor_id, d.name, d.gender, d.title, d.consultation_fee, d.phone,
       dep.dept_name
FROM doctor d
JOIN department dep ON d.dept_id = dep.dept_id
ORDER BY d.doctor_id;

-- 新增医生 + 创建账号（事务）
-- 事务开始
INSERT INTO doctor (name, gender, title, consultation_fee, phone, dept_id)
VALUES (?, ?, ?, ?, ?, ?);
-- 获取 LAST_INSERT_ID() 作为 doctor_id

INSERT INTO account (ref_id, role, password_hash)
VALUES (?, '医生', ?);
-- 事务提交

-- 修改医生
UPDATE doctor
SET name = ?, gender = ?, title = ?, consultation_fee = ?, phone = ?, dept_id = ?
WHERE doctor_id = ?;

-- 删除医生前置检查1：未来排班
SELECT COUNT(*) AS cnt FROM schedule
WHERE doctor_id = ? AND sched_date >= CURDATE();

-- 删除医生前置检查2：待就诊挂号
SELECT COUNT(*) AS cnt FROM registration
WHERE doctor_id = ? AND reg_status = '待就诊';

-- 删除医生前置检查3：在院病人（该医生为主治医生的未出院档案）
SELECT COUNT(*) AS cnt FROM admission_file
WHERE doctor_id = ? AND discharge_time IS NULL;

-- 三项均为 0 才可删除
DELETE FROM doctor WHERE doctor_id = ?;


-- ----------------------------------------------------------
-- 3.3 药品管理 (medicine)
-- ----------------------------------------------------------

-- 查询药品列表
SELECT medicine_id, med_name, specification, unit, unit_price, stock_qty
FROM medicine
ORDER BY med_name;

-- 新增药品
INSERT INTO medicine (med_name, specification, unit, unit_price, stock_qty)
VALUES (?, ?, ?, ?, ?);

-- 修改药品
UPDATE medicine
SET med_name = ?, specification = ?, unit = ?, unit_price = ?, stock_qty = ?
WHERE medicine_id = ?;
