"""
M8 医生每日查房路由
--------------------
对应 SQL 文件：sql/m8_daily_rounds.sql

每日查房 = 1 条 inpatient_record + 1 张 inpatient_prescription + N 条 prescription_detail
当日费用 = 床位费(charge_rate) + 药费(Σ qty × unit_price)
事务内扣减预交金，余额不足自动回滚。
"""
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute, transaction
from schemas.m8_daily_rounds import DailyRoundCreate
from schemas.common import MessageResponse

router = APIRouter()


@router.get("/my-inpatients", summary="我的在院病人")
def list_my_inpatients(doctor_id: int):
    """
    医生视角：查看自己负责的住院病人。
    对应 SQL 9.1
    """
    return query(
        "SELECT af.file_no, af.case_no, af.admit_time, af.deposit_balance, "
        "       p.name AS patient_name, p.gender, p.age, "
        "       w.ward_no, w.charge_rate, b.bed_no "
        "FROM admission_file af "
        "JOIN patient p ON af.case_no = p.case_no "
        "JOIN ward w ON af.ward_id = w.ward_id "
        "JOIN bed b ON af.bed_id = b.bed_id "
        "WHERE af.doctor_id = %s AND af.discharge_time IS NULL "
        "ORDER BY af.admit_time",
        (doctor_id,)
    )


@router.post("/rounds", status_code=201, summary="创建每日查房记录")
def create_daily_round(data: DailyRoundCreate):
    """
    事务 8 步（对应 SQL 9.2）：

    A. 检查当日是否已有记录（R21：一日一次）
    B. FOR UPDATE 锁定档案，获取余额 + 床位费
    C. 创建当日住院记录
    D. 创建住院处方（一天一张）
    E. 逐条添加处方明细
    F. 计算当日药费（Σ qty × unit_price）
    G. 写入当日费用（床位费 + 药费）
    H. 扣减预交金（余额不足 → 回滚）
    """
    with transaction() as conn:
        # Step A：检查当日是否已有记录（R21）
        row = query_one(
            "SELECT COUNT(*) AS cnt FROM inpatient_record "
            "WHERE file_no = %s AND record_date = CURDATE()",
            (data.file_no,)
        )
        if row["cnt"] > 0:
            raise HTTPException(409, "今日已查房，不可重复")

        # Step B：锁定档案，获取余额 + 床位费
        af = query_one(
            "SELECT af.deposit_balance, w.charge_rate "
            "FROM admission_file af "
            "JOIN ward w ON af.ward_id = w.ward_id "
            "WHERE af.file_no = %s FOR UPDATE",
            (data.file_no,)
        )
        if not af:
            raise HTTPException(404, "住院档案不存在")
        if af["deposit_balance"] <= 0:
            raise HTTPException(400, "预交金已耗尽，无法继续查房")

        charge_rate = af["charge_rate"]

        # Step C：创建当日住院记录
        record_id = execute(
            "INSERT INTO inpatient_record (file_no, record_date, treatment_desc) "
            "VALUES (%s, CURDATE(), %s)",
            (data.file_no, data.treatment_desc),
            conn=conn
        )

        # Step D：创建住院处方
        presc_id = execute(
            "INSERT INTO inpatient_prescription (record_id, doctor_id) "
            "VALUES (%s, %s)",
            (record_id, data.doctor_id),
            conn=conn
        )

        # Step E：逐条添加处方明细
        total_drug_fee = 0
        for item in data.details:
            execute(
                "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
                "VALUES (%s, '住院', %s, %s, %s)",
                (presc_id, item.medicine_id, item.qty, item.usage_inst),
                conn=conn
            )
            # 查单价计算药费（避免两次 JOIN）
            med = query_one(
                "SELECT unit_price FROM medicine WHERE medicine_id = %s",
                (item.medicine_id,)
            )
            if med:
                total_drug_fee += med["unit_price"] * item.qty

        # Step F + G：计算当日费用 = 床位费 + 药费，写入 inpatient_record
        daily_fee = charge_rate + total_drug_fee
        execute(
            "UPDATE inpatient_record SET daily_fee = %s WHERE record_id = %s",
            (daily_fee, record_id),
            conn=conn
        )

        # Step H：扣减预交金（余额不足自动回滚）
        affected = execute(
            "UPDATE admission_file SET deposit_balance = deposit_balance - %s "
            "WHERE file_no = %s AND deposit_balance >= %s",
            (daily_fee, data.file_no, daily_fee),
            conn=conn
        )
        if not affected:
            raise HTTPException(400, "预交金余额不足，查房失败")

    return {
        "record_id": record_id,
        "presc_id": presc_id,
        "daily_fee": daily_fee,
        "message": "查房记录创建成功",
    }


@router.get("/rounds/{file_no}", summary="历史查房记录")
def get_round_history(file_no: int):
    """
    查看某住院档案的所有每日查房记录。
    对应 SQL 9.3
    """
    return query(
        "SELECT ir.record_id, ir.record_date, ir.treatment_desc, ir.daily_fee, "
        "       ip.presc_id, ip.presc_time "
        "FROM inpatient_record ir "
        "LEFT JOIN inpatient_prescription ip ON ir.record_id = ip.record_id "
        "WHERE ir.file_no = %s "
        "ORDER BY ir.record_date DESC, ip.presc_time",
        (file_no,)
    )
