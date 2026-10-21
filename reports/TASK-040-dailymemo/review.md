# dailymemo 验收

结论：按 README 能在本机装好并跑通。pytest 21 项通过，live_selftest 全部 PASS，服务监听 `127.0.0.1:8000`，首页 200。`/health` 与 `/api/health` 返回 404（README 未承诺该路径）。无 P0，无 P1。未改仓库源码。

上游 commit 与上游 LICENSE 原文本次未联网，记「未核实」。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。README 要求 3.10+。工作目录 `E:\muse-bridge\in\TASK-040-dailymemo`。临时库与探测脚本在 `E:\muse-bridge\work\TASK-040-dailymemo`。

安装（均 exit 0）：

```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

装上的版本与文件一致：`fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`。

全量测试：

```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\run_pytest.py
```

```
21 passed, 3 warnings in 3.43s
```

警告原文要点：`app.py:138 DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.` 另有 Starlette `testclient.py:1`：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。收尾重跑是 `21 passed, 3 warnings in 3.55s`（同样三条警告）。

真实流程（脚本自带 8129 端口，跑完会关掉）：

```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\run_live.py
```

```
PASS 首页能打开且是 dailymemo 页面
PASS 登录成功 | {"token":"<已截断>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 时间线共 4 条且最新在前
PASS 按标签 #文档 筛选命中 2 条 | got 2
PASS 搜索「文档」命中 2 条
PASS 标签统计正确 | {'工作': 2, '文档': 2, '生活': 1}
PASS 置顶接口成功
PASS 置顶后 #生活 那条排第一
PASS 编辑生效且标签重算
PASS 删除成功
PASS 删后查不到
PASS 删后剩 3 条
LIVE SELFTEST: ALL PASS
```

起服务：cwd 为仓库，`PORT=8000`，`DAILYMEMO_DB_PATH` 指向工作目录，执行 `python app.py`。日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:61437 - "GET / HTTP/1.1" 200 OK
```

同一时段 netstat：

```
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       36844
```

HTTP 结果（`probe_http2.py`）：

```
GET / -> 200 text/html; charset=utf-8
GET /health -> 404 application/json '{"detail":"Not Found"}'
GET /api/health -> 404 application/json '{"detail":"Not Found"}'
GET /api/me -> 401 application/json '{"detail":"未登录"}'
HOME 127.0.0.1 -> 200 dailymemo=True
HOME localhost -> 200 dailymemo=True
LOGIN 200 admin True
```

首页响应头里有 `server: uvicorn` 和 `content-type`。没有 `X-Frame-Options`，也没有 `Content-Security-Policy`。

默认库路径（cwd 在工作目录、不设 `DAILYMEMO_DB_PATH`，只打印不建库）：

```
DB_PATH=E:\muse-bridge\in\TASK-040-dailymemo\data\dailymemo.db
resolve_host=127.0.0.1
```

关停：对本次启动的进程 `terminate` 之后，`check_port.py` 输出 `NO_LISTENER_ON_8000`。后来 8000 上出现的 PID 32492 命令行是 `E:\muse-bridge\work\TASK-044-freshfeeds\serve_once.py`，不是本仓库，未动。

没有因外网失败的测试。pip 使用了本地缓存，安装 exit 0。

## README 与实际不符处

下列「相符」先记一笔，避免把已经对上的条款再当成缺陷：默认端口 8000、`HOST` 默认 `127.0.0.1`、初始账号 `admin` / `admin123`、库路径不跟 cwd、Token 24 小时（`app.py:32`）、21 项测试这个数字、live_selftest 使用 8129、`#tag-` 记为 `tag`、`## 标题` 与 `a#b` 不算标签、中文标签可以识别。这些都有上面的命令输出或对应代码行。

1. `README.md:14` 写「`#` 前不能紧邻字母或数字」。`app.py:41` 的正则是 `(?<![\w#])`。实测 `_#under` → `[]`。下划线同样会挡住标签。`app.py:41`。
2. `README.md:12-13` 写标签字符是字母、数字、下划线或连字符。`app.py:41` 的 `\w` 还会吃进 Unicode 其它数字。实测 `#x½y` → `['x½y']`，`#x②y` → `['x②y']`。`app.py:41`。
3. `README.md:16` 写按关键词搜正文。`app.py:343-344` 把关键词原样放进 `LIKE '%...%'`，没有转义 `%` 和 `_`。实测 `q=100%` 同时命中「编号1000无百分号」和「百分号 100% 完成」；`q=%` 命中当时全部 4 条；`q=甲_` 命中「甲乙」。`app.py:343-344`。
4. `README.md:10` 写列表按时间倒序。`app.py:347` 实际是 `ORDER BY m.pinned DESC, m.created_at DESC, m.id DESC`。同文件 `README.md:17` 写了置顶排在最前。第 10 行单独看缺了置顶。
5. `README.md:7-18` 的功能清单没有正文长度上限。`app.py:35` 定义 `MAX_CONTENT_LENGTH = 10000`，`app.py:284-285` 超长返回 400。
6. README 没有写新密码长度。`app.py:219-220` 要求至少 6 位。页面 `static/index.html:141` 有这句提示，README 没有。
7. README 没有写同一条笔记里标签按大小写合并。`app.py:65-68` 用 `lower()` 去重。实测 `#Tag #tag` → `['Tag']`。

## 许可证与署名核查

仓库内部是对齐的。

- `LICENSE:1-3`：MIT，`Copyright (c) 2026 dailymemo contributors`。
- `README.md:90-92`：本项目 MIT，上游也是 MIT，版权归因指向 `UPSTREAM.md`。
- `UPSTREAM.md:5-8`：`source_url` 为 `https://github.com/usememos/memos`，`source_commit` 为 `ccc1f82393ab50d2c8fea40865d8c2fbe05472a8`，`license` 为 MIT，`attribution` 为 `Copyright (c) 2025 Memos`。
- `UPSTREAM.md:17-19`：声明 Python 代码是独立重写，没有复制上游源码。仓库里是 `app.py` 与一份静态页，没有上游的 Go / React / proto 树。
- `NOTES.md:5-7` 复述了同一组上游 URL、commit、MIT 和 `Copyright (c) 2025 Memos`。

本仓库版权人（2026 dailymemo contributors）和上游署名（2025 Memos）写的是两件事，文件之间没有互相打架。

`UPSTREAM.md:12-16` 称 commit 是 2026-10-21 通过 GitHub 接口实查的默认分支 HEAD，版权行逐字来自上游 LICENSE。按任务要求未访问外网，这两句外部事实「未核实」。因此没有改 `LICENSE` 和 `UPSTREAM.md`。

## 分级修复清单

P0 是跑不起来或阻断验收。P1 是安全、数据损坏、越权。其余是 P2。本次只允许修 P0/P1，下面 P2 不改代码。

### P0

无。安装、21 项测试、live_selftest、`127.0.0.1:8000` 首页 200 都已跑过。

### P1

无。核对过、未构成缺陷的点：

- 监听地址是 `127.0.0.1:8000`（netstat 上文）。默认口令只在本机回环。
- 未登录 `GET /api/me` 为 401。
- 另一个用户的笔记：get/put/delete 都是 404，列表里没有对方正文；对方自己仍能 200 读到。过期 token 为 401。
- 删除笔记后 `memo_tags` 残留条数为 0（外键级联生效）。
- 查询串 `' OR 1=1 --` 返回 0 条，SQL 用的是占位符（`app.py:343-344`）。通配符问题放在 P2-3。
- 正文里的 `<` 会先转成 `&lt;`（Node 实测 `<#lt` 的输出以 `&lt;` 开头）。

### P2

1. `static/index.html:256` 渲染标签时在已经含 `#` 的 `<span>` 前又拼了一个 `#`。`今天 #工作` 的 HTML 是 `今天 #<span ...>#工作</span>`，页面上会看成 `##工作`。修法：去掉这个多余前缀，只保留 span 里的 `#` 加标签名。
2. `static/index.html:248-249` 把整个 Unicode `\p{Pc}` 算进标签；`app.py:41` 的 Python `\w` 并不包含 `‿`。`#x‿y` 后端是 `['x']`，前端 `data-tag` 是 `x‿y`。修法：前端字符类只保留与 Python `\w` 相同的部分，连接符里只留下划线。
3. `app.py:343-344` 搜索未转义 LIKE 通配符，证据见上文 `q=100%` / `q=%` / `q=甲_`。修法：把 `%`、`_`、`\` 转义后，用 `ESCAPE '\'` 做字面匹配。
4. `app.py:138` `@app.on_event("startup")` 在当前 FastAPI 0.156.4 上会告警，服务仍能起来。修法：改成 lifespan，在 lifespan 里调用 `init_db()`。
5. `app.py:43` `FastAPI()` 使用默认文档路由。实测 `/docs`、`/redoc`、`/openapi.json` 均为 200，且不需要登录。修法：关掉这三个路由，或加上与笔记接口相同的登录校验。
6. `app.py:432-434` 首页 `FileResponse` 没有点击劫持相关头。实测响应头只有 `server` 和 `content-type`。修法：加上 `X-Frame-Options: DENY`（或等价的 CSP `frame-ancestors`）。
7. `app.py:184` 密码哈希用 `!=` 比较。修法：改成 `hmac.compare_digest`。
8. `app.py:54` 时间戳只到秒。同一秒内编辑时 `updated_at` 可以等于 `created_at`，`static/index.html:305` 就不显示「已编辑」。修法：时间戳保留到微秒。
9. `static/index.html:46` 的 `.tname::before` 会给「全部笔记」也加上 `# `；`static/index.html:130` 的 `allCount` 在脚本里没有赋值。修法：「全部笔记」不要用 `tname` 这套前缀，需要计数时再写入 `allCount`。
10. 文档与实现对齐（条目见上一节）：`README.md:10`、`README.md:12-14`、`README.md:16` 按 `app.py:41`、`app.py:65-68`、`app.py:347`、`app.py:343-344` 改写；补上 `app.py:35` 的 10000 字上限和 `app.py:219` 的 6 位新密码。修法：改 README 表述，使它和现有代码一致。
