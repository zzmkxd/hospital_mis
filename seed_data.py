"""
测试数据初始化脚本
------------------
按 FK 依赖顺序插入，覆盖全部 6 条业务流程，数据量充足。
用法：python seed_data.py
"""
import pymysql
from config import DB_CONFIG

DB_CONFIG = {k: v for k, v in DB_CONFIG.items() if k != "cursorclass"}


def main():
    conn = pymysql.connect(**DB_CONFIG)
    c = conn.cursor()

    # ============================================================
    # 1. 科室（5 个）
    # ============================================================
    depts = [
        (1, "内科", "两者兼有", "010-11111111"),
        (2, "外科", "两者兼有", "010-22222222"),
        (3, "妇产科", "两者兼有", "010-33333333"),
        (4, "儿科", "两者兼有", "010-44444444"),
        (5, "骨科", "两者兼有", "010-55555555"),
    ]
    c.executemany(
        "INSERT INTO department (dept_id, dept_name, dept_type, phone) VALUES (%s,%s,%s,%s)",
        depts,
    )
    print("  OK  科室 x5")

    # ============================================================
    # 2. 医生（8 人）+ 账号
    # ============================================================
    doctors = [
        (1, "张明", "男", "主任医师", 50.00, "13800000001", 1),
        (2, "李芳", "女", "主治医师", 30.00, "13800000002", 1),
        (3, "王强", "男", "主任医师", 50.00, "13800000003", 2),
        (4, "赵丽", "女", "主治医师", 30.00, "13800000004", 2),
        (5, "陈静", "女", "主任医师", 50.00, "13800000005", 3),
        (6, "刘波", "男", "住院医师", 15.00, "13800000006", 4),
        (7, "黄蓉", "女", "主治医师", 30.00, "13800000007", 5),
        (8, "周杰", "男", "主任医师", 50.00, "13800000008", 5),
    ]
    c.executemany(
        "INSERT INTO doctor (doctor_id, name, gender, title, consultation_fee, phone, dept_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        doctors,
    )

    doctor_accounts = [
        (1, "医生", "123456"),
        (2, "医生", "123456"),
        (3, "医生", "123456"),
        (4, "医生", "123456"),
        (5, "医生", "123456"),
        (6, "医生", "123456"),
        (7, "医生", "123456"),
        (8, "医生", "123456"),
    ]
    c.executemany(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        doctor_accounts,
    )
    print("  OK  医生 x8 + 账号 x8")

    # ============================================================
    # 3. 病房（5 个）
    # ============================================================
    wards = [
        (1, "内科301", 1, "3号楼1层", 100.00, 4, 0),
        (2, "外科201", 2, "2号楼1层", 120.00, 3, 0),
        (3, "妇产科501", 3, "5号楼1层", 150.00, 3, 0),
        (4, "儿科401", 4, "4号楼2层", 80.00, 4, 0),
        (5, "骨科601", 5, "6号楼1层", 130.00, 3, 0),
    ]
    c.executemany(
        "INSERT INTO ward (ward_id, ward_no, dept_id, location, charge_rate, total_beds, occupied_cnt) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        wards,
    )
    print("  OK  病房 x5")

    # ============================================================
    # 4. 床位（17 张）
    # ============================================================
    beds = []
    for ward_id, bed_count in [(1, 4), (2, 3), (3, 3), (4, 4), (5, 3)]:
        for i in range(1, bed_count + 1):
            beds.append((None, ward_id, f"{i:02d}", "空闲"))
    for b in beds:
        c.execute(
            "INSERT INTO bed (ward_id, bed_no, bed_status) VALUES (%s,%s,%s)",
            (b[1], b[2], b[3]),
        )
    print("  OK  床位 x17")

    # ============================================================
    # 5. 病人（8 人）+ 账号
    # ============================================================
    patients = [
        (1, "张三", "男", 35, "北京市海淀区", "13900000001"),
        (2, "李四", "女", 28, "北京市朝阳区", "13900000002"),
        (3, "王五", "男", 60, "北京市西城区", "13900000003"),
        (4, "赵六", "女", 45, "北京市东城区", "13900000004"),
        (5, "孙七", "男", 52, "北京市丰台区", "13900000005"),
        (6, "周八", "女", 7, "北京市海淀区", "13900000006"),
        (7, "吴九", "男", 72, "北京市石景山区", "13900000007"),
        (8, "郑十", "女", 31, "北京市通州区", "13900000008"),
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
        (4, "病人", "123456"),
        (5, "病人", "123456"),
        (6, "病人", "123456"),
        (7, "病人", "123456"),
        (8, "病人", "123456"),
    ]
    c.executemany(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        patient_accounts,
    )
    print("  OK  病人 x8 + 账号 x8")

    # ============================================================
    # 6. 药品（14 种 — 覆盖多科室用药）
    # ============================================================
    medicines = [
        (1, "阿莫西林胶囊", "500mg/片", "片", 0.50, 1000),
        (2, "头孢克肟片", "100mg/片", "片", 2.00, 500),
        (3, "布洛芬缓释胶囊", "200mg/粒", "粒", 0.30, 800),
        (4, "葡萄糖注射液", "500ml/瓶", "瓶", 8.00, 200),
        (5, "氯化钠注射液", "250ml/瓶", "瓶", 5.00, 300),
        (6, "维生素C片", "100mg/片", "片", 0.10, 2000),
        (7, "蒙脱石散", "3g/袋", "袋", 1.50, 400),
        (8, "奥美拉唑肠溶胶囊", "20mg/粒", "粒", 1.80, 600),
        (9, "阿托伐他汀钙片", "10mg/片", "片", 3.50, 300),
        (10, "盐酸氨溴索口服液", "100ml/瓶", "瓶", 12.00, 150),
        (11, "氯雷他定片", "10mg/片", "片", 1.20, 500),
        (12, "对乙酰氨基酚片", "500mg/片", "片", 0.20, 1200),
        (13, "硝酸甘油片", "0.5mg/片", "片", 2.50, 200),
        (14, "胰岛素注射液", "400IU/10ml", "支", 45.00, 100),
    ]
    c.executemany(
        "INSERT INTO medicine (medicine_id, med_name, specification, unit, unit_price, stock_qty) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        medicines,
    )
    print("  OK  药品 x14")

    # ============================================================
    # 7. 排班（12 条 — 覆盖 5 天，门诊+住院巡诊）
    # ============================================================
    schedules = [
        # 2026-05-29 周一
        (1, 1, "2026-05-29", "08:00", "12:00", "门诊坐诊", "内科诊室01"),
        (2, 2, "2026-05-29", "13:00", "17:00", "门诊坐诊", "内科诊室02"),
        (3, 3, "2026-05-29", "08:00", "12:00", "门诊坐诊", "外科诊室01"),
        (4, 4, "2026-05-29", "08:00", "12:00", "住院巡诊", None),
        # 2026-05-30 周二
        (5, 1, "2026-05-30", "08:00", "12:00", "门诊坐诊", "内科诊室01"),
        (6, 5, "2026-05-30", "08:00", "12:00", "门诊坐诊", "妇产科诊室01"),
        (7, 6, "2026-05-30", "08:00", "12:00", "门诊坐诊", "儿科诊室01"),
        (8, 3, "2026-05-30", "13:00", "17:00", "住院巡诊", None),
        # 2026-05-31 周三
        (9, 2, "2026-05-31", "08:00", "12:00", "门诊坐诊", "内科诊室01"),
        (10, 7, "2026-05-31", "08:00", "12:00", "门诊坐诊", "骨科诊室01"),
        (11, 4, "2026-05-31", "08:00", "12:00", "门诊坐诊", "外科诊室02"),
        # 2026-06-01 周四
        (12, 8, "2026-06-01", "08:00", "12:00", "门诊坐诊", "骨科诊室02"),
    ]
    c.executemany(
        "INSERT INTO schedule (schedule_id, doctor_id, sched_date, start_time, end_time, sched_type, clinic) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        schedules,
    )
    print("  OK  排班 x12")

    # ============================================================
    # 8. 挂号（8 条 — 覆盖多科室、初复诊、不同状态）
    # ============================================================
    registrations = [
        # 张三挂内科张明 5/29 初诊 待就诊
        (1, 1, 1, 1, "2026-05-29 08:30:00", "初诊", "待就诊"),
        # 李四挂内科张明 5/29 复诊 已就诊
        (2, 2, 1, 1, "2026-05-29 09:00:00", "复诊", "已就诊"),
        # 王五挂外科王强 5/29 初诊 待就诊
        (3, 3, 3, 3, "2026-05-29 10:00:00", "初诊", "待就诊"),
        # 赵六挂内科李芳 5/29 初诊 已就诊
        (4, 4, 2, 2, "2026-05-29 13:30:00", "初诊", "已就诊"),
        # 孙七挂妇产科陈静 5/30 初诊 待就诊
        (5, 5, 5, 6, "2026-05-30 08:20:00", "初诊", "待就诊"),
        # 周八挂儿科刘波 5/30 初诊 待就诊
        (6, 6, 6, 7, "2026-05-30 09:00:00", "初诊", "待就诊"),
        # 吴九挂骨科黄蓉 5/31 初诊 待就诊
        (7, 7, 7, 10, "2026-05-31 08:45:00", "初诊", "待就诊"),
        # 郑十挂内科李芳 5/31 初诊 已就诊
        (8, 8, 2, 9, "2026-05-31 10:15:00", "初诊", "已就诊"),
    ]
    c.executemany(
        "INSERT INTO registration (reg_id, case_no, doctor_id, schedule_id, reg_date, reg_type, reg_status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        registrations,
    )
    print("  OK  挂号 x8")

    # ============================================================
    # 9. 门诊处方 + 处方明细（4 条处方，覆盖多种药品）
    # ============================================================
    # 处方1：李四 — 头痛发热（关联挂号2）
    c.execute(
        "INSERT INTO outpatient_prescription (presc_id, reg_id, doctor_id, presc_time, symptom_desc, pay_status) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (1, 2, 1, "2026-05-29 09:15:00", "头痛、发热三天，咽喉红肿", "待支付"),
    )
    out_details_1 = [
        (1, "门诊", 1, 24, "每日三次，每次两片"),   # 阿莫西林
        (2, "门诊", 3, 10, "每日两次，每次一粒"),   # 布洛芬
        (3, "门诊", 6, 12, "每日三次，每次一片"),   # 维生素C
    ]
    for d in out_details_1:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )

    # 处方2：赵六 — 胃痛（关联挂号4）
    c.execute(
        "INSERT INTO outpatient_prescription (presc_id, reg_id, doctor_id, presc_time, symptom_desc, pay_status) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (2, 4, 2, "2026-05-29 14:00:00", "上腹隐痛一周，反酸嗳气", "已支付"),
    )
    out_details_2 = [
        (4, "门诊", 8, 14, "每日两次，每次一粒，饭前服用"),   # 奥美拉唑
        (5, "门诊", 7, 6, "每日三次，每次一袋"),             # 蒙脱石散
    ]
    for d in out_details_2:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    # 扣库存
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 14 WHERE medicine_id = 8")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 6 WHERE medicine_id = 7")

    # 处方3：郑十 — 咳嗽过敏（关联挂号8）
    c.execute(
        "INSERT INTO outpatient_prescription (presc_id, reg_id, doctor_id, presc_time, symptom_desc, pay_status) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (3, 8, 2, "2026-05-31 10:45:00", "干咳两周，夜间加重，伴皮肤瘙痒", "待支付"),
    )
    out_details_3 = [
        (6, "门诊", 10, 2, "每日三次，每次10ml"),           # 氨溴索
        (7, "门诊", 11, 6, "每日一次，每次一片"),           # 氯雷他定
        (8, "门诊", 12, 10, "必要时服用，每次一片"),        # 对乙酰氨基酚
    ]
    for d in out_details_3:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )

    # 处方4：王五 — 高血压复查（关联挂号3，直接开方模拟快速接诊）
    c.execute(
        "INSERT INTO outpatient_prescription (presc_id, reg_id, doctor_id, presc_time, symptom_desc, pay_status) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (4, 3, 3, "2026-05-29 10:20:00", "高血压复诊，血压控制尚可", "已支付"),
    )
    out_details_4 = [
        (9, "门诊", 9, 30, "每日一次，每次一片，睡前服用"),   # 阿托伐他汀
    ]
    for d in out_details_4:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 30 WHERE medicine_id = 9")

    print("  OK  门诊处方 x4 + 明细 x9")

    # ============================================================
    # 10. 入院数据（2 条）
    # ============================================================

    # 10a. 张三 → 内科301（已住院数日）
    c.execute("SELECT bed_id FROM bed WHERE ward_id = 1 AND bed_status = '空闲' ORDER BY bed_id LIMIT 1")
    bed_row = c.fetchone()
    if bed_row:
        bed_id_zhang = bed_row[0]
        c.execute(
            "INSERT INTO admission_file (file_no, case_no, doctor_id, ward_id, bed_id, admit_time, deposit_balance) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (1, 1, 1, 1, bed_id_zhang, "2026-05-28 14:00:00", 3000.00),
        )
        c.execute(
            "UPDATE patient SET is_inpatient = '是', ward_id = %s, bed_id = %s WHERE case_no = %s",
            (1, bed_id_zhang, 1),
        )
        c.execute("UPDATE bed SET bed_status = '占用' WHERE bed_id = %s", (bed_id_zhang,))
        c.execute("UPDATE ward SET occupied_cnt = occupied_cnt + 1 WHERE ward_id = 1")

    # 10b. 孙七 → 外科201
    c.execute("SELECT bed_id FROM bed WHERE ward_id = 2 AND bed_status = '空闲' ORDER BY bed_id LIMIT 1")
    bed_row2 = c.fetchone()
    if bed_row2:
        bed_id_sun = bed_row2[0]
        c.execute(
            "INSERT INTO admission_file (file_no, case_no, doctor_id, ward_id, bed_id, admit_time, deposit_balance) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (2, 5, 3, 2, bed_id_sun, "2026-05-30 16:00:00", 5000.00),
        )
        c.execute(
            "UPDATE patient SET is_inpatient = '是', ward_id = %s, bed_id = %s WHERE case_no = %s",
            (2, bed_id_sun, 5),
        )
        c.execute("UPDATE bed SET bed_status = '占用' WHERE bed_id = %s", (bed_id_sun,))
        c.execute("UPDATE ward SET occupied_cnt = occupied_cnt + 1 WHERE ward_id = 2")

    print("  OK  入院档案 x2（张三→内科301, 孙七→外科201）")

    # ============================================================
    # 11. 住院记录（每日查房）+ 住院处方 + 明细
    #     张三已住院 3 天：5/29、5/30、5/31 各一次查房
    #     孙七已住院 1 天：5/31 一次查房
    # ============================================================

    # --- 张三 5/29 查房 ---
    c.execute(
        "INSERT INTO inpatient_record (record_id, file_no, record_date, treatment_desc, daily_fee) "
        "VALUES (%s,%s,%s,%s,%s)",
        (1, 1, "2026-05-29", "入院次日查房：体温正常，血压偏高。继续抗感染治疗，加用降压药物。", 163.50),
    )
    c.execute(
        "INSERT INTO inpatient_prescription (presc_id, record_id, doctor_id, presc_time) "
        "VALUES (%s,%s,%s,%s)",
        (1, 1, 1, "2026-05-29 09:30:00"),
    )
    ip_details_1 = [
        (10, "住院", 2, 6, "每日两次，每次一片"),    # 头孢克肟
        (11, "住院", 4, 1, "每日一次，静脉滴注"),    # 葡萄糖注射液
        (12, "住院", 9, 2, "每日一次，每次一片"),    # 阿托伐他汀
    ]
    for d in ip_details_1:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 6 WHERE medicine_id = 2")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 1 WHERE medicine_id = 4")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 2 WHERE medicine_id = 9")

    # --- 张三 5/30 查房 ---
    c.execute(
        "INSERT INTO inpatient_record (record_id, file_no, record_date, treatment_desc, daily_fee) "
        "VALUES (%s,%s,%s,%s,%s)",
        (2, 1, "2026-05-30", "血压有所下降，感染症状缓解。继续当前方案，加维生素C辅助。", 112.10),
    )
    c.execute(
        "INSERT INTO inpatient_prescription (presc_id, record_id, doctor_id, presc_time) "
        "VALUES (%s,%s,%s,%s)",
        (2, 2, 1, "2026-05-30 08:45:00"),
    )
    ip_details_2 = [
        (13, "住院", 2, 3, "每日两次，每次一片"),
        (14, "住院", 6, 10, "每日三次，每次一片"),
    ]
    for d in ip_details_2:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 3 WHERE medicine_id = 2")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 10 WHERE medicine_id = 6")

    # --- 张三 5/31 查房 ---
    c.execute(
        "INSERT INTO inpatient_record (record_id, file_no, record_date, treatment_desc, daily_fee) "
        "VALUES (%s,%s,%s,%s,%s)",
        (3, 1, "2026-05-31", "病情明显好转，血压已稳定。停用静脉滴注，改为口服药维持。", 106.00),
    )
    c.execute(
        "INSERT INTO inpatient_prescription (presc_id, record_id, doctor_id, presc_time) "
        "VALUES (%s,%s,%s,%s)",
        (3, 3, 1, "2026-05-31 09:00:00"),
    )
    ip_details_3 = [
        (15, "住院", 1, 6, "每日三次，每次两片"),    # 阿莫西林
        (16, "住院", 6, 10, "每日三次，每次一片"),
    ]
    for d in ip_details_3:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 6 WHERE medicine_id = 1")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 10 WHERE medicine_id = 6")

    # --- 孙七 5/31 查房（入院次日） ---
    c.execute(
        "INSERT INTO inpatient_record (record_id, file_no, record_date, treatment_desc, daily_fee) "
        "VALUES (%s,%s,%s,%s,%s)",
        (4, 2, "2026-05-31", "入院后首次查房：术后观察，生命体征平稳。给予抗生素预防感染，止痛药缓解疼痛。", 132.60),
    )
    c.execute(
        "INSERT INTO inpatient_prescription (presc_id, record_id, doctor_id, presc_time) "
        "VALUES (%s,%s,%s,%s)",
        (4, 4, 3, "2026-05-31 08:30:00"),
    )
    ip_details_4 = [
        (17, "住院", 2, 4, "每日两次，每次一片"),    # 头孢克肟
        (18, "住院", 3, 6, "每日两次，每次一粒"),    # 布洛芬
        (19, "住院", 5, 2, "每日一次，静脉滴注"),    # 氯化钠注射液
    ]
    for d in ip_details_4:
        c.execute(
            "INSERT INTO prescription_detail (presc_id, presc_type, medicine_id, qty, usage_inst) "
            "VALUES (%s,%s,%s,%s,%s)",
            d,
        )
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 4 WHERE medicine_id = 2")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 6 WHERE medicine_id = 3")
    c.execute("UPDATE medicine SET stock_qty = stock_qty - 2 WHERE medicine_id = 5")

    # 从预交金中扣减每日费用
    c.execute("UPDATE admission_file SET deposit_balance = deposit_balance - 163.50 WHERE file_no = 1")
    c.execute("UPDATE admission_file SET deposit_balance = deposit_balance - 112.10 WHERE file_no = 1")
    c.execute("UPDATE admission_file SET deposit_balance = deposit_balance - 106.00 WHERE file_no = 1")
    c.execute("UPDATE admission_file SET deposit_balance = deposit_balance - 132.60 WHERE file_no = 2")

    print("  OK  住院记录 x4 + 住院处方 x4 + 明细 x10")

    # ============================================================
    # 12. 管理员账号
    # ============================================================
    c.execute(
        "INSERT INTO account (ref_id, role, password_hash) VALUES (%s,%s,%s)",
        (999, "管理员", "admin123"),
    )
    print("  OK  管理员账号 x1")

    conn.commit()
    conn.close()
    print("\n=== 测试数据初始化完成 ===")
    print("""
数据概览：
  科室 x5    医生 x8    药品 x14    排班 x12
  病人 x8    床位 x17   病房 x5     挂号 x8
  门诊处方 x4  门诊明细 x9
  入院档案 x2  住院记录 x4  住院处方 x4  住院明细 x10

覆盖流程：
  1. 门诊挂号 → 2. 接诊开方 → 3. 缴费 → 4. 入院 → 5. 每日查房 → 6. 出院结算
""")


if __name__ == "__main__":
    main()
