/**
 * 医生模块 — 3 个页面
 *
 *   /doctor          今日工作台
 *   /doctor/consult  门诊接诊
 *   /doctor/rounds   每日查房
 */

function renderDoctorShell(contentHtml, activeNav) {
    const user = getUser();
    const navItems = [
        { hash: "/doctor",         icon: "📋", label: "工作台" },
        { hash: "/doctor/consult", icon: "🩺", label: "门诊接诊" },
        { hash: "/doctor/rounds",  icon: "🏥", label: "每日查房" },
    ];

    const navLinks = navItems.map(m =>
        `<li class="nav-item">
          <a class="nav-link ${activeNav === m.hash ? "active" : ""}" href="#${m.hash}">${m.icon} ${m.label}</a>
        </li>`
    ).join("");

    $("appMain").innerHTML = `
      ${renderNavbar(user)}
      <ul class="nav nav-tabs px-3 pt-2 bg-white border-bottom">${navLinks}</ul>
      <div class="container-fluid py-3" id="doctorContent">${contentHtml}</div>`;
}

// ============================================================
// 工作台
// ============================================================

async function renderDoctorDashboard() {
    const user = getUser();
    renderDoctorShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/doctor");

    try {
        const queue = await api.get(`/outpatient/queue?doctor_id=${user.ref_id}`);

        const cols = [
            { key: "reg_id", label: "挂号ID" },
            { key: "case_no", label: "病案号" },
            { key: "patient_name", label: "患者" },
            { key: "reg_date", label: "挂号时间" },
            { key: "reg_type", label: "初/复诊" },
        ];

        $("doctorContent").innerHTML = `
          <h4>📋 今日工作台</h4>
          <div class="row g-3 mb-4">
            <div class="col-md-3"><div class="stat-card">
              <div class="stat-number">${queue.length}</div>
              <div class="stat-label">待就诊病人</div>
            </div></div>
            <div class="col-md-3"><div class="stat-card">
              <a href="#/doctor/rounds" class="btn btn-outline-primary btn-sm mt-2">🏥 去查房</a>
            </div></div>
            <div class="col-md-3"><div class="stat-card">
              <a href="#/doctor/consult" class="btn btn-outline-success btn-sm mt-2">🩺 门诊接诊</a>
            </div></div>
          </div>
          <div class="page-card">
            <h5>待就诊排队</h5>
            <div id="queueTable"></div>
          </div>`;

        mountTable("queueTable", cols, queue, [
            { label: "接诊", class: "btn-primary btn-sm", click: (row) => startConsult(row) },
        ]);
    } catch (err) {
        $("doctorContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

function startConsult(row) {
    sessionStorage.setItem("consult_patient", JSON.stringify(row));
    router.go("/doctor/consult");
}

// ============================================================
// 门诊接诊
// ============================================================

async function renderDoctorConsult() {
    const user = getUser();
    renderDoctorShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/doctor/consult");

    try {
        const [medicines, queue] = await Promise.all([
            api.get("/outpatient/medicines"),
            api.get(`/outpatient/queue?doctor_id=${user.ref_id}`),
        ]);

        let selectedPatient = null;
        const saved = sessionStorage.getItem("consult_patient");
        if (saved) { selectedPatient = JSON.parse(saved); sessionStorage.removeItem("consult_patient"); }

        let cart = [];

        function renderPage() {
            let patientSection = "";
            if (!selectedPatient) {
                patientSection = `
                  <h6>选择要接诊的病人</h6>
                  <div class="row g-2">${queue.length === 0 ? '<p class="text-muted">暂无待就诊病人</p>' : queue.map(p => `
                    <div class="col-md-4">
                      <div class="role-card patient-card" data-reg-id="${p.reg_id}">
                        <strong>${escapeHtml(p.patient_name)}</strong>
                        <div class="small text-muted">病案号 ${p.case_no} · ${p.reg_type}</div>
                        <div class="small text-muted">挂号时间 ${p.reg_date}</div>
                      </div>
                    </div>`).join("")}</div>`;
            } else {
                patientSection = `
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <div><strong>当前病人：</strong>${escapeHtml(selectedPatient.patient_name)}
                      <span class="text-muted ms-2">病案号 ${selectedPatient.case_no} · ${selectedPatient.reg_type}</span></div>
                    <button class="btn btn-outline-secondary btn-sm" id="changePatient">更换病人</button>
                  </div>`;
            }

            const medRows = medicines.map(m => `
              <tr><td>${escapeHtml(m.med_name)}</td><td>${escapeHtml(m.specification)}</td>
                <td>¥${m.unit_price}</td><td>${m.stock_qty}</td>
                <td><button class="btn btn-outline-primary btn-sm add-to-cart"
                  data-med-id="${m.medicine_id}" data-med-name="${escapeHtml(m.med_name)}" data-med-price="${m.unit_price}">＋ 添加</button></td></tr>`).join("");

            const cartRows = cart.map((item, i) => `
              <tr><td>${escapeHtml(item.medicine_name)}</td><td>¥${item.unit_price}</td>
                <td><input type="number" class="form-control form-control-sm cart-qty" value="${item.qty}" min="1" data-idx="${i}" style="width:80px"></td>
                <td>¥${(item.qty * item.unit_price).toFixed(2)}</td>
                <td><button class="btn btn-outline-danger btn-sm cart-remove" data-idx="${i}">✕</button></td></tr>`).join("");
            const cartTotal = cart.reduce((s, i) => s + i.qty * i.unit_price, 0);

            $("doctorContent").innerHTML = `
              <h4>🩺 门诊接诊</h4>
              <div class="page-card mb-3">${patientSection}</div>
              ${selectedPatient ? `
                <div class="row">
                  <div class="col-md-6">
                    <div class="page-card"><h6>💊 可选药品 <span class="small text-muted">（仅显示有库存）</span></h6>
                      <div style="max-height:400px;overflow-y:auto">
                        <table class="table table-sm"><thead><tr><th>名称</th><th>规格</th><th>单价</th><th>库存</th><th></th></tr></thead>
                          <tbody>${medRows}</tbody></table></div></div></div>
                  <div class="col-md-6">
                    <div class="page-card"><h6>📝 处方明细</h6>
                      ${cart.length === 0 ? '<p class="text-muted">尚未添加药品</p>' : `
                        <table class="table table-sm"><thead><tr><th>药品</th><th>单价</th><th>数量</th><th>小计</th><th></th></tr></thead>
                          <tbody>${cartRows}</tbody></table>
                        <div class="text-end fw-bold">药费合计：¥${cartTotal.toFixed(2)}</div>`}
                      <button class="btn btn-primary w-100 mt-3" id="submitPresc" ${cart.length === 0 ? "disabled" : ""}>
                        提交处方</button></div></div></div>` : ""}`;

            document.querySelectorAll(".patient-card").forEach(card => {
                card.addEventListener("click", () => {
                    const regId = parseInt(card.dataset.regId);
                    selectedPatient = queue.find(p => p.reg_id === regId);
                    renderPage();
                });
            });

            if (selectedPatient) {
                $("changePatient").addEventListener("click", () => { selectedPatient = null; cart = []; renderPage(); });
            }

            document.querySelectorAll(".add-to-cart").forEach(btn => {
                btn.addEventListener("click", () => {
                    const medId = parseInt(btn.dataset.medId);
                    const existing = cart.find(i => i.medicine_id === medId);
                    if (existing) existing.qty++;
                    else cart.push({ medicine_id: medId, medicine_name: btn.dataset.medName, unit_price: parseFloat(btn.dataset.medPrice), qty: 1 });
                    renderPage();
                });
            });

            document.querySelectorAll(".cart-qty").forEach(inp => {
                inp.addEventListener("change", () => {
                    const idx = parseInt(inp.dataset.idx), qty = parseInt(inp.value);
                    if (qty > 0) cart[idx].qty = qty; else cart.splice(idx, 1);
                    renderPage();
                });
            });

            document.querySelectorAll(".cart-remove").forEach(btn => {
                btn.addEventListener("click", () => { cart.splice(parseInt(btn.dataset.idx), 1); renderPage(); });
            });

            const submitBtn = $("submitPresc");
            if (submitBtn) {
                submitBtn.addEventListener("click", async () => {
                    if (cart.length === 0) { showToast("请添加药品", "warning"); return; }
                    submitBtn.disabled = true; submitBtn.textContent = "提交中...";
                    try {
                        const result = await api.post("/outpatient/prescriptions", {
                            reg_id: selectedPatient.reg_id,
                            doctor_id: user.ref_id,
                            symptom_desc: "",
                            details: cart.map(i => ({ medicine_id: i.medicine_id, qty: i.qty, usage_inst: "" })),
                        });
                        showToast(`处方已开具！诊疗费 ¥${result.consultation_fee} + 药费 ¥${result.drug_fee} = 总计 ¥${result.total_fee}`, "success");
                        selectedPatient = null; cart = [];
                        // 刷新药品
                        const freshMeds = await api.get("/outpatient/medicines");
                        medicines.length = 0; medicines.push(...freshMeds);
                        renderPage();
                    } catch (err) { showToast(err.message, "danger"); }
                    submitBtn.disabled = false; submitBtn.textContent = "提交处方";
                });
            }
        }

        renderPage();
    } catch (err) {
        $("doctorContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

// ============================================================
// 每日查房
// ============================================================

async function renderDoctorRounds() {
    const user = getUser();
    renderDoctorShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/doctor/rounds");

    async function load() {
        try {
            const [inpatients, medicines] = await Promise.all([
                api.get(`/rounds/my-inpatients?doctor_id=${user.ref_id}`),
                api.get("/outpatient/medicines"),
            ]);

            const cols = [
                { key: "file_no", label: "档案号" }, { key: "case_no", label: "病案号" },
                { key: "patient_name", label: "患者" }, { key: "ward_no", label: "病房" },
                { key: "bed_no", label: "床位" }, { key: "admit_time", label: "入院时间" },
                { key: "deposit_balance", label: "预交金余额" },
            ];

            $("doctorContent").innerHTML = `
              <h4>🏥 每日查房</h4>
              <div class="page-card"><h5>我的在院病人（${inpatients.length}人）</h5>
                <div id="inpatientTable"></div></div>
              <div id="roundForm" class="page-card" style="display:none"></div>`;

            mountTable("inpatientTable", cols, inpatients, [
                { label: "查房", class: "btn-primary btn-sm", click: (row) => showRoundForm(row, medicines) },
            ]);
        } catch (err) {
            $("doctorContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
        }
    }

    load();

    async function showRoundForm(patient, medicines) {
        let cart = [];
        const chargeRate = patient.charge_rate || 50;

        function renderForm() {
            const medRows = medicines.map(m => `
              <tr><td>${escapeHtml(m.med_name)}</td><td>¥${m.unit_price}</td><td>${m.stock_qty}</td>
                <td><button class="btn btn-outline-primary btn-sm round-add-med"
                  data-med-id="${m.medicine_id}" data-med-name="${escapeHtml(m.med_name)}" data-med-price="${m.unit_price}">＋</button></td></tr>`).join("");

            const cartRows = cart.map((item, i) => `
              <tr><td>${escapeHtml(item.medicine_name)}</td><td>¥${item.unit_price}</td>
                <td><input type="number" class="form-control form-control-sm round-qty" value="${item.qty}" min="1" data-idx="${i}" style="width:80px"></td>
                <td>¥${(item.qty * item.unit_price).toFixed(2)}</td>
                <td><button class="btn btn-outline-danger btn-sm round-remove" data-idx="${i}">✕</button></td></tr>`).join("");
            const drugFee = cart.reduce((s, i) => s + i.qty * i.unit_price, 0);
            const totalFee = chargeRate + drugFee;

            $("roundForm").style.display = "";
            $("roundForm").innerHTML = `
              <h5>查房 — ${escapeHtml(patient.patient_name)}（档案号 ${patient.file_no}）</h5>
              <div class="mb-3"><label class="form-label">治疗方案</label>
                <textarea class="form-control" id="roundDesc" rows="3" placeholder="记录今日治疗方案..."></textarea></div>
              <div class="row"><div class="col-md-6">
                <div class="page-card"><h6>可选药品</h6>
                  <div style="max-height:300px;overflow-y:auto">
                    <table class="table table-sm"><thead><tr><th>药品</th><th>单价</th><th>库存</th><th></th></tr></thead>
                      <tbody>${medRows}</tbody></table></div></div></div>
              <div class="col-md-6"><div class="page-card"><h6>处方</h6>
                ${cart.length ? `<table class="table table-sm"><thead><tr><th>药品</th><th>单价</th><th>数量</th><th>小计</th><th></th></tr></thead>
                  <tbody>${cartRows}</tbody></table>` : '<p class="text-muted">未添加药品</p>'}
                <table class="table table-sm">
                  <tr><td>床位费</td><td class="text-end">¥${chargeRate.toFixed(2)}</td></tr>
                  <tr><td>药费</td><td class="text-end">¥${drugFee.toFixed(2)}</td></tr>
                  <tr class="table-active fw-bold"><td>当日合计</td><td class="text-end">¥${totalFee.toFixed(2)}</td></tr></table>
                <button class="btn btn-primary w-100" id="submitRound">提交查房记录</button></div></div></div>`;

            document.querySelectorAll(".round-add-med").forEach(btn => {
                btn.addEventListener("click", () => {
                    const medId = parseInt(btn.dataset.medId);
                    const existing = cart.find(i => i.medicine_id === medId);
                    if (existing) existing.qty++;
                    else cart.push({ medicine_id: medId, medicine_name: btn.dataset.medName, unit_price: parseFloat(btn.dataset.medPrice), qty: 1 });
                    renderForm();
                });
            });
            document.querySelectorAll(".round-qty").forEach(inp => {
                inp.addEventListener("change", () => {
                    const idx = parseInt(inp.dataset.idx), qty = parseInt(inp.value);
                    if (qty > 0) cart[idx].qty = qty; else cart.splice(idx, 1);
                    renderForm();
                });
            });
            document.querySelectorAll(".round-remove").forEach(btn => {
                btn.addEventListener("click", () => { cart.splice(parseInt(btn.dataset.idx), 1); renderForm(); });
            });

            $("submitRound").addEventListener("click", async () => {
                $("submitRound").disabled = true; $("submitRound").textContent = "提交中...";
                try {
                    await api.post("/rounds/rounds", {
                        file_no: patient.file_no,
                        doctor_id: user.ref_id,
                        treatment_desc: $("roundDesc").value.trim(),
                        details: cart.map(i => ({ medicine_id: i.medicine_id, qty: i.qty, usage_inst: "" })),
                    });
                    showToast(`查房完成！当日费用 ¥${totalFee.toFixed(2)}，预交金余额已更新`, "success");
                    $("roundForm").style.display = "none"; cart = []; load();
                } catch (err) { showToast(err.message, "danger"); }
                $("submitRound").disabled = false; $("submitRound").textContent = "提交查房记录";
            });
        }

        renderForm();
    }
}
