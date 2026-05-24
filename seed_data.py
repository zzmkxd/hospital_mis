"""
测试数据初始化脚本
------------------
按 FK 依赖顺序插入，覆盖全部 6 条业务流程。
用法：python seed_data.py
"""
import pymysql
from config import DB_CONFIG

DB_CONFIG = {k: v for k, v in DB_CONFIG.items() if k != "cursorclass"}


def main():
    conn = pymysql.connect(**DB_CONFIG)
    c = conn.cursor()

    # ============================================================
    # 1. 科室（3 个）
    # ============================================================
    depts = [
        (1, "内科", "两者兼有", "010-11111111"),
        (2, "外科", "两者兼有", "010-22222222"),
        (3, "妇产科", "两者兼有", "010-33333333"),
    ]
    c.executemany(
        "INSERT INTO department (dept_id, dept_name, dept_type, phone) VALUES (%s,%s,%s,%s)",
        depts,
    )
    print("  OK  科室 x3")

    # ============================================================
    # 2. 医生（5 人）+ 账号
    # ============================================================
    doctors = [
        (1, "张明", "男", "主任医师", 50.00, "13800000001", 1),
        (2, "李芳", "女", "主治医师", 30.00, "13800000002", 1),
        (3, "王强", "男", "主任医师", 50.00, "13800000003", 2),
        (4, "赵丽", "女", "主治医师", 30.00, "13800000004", 2),
        (5, "陈静", "女", "主任医师", 50.00, "13800000005", 3),
    ]
    c.executemany(
        "INSERT INTO doctor (doctor_id, name, gender, title, consultation_fee, phone, dept_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        doctors,
    )

    # 医生账号
    doctor_accounts = [
        (1, "医生", "123456"),
        (2, "医生", "123456"),
        (3, "医生", "123456"),
        (4, "医生", "123456"),
        (5, "医生", "123456"),
    ]
    c.executemany(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        doctor_accounts,
    )
    print("  OK  医生 x5 + 账号 x5")

    # ============================================================
    # 3. 病房（3 个）
    # ============================================================
    wards = [
        (1, "内科301", 1, "3号楼1层", 100.00, 4, 0),
        (2, "外科201", 2, "2号楼1层", 120.00, 3, 0),
        (3, "妇产科501", 3, "5号楼1层", 150.00, 3, 0),
    ]
    c.executemany(
        "INSERT INTO ward (ward_id, ward_no, dept_id, location, charge_rate, total_beds, occupied_cnt) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        wards,
    )
    print("  OK  病房 x3")

    # ============================================================
    # 4. 床位（10 张）
    # ============================================================
    beds = []
    for ward_id, bed_count in [(1, 4), (2, 3), (3, 3)]:
        for i in range(1, bed_count + 1):
            beds.append((None, ward_id, f"{i:02d}", "空闲"))
    for b in beds:
        c.execute(
            "INSERT INTO bed (ward_id, bed_no, bed_status) VALUES (%s,%s,%s)",
            (b[1], b[2], b[3]),
        )
    print("  OK  床位 x10")

    # ============================================================
    # 5. 病人（3 人）+ 账号
    # ============================================================
    patients = [
        (1, "张三", "男", 35, "北京市海淀区", "13900000001"),
        (2, "李四", "女", 28, "北京市朝阳区", "13900000002"),
        (3, "王五", "男", 60, "北京市西城区", "13900000003"),
    ]
    c.executemany(
        "INSERT INTO patient (case_no, name, gender, age, address, phone) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        patients,
    )

    patient_accounts = [
        (1, "病人", "123456"),
        (2, "病人", "123456"),
        (3, "病人", "123456"),
    ]
    c.executemany(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        patient_accounts,
    )
    print("  OK  病人 x3 + 账号 x3")

    # ============================================================
    # 6. 药品（5 种）
    # ============================================================
    medicines = [
        (1, "阿莫西林胶囊", "500mg/片", "片", 0.50, 1000),
        (2, "头孢克肟片", "100mg/片", "片", 2.00, 500),
        (3, "布洛芬缓释胶囊", "200mg/粒", "粒", 0.30, 800),
        (4, "葡萄糖注射液", "500ml/瓶", "瓶", 8.00, 200),
        (5, "氯化钠注射液", "250ml/瓶", "瓶", 5.00, 300),
    ]
    c.executemany(
        "INSERT INTO medicine (medicine_id, med_name, specification, unit, unit_price, stock_qty) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        medicines,
    )
    print("  OK  药品 x5")

    # ============================================================
    # 7. 排班（5 条 — 今天 + 明天，门诊和住院巡诊都有）
    # ============================================================
    schedules = [
        # 内科张明 今天门诊坐诊
        (1, 1, "2026-05-25", "08:00", "12:00", "门诊坐诊", "内科诊室01"),
        # 内科李芳 今天门诊坐诊
        (2, 2, "2026-05-25", "13:00", "17:00", "门诊坐诊", "内科诊室02"),
        # 外科王强 今天门诊坐诊
        (3, 3, "2026-05-25", "08:00", "12:00", "门诊坐诊", "外科诊室01"),
        # 外科赵丽 今天住院巡诊
        (4, 4, "2026-05-25", "08:00", "12:00", "住院巡诊", None),
        # 内科张明 明天门诊坐诊
        (5, 1, "2026-05-26", "08:00", "12:00", "门诊坐诊", "内科诊室01"),
    ]
    c.executemany(
        "INSERT INTO schedule (schedule_id, doctor_id, sched_date, start_time, end_time, sched_type, clinic) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        schedules,
    )
    print("  OK  排班 x5")

    # ============================================================
    # 8. 挂号（3 条 — 覆盖待就诊 + 已就诊状态）
    # ============================================================
    registrations = [
        # 张三挂内科张明 今天 初诊 待就诊
        (1, 1, 1, 1, "2026-05-25 08:30:00", "初诊", "待就诊"),
        # 李四挂内科张明 今天 复诊 已就诊（模拟历史）
        (2, 2, 1, 1, "2026-05-25 09:00:00", "复诊", "已就诊"),
        # 王五挂外科王强 今天 初诊 待就诊
        (3, 3, 3, 3, "2026-05-25 10:00:00", "初诊", "待就诊"),
    ]
    c.executemany(
        "INSERT INTO registration (reg_id, case_no, doctor_id, schedule_id, reg_date, reg_type, reg_status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        registrations,
    )
    print("  OK  挂号 x3")

    # ============================================================
    # 9. 门诊处方 + 处方明细（1 条，关联李四的已就诊挂号）
    # ============================================================
    c.execute(
        "INSERT INTO outpatient_prescription (presc_id, reg_id, doctor_id, presc_time, symptom_desc, pay_status) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (1, 2, 1, "2026-05-25 09:15:00", "头痛、发热三天", "待支付"),
    )

    out_details = [
        (1, "门诊", 1, 24, "每日三次，每次两片"),   # 阿莫西林
        (2, "门诊", 3, 10, "每日两次，每次一粒"),   # 布洛芬
    ]
    for d in out_details:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    print("  OK  门诊处方 x1 + 明细 x2")

    # ============================================================
    # 10. 入院数据（1 条 — 张三被收入内科病房）
    # ============================================================
    # 先查出内科病房的第一个空闲床位
    c.execute("SELECT bed_id FROM bed WHERE ward_id = 1 AND bed_status = '空闲' ORDER BY bed_id LIMIT 1")
    bed_row = c.fetchone()
    if bed_row:
        bed_id = bed_row[0]

        c.execute(
            "INSERT INTO admission_file (file_no, case_no, doctor_id, ward_id, bed_id, admit_time, deposit_balance) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (1, 1, 1, 1, bed_id, "2026-05-24 14:00:00", 3000.00),
        )

        # 更新病人状态
        c.execute(
            "UPDATE patient SET is_inpatient = '是', ward_id = %s, bed_id = %s WHERE case_no = %s",
            (1, bed_id, 1),
        )

        # 更新床位状态
        c.execute("UPDATE bed SET bed_status = '占用' WHERE bed_id = %s", (bed_id,))

        # 更新病房人数
        c.execute("UPDATE ward SET occupied_cnt = occupied_cnt + 1 WHERE ward_id = 1")

        print("  OK  入院档案 x1（张三 → 内科301）")

    # ============================================================
    # 11. 管理员账号
    # ============================================================
    c.execute(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        (999, "管理员", "admin123"),
    )
    print("  OK  管理员账号 x1")

    conn.commit()
    conn.close()
    print("\n=== 测试数据初始化完成 ===")


if __name__ == "__main__":
    main()
