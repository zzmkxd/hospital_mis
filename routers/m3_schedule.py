"""
M3 排班管理路由
--------------
对应 SQL 文件：sql/m3_schedule.sql

重叠判定公式：A.start_time < B.end_time AND A.end_time > B.start_time
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute
from schemas.m3_schedule import ScheduleCreate, ScheduleUpdate
from schemas.common import MessageResponse

router = APIRouter()


@router.get("", summary="查看排班列表")
def list_schedules():
    """对应 SQL 4.1 — 含医生姓名、科室名称"""
    return query(
        "SELECT s.schedule_id, s.sched_date, s.start_time, s.end_time, "
        "       s.sched_type, s.clinic, "
        "       d.doctor_id, d.name AS doctor_name, d.title, dep.dept_name "
        "FROM schedule s "
        "JOIN doctor d ON s.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "ORDER BY s.sched_date DESC, s.start_time"
    )


@router.post("", status_code=201, summary="创建排班")
def create_schedule(data: ScheduleCreate):
    """
    创建前执行 3 层冲突检测：
      R03 — 同一医生同日时间段不重叠
      R04 — 同一诊室同时段不冲突（仅门诊坐诊）
    对应 SQL 4.2 + 4.3
    """
    # 检测1（R03）：医生时间冲突
    conflict = query_one(
        "SELECT COUNT(*) AS cnt FROM schedule "
        "WHERE doctor_id = %s AND sched_date = %s AND start_time < %s AND end_time > %s",
        (data.doctor_id, data.sched_date, data.end_time, data.start_time)
    )
    if conflict["cnt"] > 0:
        raise HTTPException(409, "该医生在此时段已有排班")

    # 检测2（R04）：诊室冲突（仅门诊坐诊）
    if data.sched_type == "门诊坐诊":
        room_conflict = query_one(
            "SELECT COUNT(*) AS cnt FROM schedule "
            "WHERE clinic = %s AND sched_date = %s AND sched_type = '门诊坐诊' "
            "  AND start_time < %s AND end_time > %s",
            (data.clinic, data.sched_date, data.end_time, data.start_time)
        )
        if room_conflict["cnt"] > 0:
            raise HTTPException(409, "该诊室在此时段已被占用")

    schedule_id = execute(
        "INSERT INTO schedule (doctor_id, sched_date, start_time, end_time, sched_type, clinic) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (data.doctor_id, data.sched_date, data.start_time, data.end_time,
         data.sched_type, data.clinic)
    )
    return {"schedule_id": schedule_id, "message": "排班创建成功"}


@router.put("/{schedule_id}", summary="修改排班")
def update_schedule(schedule_id: int, data: ScheduleUpdate):
    """
    冲突检测逻辑与创建相同，额外排除自身：AND schedule_id != ?
    对应 SQL 4.4 + 4.2（编辑时排除自身）
    """
    conflict = query_one(
        "SELECT COUNT(*) AS cnt FROM schedule "
        "WHERE doctor_id = %s AND sched_date = %s AND start_time < %s AND end_time > %s "
        "  AND schedule_id != %s",
        (data.doctor_id, data.sched_date, data.end_time, data.start_time, schedule_id)
    )
    if conflict["cnt"] > 0:
        raise HTTPException(409, "该医生在此时段已有排班")

    if data.sched_type == "门诊坐诊":
        room_conflict = query_one(
            "SELECT COUNT(*) AS cnt FROM schedule "
            "WHERE clinic = %s AND sched_date = %s AND sched_type = '门诊坐诊' "
            "  AND start_time < %s AND end_time > %s AND schedule_id != %s",
            (data.clinic, data.sched_date, data.end_time, data.start_time, schedule_id)
        )
        if room_conflict["cnt"] > 0:
            raise HTTPException(409, "该诊室在此时段已被占用")

    affected = execute(
        "UPDATE schedule SET doctor_id=%s, sched_date=%s, start_time=%s, end_time=%s, "
        "sched_type=%s, clinic=%s WHERE schedule_id=%s",
        (data.doctor_id, data.sched_date, data.start_time, data.end_time,
         data.sched_type, data.clinic, schedule_id)
    )
    if not affected:
        raise HTTPException(404, "排班记录不存在")
    return MessageResponse(message="排班已更新", affected_rows=affected)


@router.delete("/{schedule_id}", summary="删除排班")
def delete_schedule(schedule_id: int):
    """对应 SQL 4.5"""
    execute("DELETE FROM schedule WHERE schedule_id = %s", (schedule_id,))
    return MessageResponse(message="排班已删除", affected_rows=1)
