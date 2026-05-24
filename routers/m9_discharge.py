"""
M9 出院结算路由
--------------
对应 SQL 文件：sql/m9_discharge.sql

出院流程：
  锁定档案 → 校验出院时间 → 汇总总费用 → 计算结算金额
  → 填写出院时间 → 释放病人/床位/病房资源

结算金额 = deposit_balance - total_cost（正退负补）
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from db import query, query_one, execute, transaction
from schemas.m9_discharge import DischargeRequest
from schemas.common import MessageResponse

router = APIRouter()


@router.post("", summary="办理出院")
def discharge(data: DischargeRequest):
    """
    事务 7 步（对应 SQL 10.1）：

    A. FOR UPDATE 锁定档案
    B. 校验已出院（discharge_time NOT NULL → 拒绝重复）
    C. 校验出院时间晚于入院时间（R25）
    D. 汇总住院总费用（R26）
    E. 计算结算金额（R27）：deposit_balance - total_cost
    F. 填写出院时间
    G. 释放资源（R28）：病人状态、床位、病房
    """
    with transaction() as conn:
        # Step A：锁定档案
        af = query_one(
            "SELECT file_no, case_no, ward_id, bed_id, admit_time, deposit_balance "
            "FROM admission_file WHERE file_no = %s FOR UPDATE",
            (data.file_no,),
        )
        if not af:
            raise HTTPException(404, "住院档案不存在")

        # Step B：校验是否已出院
        # 如果 discharge_time 已被设置（通过另一个查询），我们直接拒绝
        # 这里用第二次查询确认（因为 FOR UPDATE 已锁定，并发安全）
        check = query_one(
            "SELECT discharge_time FROM admission_file WHERE file_no = %s",
            (data.file_no,)
        )
        if check and check["discharge_time"] is not None:
            raise HTTPException(409, "该病人已出院，不可重复操作")

        # Step C：校验出院时间晚于入院时间（R25）
        if datetime.now() <= af["admit_time"]:
            raise HTTPException(400, "出院时间必须晚于入院时间")

        # Step D：汇总住院总费用（R26）
        cost = query_one(
            "SELECT COALESCE(SUM(daily_fee), 0) AS total_cost "
            "FROM inpatient_record WHERE file_no = %s",
            (data.file_no,)
        )
        total_cost = float(cost["total_cost"])

        # Step E：计算结算金额（R27）
        deposit = float(af["deposit_balance"])
        settlement = deposit - total_cost  # 正退负补

        # Step F：填写出院时间
        execute(
            "UPDATE admission_file SET discharge_time = NOW() WHERE file_no = %s",
            (data.file_no,),
            conn=conn
        )

        # Step G：释放资源（R28）
        execute(
            "UPDATE patient SET is_inpatient = '否', ward_id = NULL, bed_id = NULL "
            "WHERE case_no = %s",
            (af["case_no"],),
            conn=conn
        )
        execute(
            "UPDATE bed SET bed_status = '空闲' WHERE bed_id = %s",
            (af["bed_id"],),
            conn=conn
        )
        execute(
            "UPDATE ward SET occupied_cnt = occupied_cnt - 1 WHERE ward_id = %s",
            (af["ward_id"],),
            conn=conn
        )

    return {
        "file_no": data.file_no,
        "total_cost": total_cost,
        "deposit_balance": deposit,
        "settlement": settlement,
        "message": "出院结算完成" if settlement >= 0 else f"出院结算完成，需补缴 {abs(settlement):.2f} 元",
    }


@router.get("/summary/{file_no}", summary="出院费用汇总")
def discharge_summary(file_no: int):
    """
    出院后：查询某次住院的完整费用汇总。
    包含住院天数、总费用、最终余额。
    对应 SQL 10.2
    """
    row = query_one(
        "SELECT af.file_no, af.admit_time, af.discharge_time, "
        "       af.deposit_balance AS final_balance, "
        "       DATEDIFF(af.discharge_time, af.admit_time) AS stay_days, "
        "       COALESCE(SUM(ir.daily_fee), 0) AS total_cost "
        "FROM admission_file af "
        "LEFT JOIN inpatient_record ir ON af.file_no = ir.file_no "
        "WHERE af.file_no = %s "
        "GROUP BY af.file_no, af.admit_time, af.discharge_time, af.deposit_balance",
        (file_no,)
    )
    if not row:
        raise HTTPException(404, "住院档案不存在")
    return row
