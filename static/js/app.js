/**
 * 应用入口 — 路由注册 + 登录页渲染 + 路由守卫
 */

// ============================================================
// 通用：带导航栏的页面壳
// ============================================================

/** 渲染顶部导航栏，管理员带 sidebar 切换按钮 */
function renderNavbar(user) {
    const roleBadge = { "管理员": "primary", "医生": "success", "病人": "info" }[user.role] || "secondary";
    return `
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container-fluid">
          <a class="navbar-brand" href="#/${user.role === "管理员" ? "admin" : user.role === "医生" ? "doctor" : "patient"}">
            🏥 医院管理信息系统
          </a>
          <div class="d-flex align-items-center">
            <span class="badge bg-${roleBadge} me-2">${user.role}</span>
            <span class="text-light me-3">${escapeHtml(user.name)}</span>
            <button class="btn btn-outline-light btn-sm" onclick="handleLogout()">退出</button>
          </div>
        </div>
      </nav>`;
}

function handleLogout() {
    logout();
    router.go("/login");
}

// ============================================================
// 路由守卫 — 未登录自动跳转登录页
// ============================================================

function requireAuth(handler) {
    return (params) => {
        if (!isLoggedIn()) {
            router.go("/login");
            return;
        }
        handler(params);
    };
}

// ============================================================
// 登录页
// ============================================================

function renderLoginPage() {
    // 已登录则跳转
    if (isLoggedIn()) {
        redirectByRole();
        return;
    }

    $("appMain").innerHTML = `
      <div class="login-page d-flex align-items-center justify-content-center">
        <div class="container">
          <div class="row justify-content-center">
            <div class="col-md-5 col-lg-4">
              <div class="card p-4">
                <h3 class="text-center mb-3">🏥 医院管理信息系统</h3>
                <p class="text-center text-muted mb-4">数据库课程设计 · 请登录</p>

                <!-- 角色选择卡片 -->
                <div class="row g-2 mb-3" id="roleCards">
                  <div class="col-4">
                    <div class="role-card" data-role="管理员">
                      <span class="role-icon">🔧</span>管理员
                    </div>
                  </div>
                  <div class="col-4">
                    <div class="role-card" data-role="医生">
                      <span class="role-icon">👨‍⚕️</span>医生
                    </div>
                  </div>
                  <div class="col-4">
                    <div class="role-card" data-role="病人">
                      <span class="role-icon">👤</span>病人
                    </div>
                  </div>
                </div>

                <!-- 登录表单 -->
                <div class="mb-3">
                  <label class="form-label" id="refLabel">账号</label>
                  <input type="text" class="form-control" id="refIdInput" placeholder="请输入账号">
                </div>
                <div class="mb-3">
                  <label class="form-label">密码</label>
                  <input type="password" class="form-control" id="passwordInput" placeholder="请输入密码">
                </div>
                <div class="mb-3 text-danger small d-none" id="loginError"></div>
                <button class="btn btn-primary w-100" id="loginBtn" disabled>
                  请先选择角色
                </button>

                <!-- 提示 -->
                <div class="mt-3 small text-muted">
                  <details>
                    <summary class="cursor-pointer">测试账号（点击展开）</summary>
                    <ul class="mt-2 mb-0">
                      <li>管理员：999 / admin123</li>
                      <li>医生：1 / 123456（或 2, 3, 4, 5）</li>
                      <li>病人：1 / 123456（或 2, 3）</li>
                    </ul>
                  </details>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>`;

    // ---- 交互逻辑 ----
    let selectedRole = null;

    // 角色卡片点击
    document.querySelectorAll(".role-card").forEach(card => {
        card.addEventListener("click", () => {
            document.querySelectorAll(".role-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            selectedRole = card.dataset.role;

            // 更新标签文字
            const labels = { "管理员": "管理员账号", "医生": "医生ID", "病人": "病案号" };
            $("refLabel").textContent = labels[selectedRole];
            $("refIdInput").placeholder = {
                "管理员": "请输入管理员账号",
                "医生": "请输入医生ID",
                "病人": "请输入病案号"
            }[selectedRole];

            $("loginBtn").disabled = false;
            $("loginBtn").textContent = `以${selectedRole}身份登录`;
        });
    });

    // 回车登录
    $("passwordInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") doLogin();
    });

    // 登录按钮
    $("loginBtn").addEventListener("click", doLogin);

    async function doLogin() {
        if (!selectedRole) return;
        const refId = $("refIdInput").value.trim();
        const password = $("passwordInput").value;
        if (!refId || !password) {
            showToast("请填写完整信息", "warning");
            return;
        }

        $("loginBtn").disabled = true;
        $("loginBtn").textContent = "登录中...";
        $("loginError").classList.add("d-none");

        try {
            const user = await api.post("/auth/login", {
                ref_id: parseInt(refId),
                password: password,
                role: selectedRole
            });
            saveUser(user);
            showToast(`欢迎，${user.name}！`, "success");
            redirectByRole();
        } catch (err) {
            $("loginError").textContent = err.message;
            $("loginError").classList.remove("d-none");
            $("loginBtn").disabled = false;
            $("loginBtn").textContent = `以${selectedRole}身份登录`;
        }
    }
}

function redirectByRole() {
    const user = getUser();
    if (!user) return;
    const map = { "管理员": "/admin", "医生": "/doctor", "病人": "/patient" };
    router.go(map[user.role] || "/login");
}

// ============================================================
// 404 页面
// ============================================================

function renderNotFound() {
    $("appMain").innerHTML = `
      <div class="container text-center py-5">
        <h1 class="display-1 text-muted">404</h1>
        <p class="lead">页面不存在</p>
        <a href="#/login" class="btn btn-primary">返回首页</a>
      </div>`;
}

// ============================================================
// 启动
// ============================================================

router
    .on("/login", renderLoginPage)

    // 管理员
    .on("/admin",           requireAuth(renderAdminDashboard))
    .on("/admin/departments", requireAuth(renderAdminDepartments))
    .on("/admin/doctors",    requireAuth(renderAdminDoctors))
    .on("/admin/medicines",  requireAuth(renderAdminMedicines))
    .on("/admin/schedules",  requireAuth(renderAdminSchedules))
    .on("/admin/admission",  requireAuth(renderAdminAdmission))
    .on("/admin/discharge",  requireAuth(renderAdminDischarge))
    .on("/admin/stats",      requireAuth(renderAdminStats))

    // 医生
    .on("/doctor",          requireAuth(renderDoctorDashboard))
    .on("/doctor/consult",  requireAuth(renderDoctorConsult))
    .on("/doctor/rounds",   requireAuth(renderDoctorRounds))

    // 病人
    .on("/patient",          requireAuth(renderPatientDashboard))
    .on("/patient/register", requireAuth(renderPatientRegister))
    .on("/patient/payment",  requireAuth(renderPatientPayment))

    .fallback(renderNotFound)
    .start();
