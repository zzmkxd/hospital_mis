"""
M2 管理员基础数据维护路由
--------------------------
对应 SQL 文件：sql/m2_admin_maintenance.sql
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute, transaction
from schemas.m2_admin import (
    DepartmentCreate, DepartmentUpdate,
    DoctorCreate, DoctorUpdate,
    MedicineCreate, MedicineUpdate,
)
from schemas.common import MessageResponse, ErrorResponse

router = APIRouter()


# ============================================================
# 科室 (department)
# ============================================================

@router.get("/departments", summary="查询科室列表")
def list_departments():
    """对应 SQL 3.1 查询科室列表"""
    return query("SELECT dept_id, dept_name, dept_type, phone FROM department ORDER BY dept_id")


@router.post("/departments", status_code=201, summary="新增科室")
def create_department(data: DepartmentCreate):
    """对应 SQL 3.1 新增科室"""
    dept_id = execute(
        "INSERT INTO department (dept_name, dept_type, phone) VALUES (%s, %s, %s)",
        (data.dept_name, data.dept_type, data.phone)
    )
    return {"dept_id": dept_id, "message": "科室创建成功"}


@router.put("/departments/{dept_id}", summary="修改科室")
def update_department(dept_id: int, data: DepartmentUpdate):
    """对应 SQL 3.1 修改科室"""
    affected = execute(
        "UPDATE department SET dept_name=%s, dept_type=%s, phone=%s WHERE dept_id=%s",
        (data.dept_name, data.dept_type, data.phone, dept_id)
    )
    if not affected:
        raise HTTPException(404, "科室不存在")
    return MessageResponse(message="科室已更新", affected_rows=affected)


@router.delete("/departments/{dept_id}", summary="删除科室")
def delete_department(dept_id: int):
    """
    删除科室前置检查：
      1. 是否有归属医生
      2. 是否有归属病房
    两项均为 0 才可删除。
    对应 SQL 3.1 删除科室前置检查
    """
    doctors = query_one("SELECT COUNT(*) AS cnt FROM doctor WHERE dept_id = %s", (dept_id,))
    wards   = query_one("SELECT COUNT(*) AS cnt FROM ward WHERE dept_id = %s", (dept_id,))
    if doctors["cnt"] > 0:
        raise HTTPException(400, "该科室下仍有医生，无法删除")
    if wards["cnt"] > 0:
        raise HTTPException(400, "该科室下仍有病房，无法删除")
    execute("DELETE FROM department WHERE dept_id = %s", (dept_id,))
    return MessageResponse(message="科室已删除", affected_rows=1)


# ============================================================
# 医生 (doctor)
# ============================================================

@router.get("/doctors", summary="查询医生列表")
def list_doctors():
    """对应 SQL 3.2 查询医生列表"""
    return query(
        "SELECT d.doctor_id, d.dept_id, d.name, d.gender, d.title, d.consultation_fee, d.phone, "
        "       dep.dept_name "
        "FROM doctor d JOIN department dep ON d.dept_id = dep.dept_id "
        "ORDER BY d.doctor_id"
    )


@router.post("/doctors", status_code=201, summary="新增医生")
def create_doctor(data: DoctorCreate):
    """
    事务：INSERT doctor + INSERT account。
    对应 SQL 3.2 新增医生 + 创建账号
    """
    with transaction() as conn:
        doctor_id = execute(
            "INSERT INTO doctor (name, gender, title, consultation_fee, phone, dept_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (data.name, data.gender, data.title, data.consultation_fee, data.phone, data.dept_id),
            conn=conn
        )
        execute(
            "INSERT INTO account (ref_id, role, password_hash) VALUES (%s, %s, %s)",
            (doctor_id, "医生", data.password),  # TODO: bcrypt 哈希
            conn=conn
        )
    return {"doctor_id": doctor_id, "message": "医生及账号创建成功"}


@router.put("/doctors/{doctor_id}", summary="修改医生")
def update_doctor(doctor_id: int, data: DoctorUpdate):
    """对应 SQL 3.2 修改医生"""
    affected = execute(
        "UPDATE doctor SET name=%s, gender=%s, title=%s, consultation_fee=%s, phone=%s, dept_id=%s "
        "WHERE doctor_id=%s",
        (data.name, data.gender, data.title, data.consultation_fee, data.phone, data.dept_id, doctor_id)
    )
    if not affected:
        raise HTTPException(404, "医生不存在")
    return MessageResponse(message="医生已更新", affected_rows=affected)


@router.delete("/doctors/{doctor_id}", summary="删除医生")
def delete_doctor(doctor_id: int):
    """
    删除前置 3 项检查：
      1. 未来排班
      2. 待就诊挂号
      3. 在院病人（未出院档案）
    三项均为 0 才可删除。
    事务：删除 doctor + 级联删除 account。
    """
    sched = query_one(
        "SELECT COUNT(*) AS cnt FROM schedule WHERE doctor_id=%s AND sched_date >= CURDATE()",
        (doctor_id,)
    )
    reg = query_one(
        "SELECT COUNT(*) AS cnt FROM registration WHERE doctor_id=%s AND reg_status='待就诊'",
        (doctor_id,)
    )
    adm = query_one(
        "SELECT COUNT(*) AS cnt FROM admission_file WHERE doctor_id=%s AND discharge_time IS NULL",
        (doctor_id,)
    )
    if sched["cnt"] > 0:
        raise HTTPException(400, "该医生仍有未来排班，无法删除")
    if reg["cnt"] > 0:
        raise HTTPException(400, "该医生仍有待就诊挂号，无法删除")
    if adm["cnt"] > 0:
        raise HTTPException(400, "该医生仍有在院病人，无法删除")

    # 事务：删除医生 + 级联删除关联账号
    with transaction() as conn:
        execute(
            "DELETE FROM account WHERE ref_id = %s AND role = '医生'",
            (doctor_id,), conn=conn
        )
        execute("DELETE FROM doctor WHERE doctor_id = %s", (doctor_id,), conn=conn)

    return MessageResponse(message="医生及关联账号已删除", affected_rows=1)


# ============================================================
# 药品 (medicine)
# ============================================================

@router.get("/medicines", summary="查询药品列表")
def list_medicines():
    """对应 SQL 3.3 查询药品列表"""
    return query(
        "SELECT medicine_id, med_name, specification, unit, unit_price, stock_qty "
        "FROM medicine ORDER BY med_name"
    )


@router.post("/medicines", status_code=201, summary="新增药品")
def create_medicine(data: MedicineCreate):
    """对应 SQL 3.3 新增药品"""
    med_id = execute(
        "INSERT INTO medicine (med_name, specification, unit, unit_price, stock_qty) "
        "VALUES (%s, %s, %s, %s, %s)",
        (data.med_name, data.specification, data.unit, data.unit_price, data.stock_qty)
    )
    return {"medicine_id": med_id, "message": "药品创建成功"}


@router.put("/medicines/{medicine_id}", summary="修改药品")
def update_medicine(medicine_id: int, data: MedicineUpdate):
    """对应 SQL 3.3 修改药品"""
    affected = execute(
        "UPDATE medicine SET med_name=%s, specification=%s, unit=%s, unit_price=%s, stock_qty=%s "
        "WHERE medicine_id=%s",
        (data.med_name, data.specification, data.unit, data.unit_price, data.stock_qty, medicine_id)
    )
    if not affected:
        raise HTTPException(404, "药品不存在")
    return MessageResponse(message="药品已更新", affected_rows=affected)
