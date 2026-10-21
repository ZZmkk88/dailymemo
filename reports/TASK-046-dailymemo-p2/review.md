# dailymemo 第二轮审查（P2）

结论：没有 P0。上一轮 12 条 P2 里 11 条已在当前 HEAD `cff0aee` 落地。还开着的只有会话 token 明文入库（上一轮 P2-8）。本轮把它定为 P1：库文件被拷走后，过期前可以用原文 token 重放。只改 `app.py` 这一处。

基线（仓库根，exit 0）：`24 passed, 1 warning in 4.97s`。`tests/live_selftest.py`：`LIVE SELFTEST: ALL PASS`（2.12s）。警告只有 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`，来自 `fastapi/testclient.py:1`，没有 `on_event`。

## 上一轮 P2 核对

行号是本轮改代码之前的位置。

1. **已落地，不改。** `on_event("startup")` 已换成 lifespan。`app.py:41-44` 在启动时调用 `init_db()`，`app.py:56-58` 把 `lifespan=lifespan` 交给 FastAPI。pytest 警告里没有 `on_event is deprecated`。未登录访问 `/api/memos` 返回 401（探针），不是缺表 500。
2. **已落地，不改。** 修法是「文档写明上限，或做翻页」二选一。`README.md:17` 已写默认最多 200 条、上限 500。`app.py:49` 为 `MAX_LIST_LIMIT = 500`，`app.py:362` 默认 `limit=200`。界面 `static/index.html:281-285` 仍不传 `limit`、也没有翻页。再做翻页是新功能，本轮不加。
3. **已落地，不改。** `README.md:14` 已写「`#` 前不能紧邻词字符」，并举例 `a#b`、`_#tag`。`app.py:54` 仍是 `(?<![\w#])`。探针：`'_#under' => []`，`'a#b' => []`，`'## 标题' => []`。
4. **已落地，不改。** `static/index.html:251` 的字符类是 Lu/Ll/Lt/Lm/Lo/Nd/Nl/No 加下划线，没有 `\p{Pc}`。全码位探针：Python `\w` 与这组分类加下划线相比，多匹配 0、少匹配 0；Pc 只有 `U+005F`。Node 按页面源码求值后，`#‿x` 标签为 `[]`，`#²`、`#Ⅰ`、`#工作` 与 `app.extract_tags` 一致，渲染后的可见文本与原文相同（没有多一个 `#`）。
5. **已落地，不改。** `README.md:7` 已改成「后端接口均有自动化测试覆盖」，不再把今天/昨天分组说成已测试。日期分组只在 `static/index.html:268-274` 和 `:299-314`。`README.md:72` 写共 24 项，与本次 pytest `24 passed` 一致。
6. **已落地，不改。** `app.py:36-38`、`app.py:59-61` 默认关闭 `/docs`、`/redoc`、`/openapi.json`。探针三个都是 404。`tests/test_app.py:99-102` 覆盖了 `/docs` 和 `/openapi.json`。
7. **已落地，不改。** 密码比较已是 `hmac.compare_digest`：`app.py:198-200`、`app.py:237-239`。
8. **仍在，本轮修。** 登录把原文 token 写入 `sessions`。`app.py:202-206` 插入原文；`app.py:178-181` 按原文查询；`app.py:222` 按原文删除；`app.py:252-255` 按原文保留当前会话。探针：`stored_equals_raw_token True`。
9. **已落地，不改。** `static/index.html:47` 对 `.tname.notag` 取消 `::before`，`:131` 的「全部笔记」使用 `tname notag`。
10. **已落地，不改。** `static/index.html:300-308` 先画「📌 置顶」，置顶项不再进日期标题。`README.md:18` 写了单独的置顶区。
11. **已落地，不改。** `static/index.html:221` 在改密成功后执行 `$("pwBanner").classList.add("hidden")`。
12. **已落地，不改。** `README.md:20` 写「一条笔记最多 10000 字」，与 `app.py:48` 的 `MAX_CONTENT_LENGTH = 10000` 一致。

另外核对过、不单列进修复清单：新旧密码相同返回 400（探针 `same_password 400`，`app.py:241-242`）；默认只绑 `127.0.0.1`（`app.py:33`，探针 `resolve_host 127.0.0.1`）。

## 许可证与署名

未改 LICENSE / UPSTREAM。任务禁止抓取外网，所以上游 commit 与版权原文未核实，不能判定 `UPSTREAM.md` 的事实性声明是错的。

仓库内部：`LICENSE:3` 为 `Copyright (c) 2026 dailymemo contributors`。`UPSTREAM.md:7-8` 把上游记为 MIT，归因行 `Copyright (c) 2025 Memos`。两者不是同一份作品。

## 不修的观察

- 功能清单没写「退出」，代码有（`app.py:217`、`static/index.html:124`）。这是上一轮差异说明，不是 P2 行动项。登出接口有测试。不改 README。
- `NOTES.md:39-40` 仍把标签写成「非空白、非 `#`、非标点」。上一轮已说明 NOTES 不单列。不改。
- httpx / Starlette 弃用警告要换测试客户端或依赖版本。任务不许改已有依赖版本，也不许改 `tests/`。不改。

## 分级修复清单

### P0

无。pytest 24 项通过，live_selftest 全部通过，首页 200。

### P1

1. **P1-1**（上一轮 P2-8）会话 token 明文入库，拷走数据库即可重放。`app.py:178-181`、`app.py:202-206`、`app.py:222`、`app.py:252-255`。修法：用 `sha256` 十六进制摘要入库；校验、登出、改密吊销其他会话时，先对请求里的原文 token 做同一种哈希再查。登录响应仍返回原文。已有会话会失效，需要重新登录。不改表结构，不改测试。

### P2

无待改项。上面 1–7、9–12 已在当前树落地；第 2 条的翻页选项不采用。
