"""
M6 病人缴费与历史查看路由
-------------------------
对应 SQL 文件：sql/m6_patient_payment.sql
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute
from schemas.m6_payment import PaymentRequest
from schemas.common import MessageResponse

router = APIRouter()


@router.get("/unpaid", summary="待支付处方列表")
def list_unpaid_prescriptions(case_no: int):
    """
    病人视角：查看自己所有待支付的门诊处方。
    对应 SQL 7.1
    """
    return query(
        "SELECT op.presc_id, op.presc_time, op.symptom_desc, op.pay_status, "
        "       d.name AS doctor_name, d.consultation_fee, dep.dept_name "
        "FROM outpatient_prescription op "
        "JOIN registration r ON op.reg_id = r.reg_id "
        "JOIN doctor d ON op.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "WHERE r.case_no = %s AND op.pay_status = '待支付' "
        "ORDER BY op.presc_time DESC",
        (case_no,)
    )


@router.get("/prescriptions/{presc_id}/fee", summary="处方费用汇总")
def get_prescription_fee(presc_id: int):
    """
    诊疗费 + 药费（Σ qty × unit_price）。
    对应 SQL 7.2
    """
    row = query_one(
        "SELECT d.consultation_fee "
        "     + COALESCE(SUM(pd.qty * m.unit_price), 0) AS total_fee "
        "FROM outpatient_prescription op "
        "JOIN doctor d ON op.doctor_id = d.doctor_id "
        "LEFT JOIN prescription_detail pd ON pd.presc_id = op.presc_id AND pd.presc_type = '门诊' "
        "LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id "
        "WHERE op.presc_id = %s "
        "GROUP BY op.presc_id, d.consultation_fee",
        (presc_id,)
    )
    if not row:
        raise HTTPException(404, "处方不存在")
    return {"presc_id": presc_id, "total_fee": row["total_fee"]}


@router.post("/pay", summary="支付处方")
def pay_prescription(data: PaymentRequest):
    """
    仅待支付状态可支付。
    对应 SQL 7.3
    """
    affected = execute(
        "UPDATE outpatient_prescription SET pay_status = '已支付' "
        "WHERE presc_id = %s AND pay_status = '待支付'",
        (data.presc_id,)
    )
    if not affected:
        raise HTTPException(400, "处方不存在或已支付")
    return MessageResponse(message="支付成功", affected_rows=affected)


@router.get("/history/outpatient", summary="门诊历史")
def outpatient_history(case_no: int):
    """
    R31 门诊部分：挂号 → 处方 → 支付全链路。
    对应 SQL 7.4
    """
    return query(
        "SELECT '门诊' AS record_type, r.reg_date AS time, op.presc_time, "
        "       d.name AS doctor_name, dep.dept_name, op.symptom_desc, op.pay_status "
        "FROM registration r "
        "LEFT JOIN outpatient_prescription op ON r.reg_id = op.reg_id "
        "JOIN doctor d ON r.doctor_id = d.doctor_id "
        "JOIN department dep ON d.dept_id = dep.dept_id "
        "WHERE r.case_no = %s "
        "ORDER BY r.reg_date DESC",
        (case_no,)
    )


@router.get("/history/inpatient", summary="住院历史")
def inpatient_history(case_no: int):
    """
    R31 住院部分：入院档案 → 出院结算全链路。
    对应 SQL 7.5
    """
    return query(
        "SELECT af.file_no, '住院' AS record_type, af.admit_time, af.discharge_time, "
        "       d.name AS doctor_name, w.ward_no, b.bed_no, af.deposit_balance "
        "FROM admission_file af "
        "JOIN doctor d ON af.doctor_id = d.doctor_id "
        "JOIN ward w ON af.ward_id = w.ward_id "
        "JOIN bed b ON af.bed_id = b.bed_id "
        "WHERE af.case_no = %s "
        "ORDER BY af.admit_time DESC",
        (case_no,)
    )


@router.get("/history/inpatient/{file_no}/costs", summary="住院费用明细")
def inpatient_cost_detail(file_no: int):
    """
    某次住院的每日费用明细（含药品明细）。
    对应 SQL 7.6
    """
    return query(
        "SELECT ir.record_date, ir.treatment_desc, ir.daily_fee, "
        "       ip.presc_id, ip.presc_time, "
        "       pd.qty, pd.usage_inst, "
        "       m.med_name, m.unit_price, (pd.qty * m.unit_price) AS drug_cost "
        "FROM inpatient_record ir "
        "LEFT JOIN inpatient_prescription ip ON ir.record_id = ip.record_id "
        "LEFT JOIN prescription_detail pd ON pd.presc_id = ip.presc_id AND pd.presc_type = '住院' "
        "LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id "
        "WHERE ir.file_no = %s "
        "ORDER BY ir.record_date DESC, ip.presc_time",
        (file_no,)
    )
