/**
 * 管理员模块 — 8 个页面
 *
 *   /admin             统计概览
 *   /admin/departments  科室 CRUD
 *   /admin/doctors      医生 CRUD
 *   /admin/medicines    药品 CRUD
 *   /admin/schedules    排班 CRUD
 *   /admin/admission    入院登记
 *   /admin/discharge    出院结算
 *   /admin/stats        统计报表
 */

function renderAdminShell(contentHtml, activeMenu) {
    const user = getUser();
    const menuItems = [
        { hash: "/admin",             icon: "📊", label: "统计概览" },
        { hash: "/admin/departments", icon: "🏢", label: "科室管理" },
        { hash: "/admin/doctors",     icon: "👨‍⚕️", label: "医生管理" },
        { hash: "/admin/medicines",   icon: "💊", label: "药品管理" },
        { hash: "/admin/schedules",   icon: "📅", label: "排班管理" },
        { hash: "/admin/admission",   icon: "🏥", label: "入院登记" },
        { hash: "/admin/discharge",   icon: "📋", label: "出院结算" },
        { hash: "/admin/stats",       icon: "📈", label: "统计报表" },
    ];

    const sidebarLinks = menuItems.map(m =>
        `<a class="nav-link ${activeMenu === m.hash ? "active" : ""}"
          href="#${m.hash}"><span>${m.icon} ${m.label}</span></a>`
    ).join("");

    $("appMain").innerHTML = `
      ${renderNavbar(user)}
      <div class="admin-layout">
        <nav class="admin-sidebar">
          <div class="px-3 mb-2 small text-muted">管理功能</div>
          ${sidebarLinks}
        </nav>
        <main class="admin-content" id="adminContent">${contentHtml}</main>
      </div>`;
}

// ============================================================
// 统计概览
// ============================================================

async function renderAdminDashboard() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin");

    try {
        const [depts, doctors, beds] = await Promise.all([
            api.get("/admin/departments"),
            api.get("/admin/doctors"),
            api.get("/stats/beds"),
        ]);

        const occupiedBeds = beds.reduce((s, b) => s + (b.occupied_beds || 0), 0);
        const totalWards = beds.reduce((s, b) => s + (b.ward_count || 0), 0);

        $("adminContent").innerHTML = `
          <h4 class="mb-3">📊 统计概览</h4>
          <div class="row g-3 mb-4">
            <div class="col-md-3"><div class="stat-card">
              <div class="stat-number">${depts.length}</div><div class="stat-label">科室总数</div>
            </div></div>
            <div class="col-md-3"><div class="stat-card">
              <div class="stat-number">${doctors.length}</div><div class="stat-label">医生总数</div>
            </div></div>
            <div class="col-md-3"><div class="stat-card">
              <div class="stat-number">${occupiedBeds}</div><div class="stat-label">当前住院人数</div>
            </div></div>
            <div class="col-md-3"><div class="stat-card">
              <div class="stat-number">${totalWards}</div><div class="stat-label">病房总数</div>
            </div></div>
          </div>
          <div class="page-card">
            <h5>快捷操作</h5>
            <div class="row g-2">
              <div class="col-md-3"><a href="#/admin/departments" class="btn btn-outline-primary w-100">🏢 科室管理</a></div>
              <div class="col-md-3"><a href="#/admin/doctors" class="btn btn-outline-primary w-100">👨‍⚕️ 医生管理</a></div>
              <div class="col-md-3"><a href="#/admin/schedules" class="btn btn-outline-primary w-100">📅 排班管理</a></div>
              <div class="col-md-3"><a href="#/admin/stats" class="btn btn-outline-primary w-100">📈 统计报表</a></div>
            </div>
          </div>`;
    } catch (err) {
        $("adminContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

// ============================================================
// 科室管理
// ============================================================

async function renderAdminDepartments() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/departments");

    try {
        const departments = await api.get("/admin/departments");
        renderDepartmentsPage(departments);
    } catch (err) {
        $("adminContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

function renderDepartmentsPage(departments) {
    const cols = [
        { key: "dept_id", label: "ID" },
        { key: "dept_name", label: "科室名称" },
        { key: "dept_type", label: "科室类型" },
        { key: "phone", label: "电话" },
    ];

    let html = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4>🏢 科室管理</h4>
        <button class="btn btn-primary" onclick="showDeptModal()">＋ 新增科室</button>
      </div>
      <div class="page-card" id="deptTable"></div>`;

    $("adminContent").innerHTML = html;
    mountTable("deptTable", cols, departments, [
        { label: "编辑", class: "btn-outline-primary btn-sm", click: (row) => showDeptModal(row) },
        { label: "删除", class: "btn-outline-danger btn-sm", click: (row) => deleteDept(row) },
    ]);
}

function showDeptModal(row = null) {
    const isEdit = !!row;
    const title = isEdit ? "编辑科室" : "新增科室";
    let body = `
      <div class="mb-3">
        <label class="form-label">科室名称</label>
        <input class="form-control" id="deptName" value="${escapeHtml(row?.dept_name || "")}">
      </div>
      <div class="mb-3">
        <label class="form-label">科室类型</label>
        <input class="form-control" id="deptType" value="${escapeHtml(row?.dept_type || "")}">
      </div>
      <div class="mb-3">
        <label class="form-label">电话</label>
        <input class="form-control" id="deptPhone" value="${escapeHtml(row?.phone || "")}">
      </div>`;

    const modal = createModal(title, body, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "保存", class: "btn-primary", click: async () => {
            const payload = {
                dept_name: $("deptName").value.trim(),
                dept_type: $("deptType").value.trim(),
                phone: $("deptPhone").value.trim(),
            };
            if (!payload.dept_name) { showToast("科室名称不能为空", "warning"); return; }
            try {
                if (isEdit) {
                    await api.put(`/admin/departments/${row.dept_id}`, payload);
                } else {
                    await api.post("/admin/departments", payload);
                }
                modal.hide();
                showToast(isEdit ? "科室已更新" : "科室已创建", "success");
                renderAdminDepartments();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    modal.show();
}

async function deleteDept(row) {
    const m = createModal("确认删除", `
      <p>确定要删除科室 <strong>${escapeHtml(row.dept_name)}</strong> 吗？</p>
      <p class="text-muted small">删除前将检查该科室下是否有医生和病房。</p>`, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "确认删除", class: "btn-danger", click: async () => {
            try {
                await api.delete(`/admin/departments/${row.dept_id}`);
                m.hide();
                showToast("科室已删除", "success");
                renderAdminDepartments();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    m.show();
}

// ============================================================
// 医生管理
// ============================================================

async function renderAdminDoctors() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/doctors");

    try {
        const [doctors, departments] = await Promise.all([
            api.get("/admin/doctors"),
            api.get("/admin/departments"),
        ]);
        renderDoctorsPage(doctors, departments);
    } catch (err) {
        $("adminContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

function renderDoctorsPage(doctors, departments) {
    const cols = [
        { key: "doctor_id", label: "ID" },
        { key: "name", label: "姓名" },
        { key: "dept_name", label: "科室" },
        { key: "title", label: "职称" },
        { key: "consultation_fee", label: "诊疗费(元)" },
        { key: "phone", label: "电话" },
    ];

    let html = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4>👨‍⚕️ 医生管理</h4>
        <button class="btn btn-primary" onclick="showDoctorModal()">＋ 新增医生</button>
      </div>
      <div class="page-card" id="doctorTable"></div>`;

    $("adminContent").innerHTML = html;
    mountTable("doctorTable", cols, doctors, [
        { label: "编辑", class: "btn-outline-primary btn-sm", click: (row) => showDoctorModal(row, departments) },
        { label: "删除", class: "btn-outline-danger btn-sm", click: (row) => deleteDoctor(row) },
    ]);
}

function showDoctorModal(row = null, departments = []) {
    const isEdit = !!row;
    const title = isEdit ? "编辑医生" : "新增医生";
    const deptOptions = departments.map(d =>
        `<option value="${d.dept_id}" ${row?.dept_id === d.dept_id ? "selected" : ""}>${escapeHtml(d.dept_name)}</option>`
    ).join("");

    let body = `
      <div class="mb-3">
        <label class="form-label">姓名</label>
        <input class="form-control" id="docName" value="${escapeHtml(row?.name || "")}">
      </div>
      <div class="mb-3">
        <label class="form-label">性别</label>
        <select class="form-select" id="docGender">
          <option value="男" ${row?.gender === "男" ? "selected" : ""}>男</option>
          <option value="女" ${row?.gender === "女" ? "selected" : ""}>女</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">科室</label>
        <select class="form-select" id="docDept">${deptOptions}</select>
      </div>
      <div class="mb-3">
        <label class="form-label">职称</label>
        <select class="form-select" id="docTitle">
          <option ${row?.title === "主任医师" ? "selected" : ""}>主任医师</option>
          <option ${row?.title === "主治医师" ? "selected" : ""}>主治医师</option>
          <option ${row?.title === "住院医师" ? "selected" : ""}>住院医师</option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">诊疗费</label>
        <input type="number" class="form-control" id="docFee" value="${row?.consultation_fee || 0}" min="0" step="0.01">
      </div>
      <div class="mb-3">
        <label class="form-label">电话</label>
        <input class="form-control" id="docPhone" value="${escapeHtml(row?.phone || "")}">
      </div>
      ${!isEdit ? `<div class="mb-3">
        <label class="form-label">初始密码</label>
        <input class="form-control" id="docPassword" value="123456" type="text">
      </div>` : ""}`;

    const modal = createModal(title, body, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "保存", class: "btn-primary", click: async () => {
            const payload = {
                name: $("docName").value.trim(),
                gender: $("docGender").value,
                dept_id: parseInt($("docDept").value),
                title: $("docTitle").value,
                consultation_fee: parseFloat($("docFee").value),
                phone: $("docPhone").value.trim(),
            };
            if (!isEdit) payload.password = $("docPassword").value.trim();
            if (!payload.name) { showToast("姓名不能为空", "warning"); return; }
            try {
                if (isEdit) {
                    await api.put(`/admin/doctors/${row.doctor_id}`, payload);
                } else {
                    await api.post("/admin/doctors", payload);
                }
                modal.hide();
                showToast(isEdit ? "医生已更新" : "医生已创建", "success");
                renderAdminDoctors();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    modal.show();
}

async function deleteDoctor(row) {
    const m = createModal("确认删除", `
      <p>确定要删除医生 <strong>${escapeHtml(row.name)}</strong> 吗？</p>
      <p class="text-muted small">删除前将检查排班、挂号和住院档案。</p>`, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "确认删除", class: "btn-danger", click: async () => {
            try {
                await api.delete(`/admin/doctors/${row.doctor_id}`);
                m.hide();
                showToast("医生已删除", "success");
                renderAdminDoctors();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    m.show();
}

// ============================================================
// 药品管理
// ============================================================

async function renderAdminMedicines() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/medicines");

    try {
        const medicines = await api.get("/admin/medicines");
        renderMedicinesPage(medicines);
    } catch (err) {
        $("adminContent").innerHTML = `<div class="alert alert-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
}

function renderMedicinesPage(medicines) {
    const cols = [
        { key: "medicine_id", label: "ID" },
        { key: "med_name", label: "药品名称" },
        { key: "specification", label: "规格" },
        { key: "unit", label: "单位" },
        { key: "unit_price", label: "单价(元)" },
        { key: "stock_qty", label: "库存" },
    ];

    let html = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4>💊 药品管理</h4>
        <button class="btn btn-primary" onclick="showMedicineModal()">＋ 新增药品</button>
      </div>
      <div class="page-card" id="medicineTable"></div>`;

    $("adminContent").innerHTML = html;
    mountTable("medicineTable", cols, medicines, [
        { label: "编辑", class: "btn-outline-primary btn-sm", click: (row) => showMedicineModal(row) },
    ]);
}

function showMedicineModal(row = null) {
    const isEdit = !!row;
    const body = `
      <div class="mb-3">
        <label class="form-label">药品名称</label>
        <input class="form-control" id="medName" value="${escapeHtml(row?.med_name || "")}">
      </div>
      <div class="mb-3">
        <label class="form-label">规格</label>
        <input class="form-control" id="medSpec" value="${escapeHtml(row?.specification || "")}">
      </div>
      <div class="mb-3">
        <label class="form-label">单位</label>
        <input class="form-control" id="medUnit" value="${escapeHtml(row?.unit || "盒")}">
      </div>
      <div class="mb-3">
        <label class="form-label">单价(元)</label>
        <input type="number" class="form-control" id="medPrice" value="${row?.unit_price || 0}" min="0" step="0.01">
      </div>
      <div class="mb-3">
        <label class="form-label">库存</label>
        <input type="number" class="form-control" id="medStock" value="${row?.stock_qty || 0}" min="0" step="1">
      </div>`;

    const modal = createModal(isEdit ? "编辑药品" : "新增药品", body, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "保存", class: "btn-primary", click: async () => {
            const payload = {
                med_name: $("medName").value.trim(),
                specification: $("medSpec").value.trim(),
                unit: $("medUnit").value.trim(),
                unit_price: parseFloat($("medPrice").value),
                stock_qty: parseInt($("medStock").value),
            };
            if (!payload.med_name) { showToast("药品名称不能为空", "warning"); return; }
            try {
                if (isEdit) {
                    await api.put(`/admin/medicines/${row.medicine_id}`, payload);
                } else {
                    await api.post("/admin/medicines", payload);
                }
                modal.hide();
                showToast(isEdit ? "药品已更新" : "药品已创建", "success");
                renderAdminMedicines();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    modal.show();
}

// ============================================================
// 排班管理
// ============================================================

async function renderAdminSchedules() {
    renderAdminShell(`
      <h4>📅 排班管理</h4>
      <div class="page-card">
        <button class="btn btn-primary mb-3" onclick="showScheduleModal()">＋ 新增排班</button>
        <div id="scheduleTable">加载中...</div>
      </div>`, "/admin/schedules");
    await loadSchedules();
}

async function loadSchedules() {
    try {
        const schedules = await api.get("/schedules");
        const cols = [
            { key: "schedule_id", label: "ID" },
            { key: "sched_date", label: "日期" },
            { key: "doctor_name", label: "医生" },
            { key: "dept_name", label: "科室" },
            { key: "start_time", label: "开始" },
            { key: "end_time", label: "结束" },
            { key: "sched_type", label: "类型" },
            { key: "clinic", label: "诊室" },
        ];
        mountTable("scheduleTable", cols, schedules, [
            { label: "编辑", class: "btn-outline-primary btn-sm", click: (row) => showScheduleModal(row) },
            { label: "删除", class: "btn-outline-danger btn-sm", click: (row) => deleteSchedule(row) },
        ]);
    } catch (err) {
        $("scheduleTable").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`;
    }
}

async function showScheduleModal(row = null) {
    const isEdit = !!row;
    const [doctors] = await Promise.all([api.get("/admin/doctors")]);
    const doctorOptions = doctors.map(d =>
        `<option value="${d.doctor_id}" ${row?.doctor_id === d.doctor_id ? "selected" : ""}>${escapeHtml(d.name)} (${escapeHtml(d.dept_name)})</option>`
    ).join("");

    const body = `
      <div class="mb-3">
        <label class="form-label">医生</label>
        <select class="form-select" id="schedDoctor">${doctorOptions}</select>
      </div>
      <div class="mb-3">
        <label class="form-label">日期</label>
        <input type="date" class="form-control" id="schedDate" value="${row?.sched_date || ""}">
      </div>
      <div class="row mb-3">
        <div class="col">
          <label class="form-label">开始时间</label>
          <input type="time" class="form-control" id="schedStart" value="${row?.start_time || ""}">
        </div>
        <div class="col">
          <label class="form-label">结束时间</label>
          <input type="time" class="form-control" id="schedEnd" value="${row?.end_time || ""}">
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">排班类型</label>
        <select class="form-select" id="schedType">
          <option value="门诊坐诊" ${row?.sched_type === "门诊坐诊" ? "selected" : ""}>门诊坐诊</option>
          <option value="住院巡诊" ${row?.sched_type === "住院巡诊" ? "selected" : ""}>住院巡诊</option>
        </select>
      </div>
      <div class="mb-3" id="clinicGroup">
        <label class="form-label">诊室 <span class="text-muted small">（门诊必填）</span></label>
        <input class="form-control" id="schedClinic" value="${escapeHtml(row?.clinic || "")}">
      </div>`;

    const modal = createModal(isEdit ? "编辑排班" : "新增排班", body, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "保存", class: "btn-primary", click: async () => {
            const schedType = $("schedType").value;
            const clinic = $("schedClinic").value.trim();
            if (schedType === "门诊坐诊" && !clinic) { showToast("门诊坐诊必须指定诊室", "warning"); return; }
            const payload = {
                doctor_id: parseInt($("schedDoctor").value),
                sched_date: $("schedDate").value,
                start_time: $("schedStart").value,
                end_time: $("schedEnd").value,
                sched_type: schedType,
                clinic: schedType === "住院巡诊" ? null : clinic,
            };
            if (!payload.sched_date || !payload.start_time || !payload.end_time) { showToast("日期和时间不能为空", "warning"); return; }
            if (payload.start_time >= payload.end_time) { showToast("结束时间必须晚于开始时间", "warning"); return; }
            try {
                if (isEdit) {
                    await api.put(`/schedules/${row.schedule_id}`, payload);
                } else {
                    await api.post("/schedules", payload);
                }
                modal.hide();
                showToast(isEdit ? "排班已更新" : "排班已创建", "success");
                loadSchedules();
            } catch (err) { showToast(err.message, "warning"); }
        }},
    ]);

    function toggleClinic() { $("clinicGroup").style.display = $("schedType").value === "门诊坐诊" ? "" : "none"; }
    $("schedType").addEventListener("change", toggleClinic);
    toggleClinic();
    modal.show();
}

async function deleteSchedule(row) {
    const m = createModal("确认删除", `<p>确定要删除排班记录 <strong>#${row.schedule_id}</strong> 吗？</p>`, [
        { text: "取消", class: "btn-secondary", dismiss: true },
        { text: "确认删除", class: "btn-danger", click: async () => {
            try {
                await api.delete(`/schedules/${row.schedule_id}`);
                m.hide(); showToast("排班已删除", "success"); loadSchedules();
            } catch (err) { showToast(err.message, "danger"); }
        }},
    ]);
    m.show();
}

// ============================================================
// 入院登记 — 3 步表单
// ============================================================

async function renderAdminAdmission() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/admission");

    try {
        const departments = await api.get("/admin/departments");
        let step = 1, selectedDept = null, selectedWard = null, selectedBed = null, wards = [], beds = [];

        function renderStep() {
            const stepBar = [
                { num: 1, label: "选择科室" }, { num: 2, label: "选择病房/床位" }, { num: 3, label: "填写信息并确认" },
            ].map(s => `<div class="step ${s.num < step ? "done" : s.num === step ? "active" : ""}">${s.label}</div>`).join("");

            let body = "";
            if (step === 1) {
                body = `<h5>请选择科室</h5><div class="row g-2">${departments.map(d => `
                  <div class="col-md-4"><div class="role-card" data-dept-id="${d.dept_id}" data-dept-name="${escapeHtml(d.dept_name)}">
                    <span class="role-icon">🏢</span><strong>${escapeHtml(d.dept_name)}</strong>
                    <div class="small text-muted">${escapeHtml(d.dept_type || "")}</div>
                  </div></div>`).join("")}</div>`;
            } else if (step === 2) {
                body = `<h5>${escapeHtml(selectedDept.dept_name)} — 可选病房</h5>
                  <div id="wardList">${wards.length === 0 ? '<p class="text-muted">该科室暂无可用病房</p>' : ''}</div>
                  <div id="bedArea" class="mt-3"></div>`;
            } else {
                body = `<div class="row"><div class="col-md-6">
                  <div class="mb-3"><label class="text-muted">科室</label><div class="fw-bold">${escapeHtml(selectedDept.dept_name)}</div></div>
                  <div class="mb-3"><label class="text-muted">病房</label><div class="fw-bold">${escapeHtml(selectedWard.ward_no)}</div></div>
                  <div class="mb-3"><label class="text-muted">床位</label><div class="fw-bold">${escapeHtml(selectedBed.bed_no)}</div></div>
                </div><div class="col-md-6">
                  <div class="mb-3"><label class="form-label">病案号</label>
                    <input type="number" class="form-control" id="admCaseNo" placeholder="病人病案号"></div>
                  <div class="mb-3"><label class="form-label">主治医生</label>
                    <select class="form-select" id="admDoctor"></select></div>
                  <div class="mb-3"><label class="form-label">预交金(元)</label>
                    <input type="number" class="form-control" id="admDeposit" value="5000" min="0" step="0.01"></div>
                </div></div>`;
            }

            $("adminContent").innerHTML = `
              <h4>🏥 入院登记</h4>
              <div class="step-indicator">${stepBar}</div>
              <div class="page-card">${body}</div>
              <div class="d-flex justify-content-between">
                <button class="btn btn-secondary" id="backBtn" ${step === 1 ? "disabled" : ""}>上一步</button>
                <button class="btn btn-primary" id="nextBtn">${step === 3 ? "确认入院" : "下一步"}</button>
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
                wards.forEach(w => {
                    $("wardList").insertAdjacentHTML("beforeend", `
                      <div class="role-card d-inline-block m-1 ward-card" data-ward-id="${w.ward_id}" style="width:200px">
                        <strong>${escapeHtml(w.ward_no)}</strong>
                        <div class="small text-muted">空床 ${w.available_beds} / ${w.total_beds}</div>
                      </div>`);
                });
                document.querySelectorAll(".ward-card").forEach(card => {
                    card.addEventListener("click", async () => {
                        document.querySelectorAll(".ward-card").forEach(c => c.classList.remove("selected"));
                        card.classList.add("selected");
                        selectedWard = wards.find(w => w.ward_id === parseInt(card.dataset.wardId));
                        selectedBed = null;
                        try {
                            beds = await api.get(`/admission/beds?ward_id=${selectedWard.ward_id}`);
                            $("bedArea").innerHTML = `
                              <h6>空闲床位</h6><div class="row g-2">${beds.map(b => `
                                <div class="col-md-3"><div class="role-card bed-card" data-bed-id="${b.bed_id}" data-bed-no="${escapeHtml(b.bed_no)}">🛏️ ${escapeHtml(b.bed_no)}</div></div>
                              `).join("")}</div>`;
                            document.querySelectorAll(".bed-card").forEach(bc => {
                                bc.addEventListener("click", () => {
                                    document.querySelectorAll(".bed-card").forEach(b => b.classList.remove("selected"));
                                    bc.classList.add("selected");
                                    selectedBed = beds.find(b => b.bed_id === parseInt(bc.dataset.bedId));
                                });
                            });
                        } catch (err) { showToast(err.message, "danger"); }
                    });
                });
            }
            if (step === 3) {
                (async () => {
                    try {
                        const doctors = await api.get("/admin/doctors");
                        $("admDoctor").innerHTML = doctors.map(d =>
                            `<option value="${d.doctor_id}">${escapeHtml(d.name)} (${escapeHtml(d.title)})</option>`).join("");
                    } catch (err) { /* ignore */ }
                })();
            }

            $("backBtn").addEventListener("click", () => { step--; renderStep(); });
            $("nextBtn").addEventListener("click", async () => {
                if (step === 1) {
                    if (!selectedDept) { showToast("请选择一个科室", "warning"); return; }
                    try { wards = await api.get(`/admission/wards?dept_id=${selectedDept.dept_id}`); step++; }
                    catch (err) { showToast(err.message, "danger"); return; }
                } else if (step === 2) {
                    if (!selectedWard || !selectedBed) { showToast("请选择病房和床位", "warning"); return; }
                    step++;
                } else {
                    const caseNo = parseInt($("admCaseNo").value);
                    const deposit = parseFloat($("admDeposit").value);
                    const doctorId = parseInt($("admDoctor").value);
                    if (!caseNo) { showToast("请输入病案号", "warning"); return; }
                    if (!doctorId) { showToast("请选择主治医生", "warning"); return; }
                    if (deposit <= 0) { showToast("预交金必须大于0", "warning"); return; }
                    try {
                        await api.post("/admission", {
                            case_no: caseNo, ward_id: selectedWard.ward_id,
                            bed_id: selectedBed.bed_id, deposit_balance: deposit,
                            doctor_id: doctorId,
                        });
                        showToast("入院登记成功！", "success");
                        step = 1; selectedDept = null; selectedWard = null; selectedBed = null;
                    } catch (err) { showToast(err.message, "danger"); return; }
                }
                renderStep();
            });
        }
        renderStep();
    } catch (err) {
        $("adminContent").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`;
    }
}

// ============================================================
// 出院结算
// ============================================================

async function renderAdminDischarge() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/discharge");

    async function load() {
        try {
            const inpatients = await api.get("/admission");
            const cols = [
                { key: "file_no", label: "档案号" }, { key: "case_no", label: "病案号" },
                { key: "patient_name", label: "患者姓名" }, { key: "ward_no", label: "病房" },
                { key: "bed_no", label: "床位" }, { key: "admit_time", label: "入院时间" },
                { key: "deposit_balance", label: "预交金余额" },
            ];
            $("adminContent").innerHTML = `
              <h4>📋 出院结算</h4>
              <div class="page-card"><p class="text-muted">当前在院病人</p><div id="dischargeTable"></div></div>`;
            mountTable("dischargeTable", cols, inpatients, [
                { label: "结算出院", class: "btn-outline-warning btn-sm", click: (row) => doDischarge(row) },
            ]);
        } catch (err) { $("adminContent").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`; }
    }

    async function doDischarge(row) {
        try {
            const summary = await api.get(`/discharge/summary/${row.file_no}`);
            const settlement = (summary.final_balance || row.deposit_balance) - (summary.total_cost || 0);
            const m = createModal("出院结算确认", `
              <table class="table table-sm">
                <tr><td>档案号</td><td><strong>${row.file_no}</strong></td></tr>
                <tr><td>病案号</td><td>${row.case_no}</td></tr>
                <tr><td>患者</td><td>${escapeHtml(row.patient_name)}</td></tr>
                <tr><td>入院时间</td><td>${row.admit_time}</td></tr>
                <tr><td>住院天数</td><td>${summary.stay_days || 0} 天</td></tr>
                <tr><td>总费用</td><td class="text-danger fw-bold">¥${summary.total_cost || 0}</td></tr>
                <tr><td>预交金余额</td><td>¥${summary.final_balance || row.deposit_balance}</td></tr>
                <tr class="table-active"><td><strong>结算金额</strong></td><td class="fw-bold">¥${settlement.toFixed(2)}</td></tr>
              </table>
              <p class="small text-muted">正数 → 退还病人；负数 → 病人需补缴</p>`, [
                { text: "取消", class: "btn-secondary", dismiss: true },
                { text: "确认出院", class: "btn-warning", click: async () => {
                    try {
                        const result = await api.post("/discharge", { file_no: row.file_no });
                        m.hide();
                        showToast(`出院结算完成！结算金额：¥${result.settlement}`, "success");
                        load();
                    } catch (err) { showToast(err.message, "danger"); }
                }},
            ]);
            m.show();
        } catch (err) { showToast(err.message, "danger"); }
    }
    load();
}

// ============================================================
// 统计报表 — 5 个 Tab
// ============================================================

async function renderAdminStats() {
    renderAdminShell(`<div class="text-center py-5 text-muted">加载中...</div>`, "/admin/stats");

    const today = new Date().toISOString().slice(0, 10);
    const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);

    const tabs = [
        { id: "statsDoctors",   label: "医生工作量", icon: "👨‍⚕️" },
        { id: "statsDepts",     label: "科室统计",   icon: "🏢" },
        { id: "statsMedicines", label: "药品使用",   icon: "💊" },
        { id: "statsBeds",      label: "床位使用率", icon: "🛏️" },
        { id: "statsSchedules", label: "排班统计",   icon: "📅" },
    ];

    $("adminContent").innerHTML = `
      <h4>📈 统计报表</h4>
      <div class="page-card">
        <div class="row mb-3">
          <div class="col-md-3"><input type="date" class="form-control" id="statsDateFrom" value="${monthAgo}"></div>
          <div class="col-md-3"><input type="date" class="form-control" id="statsDateTo" value="${today}"></div>
          <div class="col-md-3"><button class="btn btn-primary" id="statsRefresh">🔍 查询</button></div>
        </div>
        <ul class="nav nav-tabs mb-3" id="statsTabs">
          ${tabs.map((t, i) => `<li class="nav-item">
            <a class="nav-link ${i === 0 ? "active" : ""}" data-tab="${t.id}" href="#">${t.icon} ${t.label}</a>
          </li>`).join("")}
        </ul>
        <div id="statsContent">加载中...</div>
      </div>`;

    let activeTab = "statsDoctors";

    async function loadTab(tabId) {
        activeTab = tabId;
        $("statsContent").innerHTML = `<div class="text-center py-4 text-muted">加载中...</div>`;
        const from = $("statsDateFrom").value || monthAgo;
        const to = $("statsDateTo").value || today;

        try {
            let data, cols;
            switch (tabId) {
                case "statsDoctors":
                    data = await api.get(`/stats/doctors?start_date=${from}&end_date=${to}`);
                    cols = [
                        { key: "name", label: "医生" }, { key: "dept_name", label: "科室" },
                        { key: "visit_count", label: "接诊数" }, { key: "prescription_count", label: "处方数" },
                    ];
                    break;
                case "statsDepts":
                    data = await api.get("/stats/departments");
                    cols = [
                        { key: "dept_name", label: "科室" },
                        { key: "total_registrations", label: "挂号数" },
                        { key: "total_prescriptions", label: "处方数" },
                        { key: "total_admissions", label: "住院数" },
                    ];
                    break;
                case "statsMedicines":
                    data = await api.get("/stats/medicines");
                    cols = [
                        { key: "med_name", label: "药品" }, { key: "specification", label: "规格" },
                        { key: "total_qty_used", label: "使用量" }, { key: "total_revenue", label: "收入(元)" },
                        { key: "prescription_count", label: "处方数" },
                    ];
                    break;
                case "statsBeds":
                    data = await api.get("/stats/beds");
                    cols = [
                        { key: "dept_name", label: "科室" }, { key: "ward_count", label: "病房数" },
                        { key: "total_beds", label: "总床位" }, { key: "occupied_beds", label: "占用" },
                        { key: "occupancy_rate", label: "使用率(%)" },
                    ];
                    break;
                case "statsSchedules":
                    data = await api.get(`/stats/schedules?start_date=${from}&end_date=${to}`);
                    cols = [
                        { key: "sched_date", label: "日期" }, { key: "doctor_name", label: "医生" },
                        { key: "sched_type", label: "类型" }, { key: "start_time", label: "开始" },
                        { key: "end_time", label: "结束" },
                    ];
                    break;
            }
            mountTable("statsContent", cols, data || []);
        } catch (err) {
            $("statsContent").innerHTML = `<div class="alert alert-danger">${escapeHtml(err.message)}</div>`;
        }
    }

    document.querySelectorAll("#statsTabs [data-tab]").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            document.querySelectorAll("#statsTabs .nav-link").forEach(l => l.classList.remove("active"));
            link.classList.add("active");
            loadTab(link.dataset.tab);
        });
    });

    $("statsRefresh").addEventListener("click", () => loadTab(activeTab));
    loadTab("statsDoctors");
}
