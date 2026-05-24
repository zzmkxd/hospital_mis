/**
 * 病人模块 — 3 个页面
 *
 *   /patient           首页
 *   /patient/register  挂号
 *   /patient/payment   缴费 & 历史
 */

function renderPatientShell(contentHtml, activeNav) {
    const user = getUser();
    const navItems = [
        { hash: "/patient",          icon: "🏠", label: "首页" },
        { hash: "/patient/register", icon: "📝", label: "挂号" },
        { hash: "/patient/payment",  icon: "💰", label: "缴费 & 历史" },
    ];

    const navLinks = navItems.map(m =>
        `<li class="nav-item">
          <a class="nav-link ${activeNav === m.hash ? "active" : ""}" href="#${m.hash}">${m.icon} ${m.label}</a>
        </li>`
    ).join("");

    $("appMain").innerHTML = `
      ${renderNavbar(user)}
      <ul class="nav nav-tabs px-3 pt-2 bg-white border-bottom">${navLinks}</ul>
      <div class="container-fluid py-3" id="patientContent">${contentHtml}</div>`;
}

// ============================================================
// 首页
// ============================================================

async function renderPatientDashboard() {
    const user = getUser();
    renderPatientShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/patient");

    try {
        const [unpaid, myRegs] = await Promise.all([
            api.get(`/payment/unpaid?case_no=${user.ref_id}`),
            api.get(`/registrations/my?case_no=${user.ref_id}`),
        ]);

        $("patientContent").innerHTML = `
          <h4 class="mb-3">🏠 ${escapeHtml(user.name)}，欢迎您</h4>
          <div class="row g-3 mb-4">
            <div class="col-md-4"><div class="stat-card">
              <div class="stat-number">${unpaid.length}</div>
              <div class="stat-label">待支付处方</div>
              ${unpaid.length > 0 ? `<a href="#/patient/payment" class="btn btn-sm btn-primary mt-2">去缴费</a>` : ""}
            </div></div>
            <div class="col-md-4"><div class="stat-card">
              <div class="stat-number">${myRegs.length}</div>
              <div class="stat-label">挂号记录</div>
            </div></div>
            <div class="col-md-4"><div class="stat-card">
              <a href="#/patient/register" class="btn btn-lg btn-primary">📝 我要挂号</a>
            </div></div>
          </div>`;

        if (myRegs.length) {
            const cols = [
                { key: "reg_id", label: "ID" },
                { key: "doctor_name", label: "医生" },
                { key: "dept_name", label: "科室" },
                { key: "reg_date", label: "挂号时间" },
                { key: "reg_status", label: "状态" },
            ];
            $("patientContent").insertAdjacentHTML("beforeend",
                `<div class="page-card"><h5>最近挂号</h5><div id="myRegsTable"></div></div>`);
            mountTable("myRegsTable", cols, myRegs.slice(0, 10));
        }
    } catch (err) {
        $("patientContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

// ============================================================
// 挂号 — 3 步
// ============================================================

async function renderPatientRegister() {
    const user = getUser();
    renderPatientShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/patient/register");

    try {
        const departments = await api.get("/admin/departments");
        let step = 1, selectedDept = null, selectedDoctor = null;

        function renderStep() {
            const stepBar = [
                { num: 1, label: "选择科室" }, { num: 2, label: "选择医生/时段" }, { num: 3, label: "确认挂号" },
            ].map(s => {
                let cls = "step";
                if (s.num < step) cls = "step done";
                if (s.num === step) cls = "step active";
                return `<div class="${cls}">${s.label}</div>`;
            }).join("");

            let body = "";
            if (step === 1) {
                body = `<h5>请选择就诊科室</h5>
                  <div class="row g-2">${departments.map(d => `
                    <div class="col-md-4"><div class="role-card" data-dept-id="${d.dept_id}" data-dept-name="${escapeHtml(d.dept_name)}">
                      <span class="role-icon">🏢</span><strong>${escapeHtml(d.dept_name)}</strong></div></div>
                  `).join("")}</div>`;
            } else if (step === 2) {
                body = `<h5>${escapeHtml(selectedDept.dept_name)} — 今日出诊医生</h5>
                  <div id="doctorList"><p class="text-muted">加载中...</p></div>`;
            } else {
                body = `
                  <div class="row"><div class="col-md-6"><table class="table">
                    <tr><td>科室</td><td><strong>${escapeHtml(selectedDept.dept_name)}</strong></td></tr>
                    <tr><td>医生</td><td><strong>${escapeHtml(selectedDoctor.name)}</strong>（${escapeHtml(selectedDoctor.title)}）</td></tr>
                    <tr><td>时段</td><td><strong>${selectedDoctor.start_time} - ${selectedDoctor.end_time}</strong></td></tr>
                    <tr><td>日期</td><td><strong>${selectedDoctor.sched_date}</strong></td></tr>
                    <tr><td>就诊类型</td><td><strong id="visitTypeLabel">判定中...</strong></td></tr>
                  </table></div></div>`;
            }

            $("patientContent").innerHTML = `
              <h4>📝 挂号</h4>
              <div class="step-indicator">${stepBar}</div>
              <div class="page-card">${body}</div>
              <div class="d-flex justify-content-between">
                <button class="btn btn-secondary" id="backBtn" ${step === 1 ? "disabled" : ""}>上一步</button>
                <button class="btn btn-primary" id="nextBtn">${step === 3 ? "确认挂号" : "下一步"}</button>
              </div>`;

            if (step === 1) {
                document.querySelectorAll(".role-card").forEach(card => {
                    card.addEventListener("click", () => {
                        document.querySelectorAll(".role-card").forEach(c => c.classList.remove("selected"));
                        card.classList.add("selected");
                        selectedDept = { dept_id: parseInt(card.dataset.deptId), dept_name: card.dataset.deptName };
                    });
                });
            }

            if (step === 2) {
                const today = new Date().toISOString().slice(0, 10);
                (async () => {
                    try {
                        const doctors = await api.get(`/registrations/doctors?dept_id=${selectedDept.dept_id}&target_date=${today}`);
                        if (doctors.length === 0) {
                            $("doctorList").innerHTML = `<div class="alert alert-warning">该科室今日暂无门诊医生，请选择其他科室</div>`;
                        } else {
                            $("doctorList").innerHTML = `
                              <table class="table"><thead><tr><th>医生</th><th>职称</th><th>诊疗费</th><th>时段</th><th>诊室</th><th></th></tr></thead>
                              <tbody>${doctors.map(d => `
                                <tr><td>${escapeHtml(d.name)}</td><td>${escapeHtml(d.title)}</td><td>¥${d.consultation_fee}</td>
                                  <td>${d.start_time} - ${d.end_time}</td><td>${escapeHtml(d.clinic || "")}</td>
                                  <td><button class="btn btn-outline-primary btn-sm select-doctor"
                                    data-sched='${escapeHtml(JSON.stringify(d))}'>选择</button></td></tr>
                              `).join("")}</tbody></table>`;
                            document.querySelectorAll(".select-doctor").forEach(btn => {
                                btn.addEventListener("click", () => { selectedDoctor = JSON.parse(btn.dataset.sched); });
                            });
                        }
                    } catch (err) { $("doctorList").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`; }
                })();
            }

            if (step === 3) {
                (async () => {
                    try {
                        const vt = await api.get(`/registrations/visit-type?case_no=${user.ref_id}`);
                        $("visitTypeLabel").textContent = vt.reg_type;
                        $("visitTypeLabel").className = vt.reg_type === "初诊" ? "text-success" : "text-primary";
                    } catch (err) { $("visitTypeLabel").textContent = "判定失败"; }
                })();
            }

            $("backBtn").addEventListener("click", () => { step--; renderStep(); });
            $("nextBtn").addEventListener("click", async () => {
                if (step === 1) {
                    if (!selectedDept) { showToast("请选择科室", "warning"); return; }
                    step++;
                } else if (step === 2) {
                    if (!selectedDoctor) { showToast("请选择一位医生", "warning"); return; }
                    step++;
                } else {
                    try {
                        const result = await api.post("/registrations", {
                            case_no: user.ref_id,
                            doctor_id: selectedDoctor.doctor_id,
                            schedule_id: selectedDoctor.schedule_id,
                            reg_type: $("visitTypeLabel").textContent,
                        });
                        showToast(`挂号成功！挂号ID：${result.reg_id}`, "success");
                        step = 1; selectedDept = null; selectedDoctor = null;
                    } catch (err) { showToast(err.message, "danger"); return; }
                }
                renderStep();
            });
        }

        renderStep();
    } catch (err) {
        $("patientContent").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`;
    }
}

// ============================================================
// 缴费 & 历史
// ============================================================

async function renderPatientPayment() {
    const user = getUser();
    renderPatientShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/patient/payment");

    const tabs = [
        { id: "payUnpaid",   label: "待支付",   icon: "💳" },
        { id: "payOutpatient", label: "门诊历史", icon: "🩺" },
        { id: "payInpatient",  label: "住院历史", icon: "🏥" },
    ];

    $("patientContent").innerHTML = `
      <h4>💰 缴费 & 历史</h4>
      <div class="page-card">
        <ul class="nav nav-tabs mb-3" id="payTabs">
          ${tabs.map((t, i) => `<li class="nav-item">
            <a class="nav-link ${i === 0 ? "active" : ""}" data-tab="${t.id}" href="#">${t.icon} ${t.label}</a>
          </li>`).join("")}
        </ul>
        <div id="payContent">加载中...</div>
      </div>`;

    async function loadTab(tabId) {
        $("payContent").innerHTML = `<div class="text-center py-3 text-muted">加载中...</div>`;
        try {
            if (tabId === "payUnpaid") await renderUnpaid(user);
            else if (tabId === "payOutpatient") await renderOutpatientHistory(user);
            else await renderInpatientHistory(user);
        } catch (err) { $("payContent").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`; }
    }

    // ----- 待支付 -----
    async function renderUnpaid(user) {
        const unpaid = await api.get(`/payment/unpaid?case_no=${user.ref_id}`);
        if (unpaid.length === 0) {
            $("payContent").innerHTML = `<p class="text-muted">暂无待支付处方 ✅</p>`;
            return;
        }
        const cols = [
            { key: "presc_id", label: "处方ID" },
            { key: "presc_time", label: "开方时间" },
            { key: "doctor_name", label: "医生" },
            { key: "dept_name", label: "科室" },
        ];
        $("payContent").innerHTML = `<div id="unpaidTable"></div><div id="feeDetail" class="mt-3"></div>`;
        mountTable("unpaidTable", cols, unpaid, [
            { label: "查看费用", class: "btn-outline-primary btn-sm", click: async (row) => {
                const fee = await api.get(`/payment/prescriptions/${row.presc_id}/fee`);
                $("feeDetail").innerHTML = `
                  <div class="page-card"><h6>费用 — 处方 #${row.presc_id}</h6>
                    <p class="fw-bold">合计：¥${fee.total_fee}</p>
                    <button class="btn btn-success" id="payBtn">确认支付 ¥${fee.total_fee}</button></div>`;
                $("payBtn").addEventListener("click", async () => {
                    try {
                        await api.post("/payment/pay", { presc_id: row.presc_id });
                        showToast("支付成功！", "success");
                        loadTab("payUnpaid");
                    } catch (err) { showToast(err.message, "danger"); }
                });
            }},
        ]);
    }

    // ----- 门诊历史 -----
    async function renderOutpatientHistory(user) {
        const history = await api.get(`/payment/history/outpatient?case_no=${user.ref_id}`);
        if (history.length === 0) {
            $("payContent").innerHTML = `<p class="text-muted">暂无门诊记录</p>`;
            return;
        }
        const cols = [
            { key: "time", label: "挂号日期" },
            { key: "dept_name", label: "科室" },
            { key: "doctor_name", label: "医生" },
            { key: "symptom_desc", label: "诊断" },
            { key: "pay_status", label: "支付状态" },
        ];
        mountTable("payContent", cols, history);
    }

    // ----- 住院历史 -----
    async function renderInpatientHistory(user) {
        const history = await api.get(`/payment/history/inpatient?case_no=${user.ref_id}`);
        if (history.length === 0) {
            $("payContent").innerHTML = `<p class="text-muted">暂无住院记录</p>`;
            return;
        }
        const cols = [
            { key: "file_no", label: "档案号" },
            { key: "ward_no", label: "病房" },
            { key: "bed_no", label: "床位" },
            { key: "admit_time", label: "入院时间" },
            { key: "discharge_time", label: "出院时间" },
            { key: "deposit_balance", label: "预交金余额" },
        ];
        $("payContent").innerHTML = `<div id="inpatientHistoryTable"></div><div id="costDetail" class="mt-3"></div>`;
        mountTable("inpatientHistoryTable", cols, history, [
            { label: "费用明细", class: "btn-outline-primary btn-sm", click: async (row) => {
                const costs = await api.get(`/payment/history/inpatient/${row.file_no}/costs`);
                let html = `<h6>住院费用明细 — 档案 #${row.file_no}</h6>
                  <table class="table table-sm"><thead><tr><th>日期</th><th>费用</th><th>药品(单价×数量)</th><th>药费</th></tr></thead><tbody>`;
                costs.forEach(r => {
                    html += `<tr><td>${r.record_date}</td><td>¥${r.daily_fee || 0}</td>
                      <td>${escapeHtml(r.med_name || "")} ¥${r.unit_price || 0}×${r.qty || 0}</td>
                      <td>¥${r.drug_cost || 0}</td></tr>`;
                });
                html += `</tbody></table>`;
                $("costDetail").innerHTML = `<div class="page-card">${html}</div>`;
            }},
        ]);
    }

    document.querySelectorAll("#payTabs [data-tab]").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            document.querySelectorAll("#payTabs .nav-link").forEach(l => l.classList.remove("active"));
            link.classList.add("active");
            loadTab(link.dataset.tab);
        });
    });
    loadTab("payUnpaid");
}
