"""
M7 住院登记（入院）路由
-----------------------
对应 SQL 文件：sql/m7_admission.sql

一次入院涉及 6 张表的原子更新，在事务中执行：
  bed (FOR UPDATE 锁) → admission_file (INSERT) → patient (UPDATE)
  → bed (UPDATE) → ward (UPDATE)
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute, transaction
from schemas.m7_admission import AdmissionCreate
from schemas.common import MessageResponse

router = APIRouter()


@router.get("/wards", summary="查询可选病房")
def list_available_wards(dept_id: int):
    """
    筛选科室对口 + 有空床的病房。
    返回 available_beds = total_beds - occupied_cnt。
    对应 SQL 8.1
    """
    return query(
        "SELECT w.ward_id, w.ward_no, w.location, w.charge_rate, "
        "       w.total_beds, w.occupied_cnt, "
        "       (w.total_beds - w.occupied_cnt) AS available_beds "
        "FROM ward w "
        "WHERE w.dept_id = %s AND w.occupied_cnt < w.total_beds",
        (dept_id,)
    )


@router.get("/beds", summary="查询可选床位")
def list_available_beds(ward_id: int):
    """
    选定病房后，仅返回空闲床位。
    对应 SQL 8.2
    """
    return query(
        "SELECT bed_id, bed_no FROM bed WHERE ward_id = %s AND bed_status = '空闲'",
        (ward_id,)
    )


@router.post("", status_code=201, summary="办理入院")
def create_admission(data: AdmissionCreate):
    """
    事务五步（对应 SQL 8.3）：
      A. FOR UPDATE 锁定床位，防并发
      B. 创建住院档案
      C. 更新病人状态（R20）
      D. 更新床位状态
      E. 病房入住人数 +1
    """
    with transaction() as conn:
        # Step A：锁定床位
        bed = query_one(
            "SELECT bed_id, bed_status FROM bed WHERE bed_id = %s FOR UPDATE",
            (data.bed_id,),
        )
        if not bed:
            raise HTTPException(404, "床位不存在")
        if bed["bed_status"] != "空闲":
            raise HTTPException(409, "床位已被占用")

        # Step B：创建住院档案
        file_no = execute(
            "INSERT INTO admission_file (case_no, doctor_id, ward_id, bed_id, deposit_balance) "
            "VALUES (%s, %s, %s, %s, %s)",
            (data.case_no, data.doctor_id, data.ward_id, data.bed_id, data.deposit_balance),
            conn=conn
        )

        # Step C：更新病人状态（R20：病人状态与住院档案同步）
        execute(
            "UPDATE patient SET is_inpatient = '是', ward_id = %s, bed_id = %s "
            "WHERE case_no = %s",
            (data.ward_id, data.bed_id, data.case_no),
            conn=conn
        )

        # Step D：更新床位状态
        execute(
            "UPDATE bed SET bed_status = '占用' WHERE bed_id = %s",
            (data.bed_id,),
            conn=conn
        )

        # Step E：更新病房入住人数
        execute(
            "UPDATE ward SET occupied_cnt = occupied_cnt + 1 WHERE ward_id = %s",
            (data.ward_id,),
            conn=conn
        )

    return {"file_no": file_no, "message": "入院登记成功"}


@router.get("", summary="在院病人列表")
def list_inpatients():
    """
    管理员/医生视角：所有在院病人（discharge_time IS NULL）。
    对应 SQL 8.4
    """
    return query(
        "SELECT af.file_no, af.case_no, af.admit_time, af.deposit_balance, "
        "       p.name AS patient_name, p.gender, p.age, "
        "       d.name AS doctor_name, "
        "       w.ward_no, b.bed_no "
        "FROM admission_file af "
        "JOIN patient p ON af.case_no = p.case_no "
        "JOIN doctor d ON af.doctor_id = d.doctor_id "
        "JOIN ward w ON af.ward_id = w.ward_id "
        "JOIN bed b ON af.bed_id = b.bed_id "
        "WHERE af.discharge_time IS NULL "
        "ORDER BY af.admit_time"
    )
