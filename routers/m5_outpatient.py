"""
M5 医生门诊接诊与处方路由
------------------------
对应 SQL 文件：sql/m5_outpatient_consultation.sql

门诊处方 = 1 条 outpatient_prescription + N 条 prescription_detail（presc_type='门诊'）
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute, transaction
from schemas.m5_outpatient import OutpatientPrescriptionCreate
from schemas.common import MessageResponse

router = APIRouter()


@router.get("/queue", summary="接诊队列")
def consultation_queue(doctor_id: int):
    """
    医生视角：待就诊病人列表。
    对应 SQL 6.1
    """
    return query(
        "SELECT r.reg_id, r.case_no, r.reg_type, r.reg_date, "
        "       p.name AS patient_name, p.gender, p.age "
        "FROM registration r "
        "JOIN patient p ON r.case_no = p.case_no "
        "WHERE r.doctor_id = %s "
        "  AND r.reg_status = '待就诊' "
        "ORDER BY r.reg_date",
        (doctor_id,)
    )


@router.put("/consult/{reg_id}", summary="接诊")
def start_consultation(reg_id: int):
    """
    将挂号状态从 待就诊 → 已就诊。
    对应 SQL 6.2
    """
    affected = execute(
        "UPDATE registration SET reg_status = '已就诊' WHERE reg_id = %s",
        (reg_id,)
    )
    if not affected:
        raise HTTPException(404, "挂号记录不存在")
    return MessageResponse(message="已接诊", affected_rows=affected)


@router.get("/medicines", summary="可用药品列表")
def list_available_medicines():
    """
    R12：只展示库存 > 0 的药品。
    对应 SQL 6.3
    """
    return query(
        "SELECT medicine_id, med_name, specification, unit, unit_price, stock_qty "
        "FROM medicine WHERE stock_qty > 0 ORDER BY med_name"
    )


@router.post("/prescriptions", status_code=201, summary="开具门诊处方")
def create_outpatient_prescription(data: OutpatientPrescriptionCreate):
    """
    事务三步：
      A. 创建门诊处方主记录（pay_status='待支付'）
      B. 逐条添加处方明细（presc_type='门诊'）
      C.（可选）扣减库存
    对应 SQL 6.4
    """
    with transaction() as conn:
        # Step A：创建处方主记录
        presc_id = execute(
            "INSERT INTO outpatient_prescription (reg_id, doctor_id, symptom_desc, pay_status) "
            "VALUES (%s, %s, %s, '待支付')",
            (data.reg_id, data.doctor_id, data.symptom_desc),
            conn=conn
        )

        # Step B：逐条添加处方明细
        for item in data.details:
            execute(
                "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
                "VALUES (%s, '门诊', %s, %s, %s)",
                (presc_id, item.medicine_id, item.qty, item.usage_inst),
                conn=conn
            )

        # Step C（可选）：扣减库存
        if data.deduct_stock:
            for item in data.details:
                affected = execute(
                    "UPDATE medicine SET stock_qty = stock_qty - %s "
                    "WHERE medicine_id = %s AND stock_qty >= %s",
                    (item.qty, item.medicine_id, item.qty),
                    conn=conn
                )
                if not affected:
                    raise HTTPException(400, f"药品 {item.medicine_id} 库存不足")

    # 计算费用
    fee = query_one(
        "SELECT d.consultation_fee "
        "     + COALESCE(SUM(pd.qty * m.unit_price), 0) AS total_fee, "
        "       d.consultation_fee, "
        "       COALESCE(SUM(pd.qty * m.unit_price), 0) AS drug_fee "
        "FROM outpatient_prescription op "
        "JOIN doctor d ON op.doctor_id = d.doctor_id "
        "LEFT JOIN prescription_detail pd ON pd.presc_id = op.presc_id AND pd.presc_type = '门诊' "
        "LEFT JOIN medicine m ON pd.medicine_id = m.medicine_id "
        "WHERE op.presc_id = %s "
        "GROUP BY op.presc_id, d.consultation_fee",
        (presc_id,)
    )

    return {
        "presc_id": presc_id,
        "consultation_fee": fee["consultation_fee"] if fee else 0,
        "drug_fee": fee["drug_fee"] if fee else 0,
        "total_fee": fee["total_fee"] if fee else 0,
        "message": "处方开具成功",
    }


@router.get("/prescriptions/{presc_id}", summary="处方明细")
def get_prescription_detail(presc_id: int):
    """
    含每条明细的小计（qty × unit_price）。
    对应 SQL 6.5
    """
    details = query(
        "SELECT pd.detail_id, pd.qty, pd.usage_inst, "
        "       m.med_name, m.specification, m.unit, m.unit_price, "
        "       (pd.qty * m.unit_price) AS line_total "
        "FROM prescription_detail pd "
        "JOIN medicine m ON pd.medicine_id = m.medicine_id "
        "WHERE pd.presc_type = '门诊' AND pd.presc_id = %s",
        (presc_id,)
    )

    total = query_one(
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

    return {
        "presc_id": presc_id,
        "details": details,
        "total_fee": total["total_fee"] if total else 0,
    }
