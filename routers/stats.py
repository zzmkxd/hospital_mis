"""
统计查询路由
-----------
对应 SQL 文件：sql/stats_queries.sql

5 类统计：医生工作量、排班、科室、药品、床位使用率
"""
from fastapi import APIRouter
from db import query
from schemas.stats import DateRangeQuery

router = APIRouter()


@router.get("/doctors", summary="医生工作量统计")
def doctor_workload(start_date: str, end_date: str):
    """
    R30：按医生聚合已就诊挂号数 + 门诊处方数。
    对应 SQL 11.1
    """
    return query(
        "SELECT d.doctor_id, d.name, d.title, dep.dept_name, "
        "       COUNT(DISTINCT r.reg_id) AS visit_count, "
        "       COUNT(DISTINCT op.presc_id) AS prescription_count "
        "FROM doctor d "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "LEFT JOIN registration r ON d.doctor_id = r.doctor_id AND r.reg_status = '已就诊' "
        "  AND r.reg_date BETWEEN %s AND %s "
        "LEFT JOIN outpatient_prescription op ON d.doctor_id = op.doctor_id "
        "  AND op.presc_time BETWEEN %s AND %s "
        "GROUP BY d.doctor_id, d.name, d.title, dep.dept_name "
        "ORDER BY visit_count DESC",
        (start_date, end_date, start_date, end_date)
    )


@router.get("/schedules", summary="排班统计")
def schedule_stats(start_date: str, end_date: str):
    """
    按日期范围查看所有排班。
    对应 SQL 11.2
    """
    return query(
        "SELECT d.name AS doctor_name, dep.dept_name, "
        "       s.sched_date, s.sched_type, s.start_time, s.end_time, s.clinic "
        "FROM schedule s "
        "JOIN doctor d ON s.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "WHERE s.sched_date BETWEEN %s AND %s "
        "ORDER BY s.sched_date, s.start_time",
        (start_date, end_date)
    )


@router.get("/departments", summary="科室工作量统计")
def department_workload():
    """
    按科室聚合挂号数、门诊处方数、住院人数。
    对应 SQL 11.3
    """
    return query(
        "SELECT dep.dept_id, dep.dept_name, "
        "       COUNT(DISTINCT r.reg_id) AS total_registrations, "
        "       COUNT(DISTINCT op.presc_id) AS total_prescriptions, "
        "       COUNT(DISTINCT af.file_no) AS total_admissions "
        "FROM department dep "
        "LEFT JOIN doctor d ON dep.dept_id = d.dept_id "
        "LEFT JOIN registration r ON d.doctor_id = r.doctor_id AND r.reg_status = '已就诊' "
        "LEFT JOIN outpatient_prescription op ON d.doctor_id = op.doctor_id "
        "LEFT JOIN admission_file af ON d.doctor_id = af.doctor_id "
        "GROUP BY dep.dept_id, dep.dept_name "
        "ORDER BY total_registrations DESC"
    )


@router.get("/medicines", summary="药品使用统计")
def medicine_stats():
    """
    按药品聚合用量、收入、处方数。
    对应 SQL 11.4
    """
    return query(
        "SELECT m.medicine_id, m.med_name, m.specification, m.unit, "
        "       SUM(pd.qty) AS total_qty_used, "
        "       SUM(pd.qty * m.unit_price) AS total_revenue, "
        "       COUNT(DISTINCT pd.presc_id) AS prescription_count "
        "FROM medicine m "
        "JOIN prescription_detail pd ON m.medicine_id = pd.medicine_id "
        "GROUP BY m.medicine_id, m.med_name, m.specification, m.unit "
        "ORDER BY total_qty_used DESC"
    )


@router.get("/beds", summary="床位使用率统计")
def bed_occupancy():
    """
    按科室聚合病房数、床位总数、占用数、使用率。
    对应 SQL 11.5
    """
    return query(
        "SELECT dep.dept_id, dep.dept_name, "
        "       COUNT(DISTINCT w.ward_id) AS ward_count, "
        "       SUM(w.total_beds) AS total_beds, "
        "       SUM(w.occupied_cnt) AS occupied_beds, "
        "       ROUND(SUM(w.occupied_cnt) / SUM(w.total_beds) * 100, 1) AS occupancy_rate "
        "FROM department dep "
        "JOIN ward w ON dep.dept_id = w.dept_id "
        "GROUP BY dep.dept_id, dep.dept_name "
        "ORDER BY occupancy_rate DESC"
    )
