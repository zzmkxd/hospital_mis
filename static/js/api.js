/**
 * API 通信层 — 封装所有 fetch 调用
 *
 * 每个函数返回 Promise<data>，调用方用 await + try/catch 处理。
 * 错误已经转为中文提示，前端直接展示即可。
 */

const BASE = "http://127.0.0.1:8000/api";

/**
 * 核心请求函数。所有 HTTP 方法最终都走这里。
 *
 * @param {string} method  - GET / POST / PUT / DELETE
 * @param {string} path    - 以 / 开头的路径，如 "/auth/login"
 * @param {object} [body]  - 请求体（GET 请求忽略）
 * @returns {Promise<any>} - 后端返回的 JSON 数据
 */
async function request(method, path, body = null) {
    const opts = {
        method,
        headers: { "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(BASE + path, opts);
    const data = await res.json();

    if (!res.ok) {
        // 后端抛出的 HTTPException detail 在 data.detail 中
        const msg = data.detail || `${method} ${path} 失败`;
        throw new Error(msg);
    }
    return data;
}

// ---- 便捷方法 ----
const api = {
    get:    (path)              => request("GET",    path),
    post:   (path, body)        => request("POST",   path, body),
    put:    (path, body)        => request("PUT",    path, body),
    delete: (path)              => request("DELETE",  path),
};
