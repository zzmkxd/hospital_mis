/**
 * 轻量 Hash 路由器
 *
 * 用法：
 *   router.on("/pattern", handler)  注册路由
 *   router.go("/pattern")           编程式跳转
 *   router.start()                  启动监听
 *
 * handler 是一个函数，接收解析后的路由参数对象。
 * 路由模式中的 :param 会变成 handler 收到的 params.param。
 */

class Router {
    constructor() {
        this._routes = [];
        this._notFound = null;
    }

    /** 注册路由。pattern 支持 :param 占位符 */
    on(pattern, handler) {
        const regex = this._patternToRegex(pattern);
        this._routes.push({ pattern, regex, handler });
        return this;
    }

    /** 未匹配时的 fallback */
    fallback(handler) {
        this._notFound = handler;
        return this;
    }

    /** 编程式导航 */
    go(path) {
        location.hash = path;
    }

    /** 启动：绑定 hashchange 事件并立即处理当前 hash */
    start() {
        window.addEventListener("hashchange", () => this._resolve());
        this._resolve();
    }

    // ---- private ----

    _patternToRegex(pattern) {
        const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const paramed = escaped.replace(/:(\w+)/g, "(?<$1>[^/]+)");
        return new RegExp(`^${paramed}$`);
    }

    _resolve() {
        const hash = location.hash.slice(1) || "/login";
        for (const route of this._routes) {
            const m = hash.match(route.regex);
            if (m) {
                route.handler(m.groups || {});
                return;
            }
        }
        if (this._notFound) this._notFound(hash);
    }
}

const router = new Router();
