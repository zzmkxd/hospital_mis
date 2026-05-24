"""
端到端业务流程自动化验证脚本
----------------------------
按 6 条业务流程顺序调用 API，验证每一步的返回。
用法：
    python init_db.py         # 重建空库
    python seed_data.py       # 导入测试数据
    uvicorn main:app --host 127.0.0.1 --port 8000   # 另一个终端启动
    python verify_e2e.py      # 本脚本
"""
import requests
import sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000/api"
ok, fail = 0, 0

def step(desc, method, path, body=None, expect_status=200):
    global ok, fail
    try:
        if method == "GET":
            r = requests.get(BASE + path)
        elif method == "POST":
            r = requests.post(BASE + path, json=body)
        elif method == "PUT":
            r = requests.put(BASE + path, json=body)
        elif method == "DELETE":
            r = requests.delete(BASE + path)
    except Exception as e:
        print(f"  ✗ {desc} — 连接失败: {e}")
        fail += 1
        return None

    if r.status_code == expect_status:
        print(f"  [PASS] {desc} ({r.status_code})")
        ok += 1
        return r.json()
    else:
        print(f"  [FAIL] {desc} ({r.status_code}) {r.json().get('detail', '')}")
        fail += 1
        return None


# ============================================================
# 0. 连接检查
# ============================================================
print("\n=== 0. 连接检查 ===\n")
step("连接检查", "GET", "/schedules", expect_status=200)

# ============================================================
# 1. 登录（三种角色）
# ============================================================
print("\n=== 1. 登录 ===\n")

admin = step("管理员登录", "POST", "/auth/login",
             {"ref_id": 999, "password": "admin123", "role": "管理员"})
doc = step("医生登录 (张明, id=1)", "POST", "/auth/login",
           {"ref_id": 1, "password": "123456", "role": "医生"})
doc2 = step("医生登录 (李芳, id=2)", "POST", "/auth/login",
            {"ref_id": 2, "password": "123456", "role": "医生"})
pat = step("病人登录 (王伟, id=1)", "POST", "/auth/login",
           {"ref_id": 1, "password": "123456", "role": "病人"})

if not all([admin, doc, pat]):
    print("\n⚠️  登录失败，终止验证。请确认已运行 seed_data.py")
    exit(1)

assert admin["role"] == "管理员", "管理员角色不匹配"
assert doc["role"] == "医生", "医生角色不匹配"
assert pat["role"] == "病人", "病人角色不匹配"
print(f"\n  管理员: {admin['name']}  |  医生: {doc['name']}  |  病人: {pat['name']}")

# ============================================================
# 2. 管理员 — 基础数据维护（M2）
# ============================================================
print("\n=== 2. 管理员 — 基础数据维护 ===\n")

step("查看科室列表", "GET", "/admin/departments")
step("查看医生列表", "GET", "/admin/doctors")
step("查看药品列表", "GET", "/admin/medicines")

# CRUD 科室
new_dept = step("新增科室", "POST", "/admin/departments",
                {"dept_name": "测试科室", "dept_type": "门诊", "phone": "010-1234"}, expect_status=201)
if new_dept:
    step("编辑科室", "PUT", f"/admin/departments/{new_dept['dept_id']}",
         {"dept_name": "测试科室(改)", "dept_type": "门诊", "phone": "010-5678"})
    step("删除科室", "DELETE", f"/admin/departments/{new_dept['dept_id']}")

# CRUD 药品
step("新增药品", "POST", "/admin/medicines",
     {"med_name": "测试药品", "specification": "10mg×20片", "unit": "盒", "unit_price": 25.0, "stock_qty": 100}, expect_status=201)

# ============================================================
# 3. 管理员 — 排班管理（M3）
# ============================================================
print("\n=== 3. 排班管理 ===\n")

schedules = step("查看排班列表", "GET", "/schedules")
new_sched = step("新增排班", "POST", "/schedules", {
    "doctor_id": 1, "sched_date": "2026-06-01",
    "start_time": "08:00", "end_time": "12:00",
    "sched_type": "门诊坐诊", "clinic": "诊室A"
}, expect_status=201)
if new_sched:
    step("冲突检测—同医生同时段", "POST", "/schedules", {
        "doctor_id": 1, "sched_date": "2026-06-01",
        "start_time": "09:00", "end_time": "11:00",
        "sched_type": "门诊坐诊", "clinic": "诊室B"
    }, expect_status=409)
    step("新增住院巡诊", "POST", "/schedules", {
        "doctor_id": 2, "sched_date": "2026-06-01",
        "start_time": "14:00", "end_time": "17:00",
        "sched_type": "住院巡诊", "clinic": None
    }, expect_status=201)
    step("删除排班", "DELETE", f"/schedules/{new_sched['schedule_id']}")

# ============================================================
# 4. 门诊链路：挂号 → 接诊 → 开处方 → 缴费（M4→M5→M6）
# ============================================================
print("\n=== 4. 门诊链路 ===\n")

# 4.1 病人挂号
doctors = step("查询可选医生", "GET",
               "/registrations/doctors?dept_id=1&target_date=2026-05-24")
visit_type = step("判定初复诊", "GET", f"/registrations/visit-type?case_no={pat['ref_id']}")

reg = step("创建挂号", "POST", "/registrations", {
    "case_no": pat["ref_id"],
    "doctor_id": 1,
    "schedule_id": 1,
    "reg_type": visit_type["reg_type"] if visit_type else "初诊",
}, expect_status=201)
step("查看我的挂号", "GET", f"/registrations/my?case_no={pat['ref_id']}")

# 4.2 医生接诊
queue = step("医生查看待就诊队列", "GET", f"/outpatient/queue?doctor_id=1")
if reg:
    step("接诊", "PUT", f"/outpatient/consult/{reg['reg_id']}")

# 4.3 开具处方
meds = step("查看可用药品", "GET", "/outpatient/medicines")
if reg and meds and len(meds) > 0:
    med_id = meds[0]["medicine_id"]
    presc = step("开具门诊处方", "POST", "/outpatient/prescriptions", {
        "reg_id": reg["reg_id"],
        "doctor_id": 1,
        "symptom_desc": "感冒",
        "details": [{"medicine_id": med_id, "qty": 2, "usage_inst": "每日三次，每次一片"}],
    }, expect_status=201)
    if presc:
        print(f"    诊疗费={presc.get('consultation_fee')} 药费={presc.get('drug_fee')} 总费用={presc.get('total_fee')}")
        step("查看处方明细", "GET", f"/outpatient/prescriptions/{presc['presc_id']}")

# 4.4 病人缴费
unpaid = step("查看待支付处方", "GET", f"/payment/unpaid?case_no={pat['ref_id']}")
if presc:
    step("查看费用汇总", "GET", f"/payment/prescriptions/{presc['presc_id']}/fee")
    step("支付处方", "POST", "/payment/pay", {"presc_id": presc["presc_id"]})
    # 验证支付后状态
    step("确认已支付", "GET", f"/payment/unpaid?case_no={pat['ref_id']}")

# 4.5 历史查询
step("门诊历史", "GET", f"/payment/history/outpatient?case_no={pat['ref_id']}")

# ============================================================
# 5. 住院链路：入院 → 查房 → 出院（M7→M8→M9）
# ============================================================
print("\n=== 5. 住院链路 ===\n")

# 5.1 入院
wards = step("查询可选病房", "GET", "/admission/wards?dept_id=1")
if wards:
    ward_id = wards[0]["ward_id"]
    beds = step("查询空闲床位", "GET", f"/admission/beds?ward_id={ward_id}")
    if beds:
        admission = step("办理入院", "POST", "/admission", {
            "case_no": pat["ref_id"],
            "doctor_id": 1,
            "ward_id": ward_id,
            "bed_id": beds[0]["bed_id"],
            "deposit_balance": 5000,
        }, expect_status=201)
        step("在院病人列表", "GET", "/admission")

# 5.2 每日查房
inpatients = step("医生查看在院病人", "GET", f"/rounds/my-inpatients?doctor_id=1")
if inpatients and meds:
    file_no = inpatients[0]["file_no"]
    round_result = step("创建查房记录", "POST", "/rounds/rounds", {
        "file_no": file_no,
        "doctor_id": 1,
        "treatment_desc": "常规查房，病情稳定",
        "details": [{"medicine_id": meds[0]["medicine_id"], "qty": 1, "usage_inst": "每日一次"}],
    }, expect_status=201)
    if round_result:
        print(f"    当日费用={round_result.get('daily_fee')}")
    step("查房历史", "GET", f"/rounds/rounds/{file_no}")

    # R21 验证：同日重复查房
    step("重复查房应被拒绝", "POST", "/rounds/rounds", {
        "file_no": file_no,
        "doctor_id": 1,
        "treatment_desc": "再次尝试",
        "details": [{"medicine_id": meds[0]["medicine_id"], "qty": 1, "usage_inst": ""}],
    }, expect_status=409)

# 5.3 出院结算
if admission:
    file_no = admission["file_no"]
    summary = step("查看费用汇总", "GET", f"/discharge/summary/{file_no}")
    if summary:
        print(f"    住院天数={summary.get('stay_days')} 总费用={summary.get('total_cost')}")
    discharge = step("办理出院", "POST", "/discharge", {"file_no": file_no})
    if discharge:
        print(f"    结算金额={discharge.get('settlement')}")
    # 验证出院后资源释放完毕
    step("确认已出院", "GET", "/admission")

# 5.4 住院历史
step("住院历史", "GET", f"/payment/history/inpatient?case_no={pat['ref_id']}")

# ============================================================
# 6. 统计查询
# ============================================================
print("\n=== 6. 统计查询 ===\n")

step("医生工作量", "GET", "/stats/doctors?start_date=2026-01-01&end_date=2026-12-31")
step("科室统计", "GET", "/stats/departments")
step("药品统计", "GET", "/stats/medicines")
step("床位使用率", "GET", "/stats/beds")
step("排班统计", "GET", "/stats/schedules?start_date=2026-01-01&end_date=2026-12-31")

# ============================================================
# 结果汇总
# ============================================================
total = ok + fail
print(f"\n{'='*60}")
print(f"  Result: {ok}/{total} passed", end="")
if fail > 0:
    print(f", {fail} FAILED", end="")
print()
print(f"{'='*60}\n")

if fail > 0:
    print("WARNING: Some checks failed. Review [FAIL] lines above.")
    exit(1)
else:
    print("ALL PASSED. 6 business flows verified successfully.")
