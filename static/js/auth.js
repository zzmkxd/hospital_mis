/**
 * 会话管理 — 登录后信息暂存 localStorage，登出时清除。
 *
 * 登录返回的数据结构（来自 POST /api/auth/login）：
 *   { account_id, ref_id, role, name }
 *
 * role 为 "管理员" / "医生" / "病人"，后续所有页面按 role 分流。
 */

const AUTH_KEY = "hospital_user";

function getUser() {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
}

function saveUser(user) {
    localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

function logout() {
    localStorage.removeItem(AUTH_KEY);
    location.hash = "#/login";
}

function isLoggedIn() {
    return getUser() !== null;
}
