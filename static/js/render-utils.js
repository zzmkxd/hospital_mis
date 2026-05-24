/**
 * DOM 渲染工具集 — 创建表格、模态框、Toast 等可复用 UI 组件。
 *
 * 所有函数直接操作 DOM 或返回 HTML 字符串。
 * 约定：表格数据统一用 array<object>，列的 key 对应对象的属性名。
 */

// ---- Toast 提示 ----
// 使用 Bootstrap 5 Toast，需要在页面放置 <div id="toastContainer"> 容器

function showToast(message, type = "danger") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const icons = { success: "✅", danger: "❌", warning: "⚠️", info: "ℹ️" };
    const toast = document.createElement("div");
    toast.className = `toast align-items-center border-0 bg-${type} bg-opacity-10 text-${type} mb-2`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${icons[type] || ""} ${escapeHtml(message)}</div>
        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>`;
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

// ---- 表格 ----
/**
 * 根据数据和列定义生成 <table> 字符串。
 *
 * @param {array} columns  - [{key: "col_name", label: "列标题"}, ...]
 * @param {array} rows     - 数据数组，每项是 object
 * @param {array} [actions]- 可选，操作按钮 [{label: "编辑", class: "btn-sm btn-primary", click: fn(row)}, ...]
 * @returns {string} HTML
 */
function renderTable(columns, rows, actions = []) {
    if (!rows.length) {
        return `<div class="text-center text-muted py-4">暂无数据</div>`;
    }

    let html = '<table class="table table-hover align-middle"><thead><tr>';
    html += columns.map(c => `<th>${c.label}</th>`).join("");
    if (actions.length) html += `<th style="width:${actions.length * 80}px">操作</th>`;
    html += "</tr></thead><tbody>";

    rows.forEach((row, idx) => {
        html += "<tr>";
        html += columns.map(c => `<td>${escapeHtml(row[c.key] ?? "")}</td>`).join("");
        if (actions.length) {
            html += "<td>";
            actions.forEach(a => {
                html += `<button class="btn ${a.class || 'btn-outline-secondary'} btn-sm me-1"
                  data-row='${escapeHtml(JSON.stringify(row))}'
                  data-action="${a.label}">${a.label}</button>`;
            });
            html += "</td>";
        }
        html += "</tr>";
    });

    html += "</tbody></table>";
    return html;
}

/**
 * 将表格 HTML 插入容器并绑定操作按钮事件。
 */
function mountTable(containerId, columns, rows, actions = []) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = renderTable(columns, rows, actions);

    // 绑定操作按钮
    el.querySelectorAll("[data-action]").forEach(btn => {
        btn.addEventListener("click", () => {
            const row = JSON.parse(btn.dataset.row);
            const action = actions.find(a => a.label === btn.dataset.action);
            if (action && action.click) action.click(row);
        });
    });
}

// ---- 模态框 ----
let _modalIdCounter = 0;

/**
 * 动态创建 Bootstrap Modal 并插入页面。
 *
 * @param {string} title   - 标题
 * @param {string} bodyHtml- 内容 HTML
 * @param {array}  [footerButtons] - [{text, class, dismiss, click}]
 * @returns {bootstrap.Modal} 可手动 .show() / .hide()
 */
function createModal(title, bodyHtml, footerButtons = []) {
    const id = `modal_${++_modalIdCounter}`;
    const footerHtml = footerButtons.length
        ? footerButtons.map(b =>
            `<button type="button" class="btn ${b.class || 'btn-secondary'}"
              ${b.dismiss ? 'data-bs-dismiss="modal"' : ''}
              ${b.click ? `id="${id}_btn_${footerButtons.indexOf(b)}"` : ''}>
              ${b.text}</button>`
          ).join("")
        : "";

    const html = `
      <div class="modal fade" id="${id}" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">${title}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">${bodyHtml}</div>
            ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ""}
          </div>
        </div>
      </div>`;

    document.body.insertAdjacentHTML("beforeend", html);
    const modalEl = document.getElementById(id);
    const modal = new bootstrap.Modal(modalEl);

    // 绑定 footer 按钮事件
    footerButtons.forEach((b, i) => {
        if (b.click) {
            document.getElementById(`${id}_btn_${i}`).addEventListener("click", b.click);
        }
    });

    // 关闭后自动移除 DOM
    modalEl.addEventListener("hidden.bs.modal", () => modalEl.remove());

    return modal;
}

// ---- 工具 ----
function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function $(id) {
    return document.getElementById(id);
}
