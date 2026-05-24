"""
M4 病人挂号路由
--------------
对应 SQL 文件：sql/m4_registration.sql
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute
from schemas.m4_registration import RegistrationCreate, AvailableDoctorsQuery
from schemas.common import MessageResponse

router = APIRouter()


@router.get("/doctors", summary="查询可选医生列表")
def list_available_doctors(dept_id: int, target_date: str):
    """
    查询某科室某日所有门诊坐诊医生。
    对应 SQL 5.1
    """
    return query(
        "SELECT d.doctor_id, d.name, d.title, d.consultation_fee, "
        "       s.schedule_id, s.sched_date, s.start_time, s.end_time, s.clinic "
        "FROM schedule s "
        "JOIN doctor d ON s.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "WHERE dep.dept_id = %s "
        "  AND s.sched_type = '门诊坐诊' "
        "  AND s.sched_date = %s "
        "ORDER BY s.start_time",
        (dept_id, target_date)
    )


@router.get("/visit-type", summary="判断初诊/复诊")
def check_visit_type(case_no: int):
    """
    有已就诊记录 → 复诊，否则 → 初诊。
    对应 SQL 5.2
    """
    row = query_one(
        "SELECT COUNT(*) AS history_cnt FROM registration "
        "WHERE case_no = %s AND reg_status = '已就诊'",
        (case_no,)
    )
    return {"case_no": case_no, "reg_type": "复诊" if row["history_cnt"] > 0 else "初诊"}


@router.post("", status_code=201, summary="创建挂号")
def create_registration(data: RegistrationCreate):
    """
    对应 SQL 5.3
    """
    reg_id = execute(
        "INSERT INTO registration (case_no, doctor_id, schedule_id, reg_type, reg_status) "
        "VALUES (%s, %s, %s, %s, '待就诊')",
        (data.case_no, data.doctor_id, data.schedule_id, data.reg_type)
    )
    return {"reg_id": reg_id, "message": "挂号成功"}


@router.get("/my", summary="查看我的挂号列表")
def list_my_registrations(case_no: int):
    """
    病人视角：查看自己的所有挂号记录。
    对应 SQL 5.4
    """
    return query(
        "SELECT r.reg_id, r.reg_date, r.reg_type, r.reg_status, "
        "       d.name AS doctor_name, d.title, "
        "       dep.dept_name, s.sched_date, s.start_time, s.end_time, s.clinic "
        "FROM registration r "
        "JOIN doctor d ON r.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "JOIN schedule s ON r.schedule_id = s.schedule_id "
        "WHERE r.case_no = %s "
        "ORDER BY r.reg_date DESC",
        (case_no,)
    )


@router.put("/{reg_id}/cancel", summary="取消挂号")
def cancel_registration(reg_id: int):
    """
    仅待就诊状态可取消。
    对应 SQL 5.5
    """
    affected = execute(
        "UPDATE registration SET reg_status = '已取消' "
        "WHERE reg_id = %s AND reg_status = '待就诊'",
        (reg_id,)
    )
    if not affected:
        raise HTTPException(400, "挂号不存在或状态不允许取消")
    return MessageResponse(message="挂号已取消", affected_rows=affected)
