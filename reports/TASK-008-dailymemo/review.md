# dailymemo 验收

结论：仓库能在本机跑通。pytest 17 项通过，live selftest 全部通过，服务首页返回 200。没有 P0。P1 有 2 条：改密不使其他登录失效；默认监听 `0.0.0.0`，局域网能连上，而默认口令写在 README 里。前者受现有测试约束，修不动；后者本次修改。

## 本地跑通记录

环境：Python 3.11.9（`python --version`）。虚拟环境在 `E:\muse-bridge\work\TASK-008-dailymemo\venv`，没有写进仓库。依赖按 `requirements-dev.txt` 安装，退出码 0，装上的锁定版本是 fastapi 0.156.4、uvicorn 0.54.0、httpx 0.28.1、pytest 9.1.1。

全量测试命令（工作目录是仓库根，缓存和临时目录在 work 下）：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-008-dailymemo\pytest_cache
```

输出：

```
.................                                                        [100%]
app.py:128: DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
17 passed, 3 warnings in 1.64s
```

另外两条警告来自 FastAPI 自带的 TestClient：`Using httpx with starlette.testclient is deprecated; install httpx2 instead.` 测试没有失败。17 这个数字和 README 一致。

真实流程命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\in\TASK-008-dailymemo\tests\live_selftest.py
```

输出片段（退出码 0）：`PASS 首页能打开且是 dailymemo 页面`、`PASS 登录成功`（`must_change_password` 为 true）、4 条笔记、标签筛选 2 条、搜索 2 条、置顶、编辑、删除后剩 3 条，最后一行 `LIVE SELFTEST: ALL PASS`。脚本监听 8129，结束时自己关掉进程。登录响应里的 token 不贴出。

服务探测：本机 8000 上先有过一次 dailymemo 自己的启动日志 `Uvicorn running on http://0.0.0.0:8000`（`app.py:128` 的弃用警告能证明是这个仓库），但探测脚本在发 HTTP 之前就因 `netstat` 的 GBK 输出解码失败退出了，所以那一次没有首页响应。紧接着 8000 被另一个任务的 bookmark-manager 占用。误停过那个进程，已用它原来的 `start_server.py` 拉起，`GET /health` 恢复为 `200 {"ok":true,"app":"bookmark-manager"}`，并保持运行。

dailymemo 的有效 HTTP 记录改在 `PORT=18765`（同一份 `app.py`，host 仍是源码里的 `0.0.0.0`）。2026-10-21T09:06:31Z 到 09:06:32Z：

```
INFO:     Uvicorn running on http://0.0.0.0:18765
GET / STATUS 200
CONTENT-TYPE text/html; charset=utf-8
BODY ... <title>dailymemo · 碎片笔记</title> ...
LISTENING TCP    0.0.0.0:18765    LISTENING    20020
LOCAL_IP 192.168.31.86
CONNECT_LOCAL_IP open
GET /health STATUS 404
BODY {"detail":"Not Found"}
GET /api/health STATUS 404
BODY {"detail":"Not Found"}
GET /docs STATUS 200
GET /api/me STATUS 401
BODY {"detail":"未登录"}
STILL_LISTENING none
```

首页正常，未登录接口会 401，进程已退出。本仓库没有健康检查路由，`/health` 和 `/api/health` 都是 404。README 没声明这两条路径，所以 404 不记成缺陷，也不能写成健康检查通过。响应里没有 `X-Frame-Options`、`Content-Security-Policy`、`X-Content-Type-Options`。

没有测试因为访问外网失败。不存在「环境限制」项。

## README 与实际不符处

下面每一条都是 README 的说法和当前代码对不上。对得上的部分放在本节末尾，不重复展开。

1. 标签字符集、首尾连字符、正文点击筛选，三处同时对不上。
   - README.md:12 写：`#` 后跟中英文、数字、下划线或连字符，并且「点左侧标签栏或正文里的标签即可筛选」。
   - app.py:31 的正则是 `(?<![\w#])#([\w-]+)`。Python 3 的 `\w` 包含全部 Unicode 字母。实测 `extract_tags("#Привет #にほんご")` 得到 `['Привет', 'にほんご']`，超出「中英文」。
   - app.py:53 对匹配结果做 `strip("-")`。实测 `extract_tags("#work-")` 为 `['work']`，`extract_tags("#-工作-")` 为 `['工作']`。README 没有写首尾连字符会被剥掉。
   - static/index.html:245 用同一形状的 JS 正则。Node v24.21.0 实测 `"#工作"` 和 `"#摘抄"` 的匹配都是 `[]`，`"#work-"` 是 `["work-"]`。中文标签在正文里不会变成可点击元素；带尾部连字符的标签，正文点击会拿 `work-` 去筛选，后端存的却是 `work`。左侧标签栏走的是接口返回的文本，中文标签从侧栏点仍然可以筛选。

2. README.md:7 写功能「均已测试覆盖」。README.md:15 的「按日期分组（今天 / 昨天 / 具体日期）」只实现在 static/index.html:247-253。`tests/test_app.py` 没有任何分组断言；该文件第 123 行的「今天」只是一条笔记的正文。

3. README.md:67-70 的真实流程自测只写了 `.venv/bin/python tests/live_selftest.py`。同文件 Windows 小节（README.md:59-63）没有给出对应命令。本机没有 `.venv/bin/python`，改用 work 目录里的 `Scripts\python.exe` 才跑通。脚本本身可以在 Windows 上跑。

4. README.md:46 把默认数据库写成 `data/dailymemo.db`，读起来像相对当前工作目录。app.py:20-21 用的是 `Path(__file__).resolve().parent / "data" / "dailymemo.db"`，位置跟着 `app.py` 走，不跟着启动时的当前目录走。

5. README.md:27、README.md:36、README.md:39 只说默认端口 8000、用浏览器打开 localhost。app.py:420 把 host 写成 `"0.0.0.0"`。18765 上的实测是 `0.0.0.0` LISTENING，并且本机局域网地址 `192.168.31.86` 能连上。README 没写监听地址，也没写可以改。

已核对一致、不列入不符：Python 版本要求（本机 3.11.9）；默认端口 8000（app.py:420 的 `PORT` 默认值）；默认账号 admin / admin123（README.md:39、README.md:47，app.py:23-24）；Token 24 小时（README.md:9，app.py:22）；17 项自动化测试（本次输出 `17 passed`）；置顶优先、关键词搜索、按标签筛选、编辑后重算标签（live selftest 全过）；`## 标题` 和 `a#b` 不算标签（app.py:31 与本次 `extract_tags` 结果都是 `[]`）；首次登录只提示改密、不拦截后续接口（README.md:9 的「提示」，tests/live_selftest.py 在未改密时就发笔记并期望 200）。

## 许可证与署名核查

本仓库自己的声明是对齐的。

- LICENSE:1-3 是 MIT，版权行是 `Copyright (c) 2026 dailymemo contributors`。
- README.md:82 指向这份 LICENSE，并说明上游归因在 UPSTREAM.md。
- UPSTREAM.md:6-9 写上游为 https://github.com/usememos/memos ，commit `ccc1f82393ab50d2c8fea40865d8c2fbe05472a8`，许可证 MIT，署名 `Copyright (c) 2025 Memos`。UPSTREAM.md:16 称这一行是从上游 LICENSE 逐字复制的。NOTES.md:5-7 与这组事实相同。
- app.py 和 static/index.html 是 Python 加单页 HTML，仓库里看不到 Go、React 或 proto 源码，源码文件里也没有嵌上游 LICENSE 全文。这和 UPSTREAM.md:17-19「独立重写、未复制上游源码」在本仓库能看见的内容上一致。两套版权主体不打架：本仓库是 2026 dailymemo contributors，上游署名单独放在 UPSTREAM.md。MIT 并不要求一份未复制源码的独立实现再附上上游全文；现有 UPSTREAM 是额外署名。

未核实：任务不允许访问外网，没有核对 `source_commit` 是否存在，也没有核对上游 LICENSE 是否真是 `Copyright (c) 2025 Memos` 这一行。仓库内部文件彼此一致，没有确凿的写错，所以不改 LICENSE，也不改 UPSTREAM.md。

## 分级修复清单

P0：无。测试和服务都能起来。

P1：

1. 改密后，其他仍未过期的 token 继续有效。文件 app.py:212-216：更新了密码哈希并提交，没有删除该用户的其他 `sessions` 行。修复前实测：token A 改密成功后，token B 的 `GET /api/me` 仍是 200，且 `must_change_password` 已变成 false。修法：改密成功时删掉该用户除当前 token 以外的会话。本次修不动，原因见 fix-report.md：tests/test_app.py:28-31 的模块级 token 会在 tests/test_app.py:68-74 由另一个 token 第二次改密之后继续被后面的用例使用，吊销其他会话会让那些用例 401，而测试文件不能改。
2. 默认监听所有网卡，默认口令是公开的 admin / admin123。文件 app.py:420 `host="0.0.0.0"`；口令在 app.py:23-24 和 README.md:39。实测局域网地址可以连上这次启动的端口。修法：默认改为 `127.0.0.1`，增加环境变量 `HOST`，需要局域网访问时再显式设为 `0.0.0.0`，并在 README 的环境变量表写上这一行。

P2（本次不改）：

1. 正文里的中文标签点不了，首尾连字符前后端结果不同。static/index.html:245，app.py:53。修法：让前端按 Python 同一套 Unicode 规则识别并去掉首尾连字符，或把后端收窄成 README 写的字符集并让两边一致。
2. 启动事件用了已弃用的 `on_event`。app.py:128。当前 fastapi 0.156.4 仍能启动，只是警告。修法：改成 lifespan。
3. 搜索词里的 `%`、`_` 会按 LIKE 通配符解释。app.py:322-324。修法：先转义这两个字符，再拼进 `%...%`。
4. 密码比较用的是普通不等号，用户不存在时不算哈希。app.py:174、app.py:207。修法：用 `hmac.compare_digest`，未知用户也走一次假哈希。
5. `/docs` 未登录返回 200（本次探测）。app.py:33 使用 FastAPI 默认文档地址。修法：关掉 `docs_url` / `redoc_url` / `openapi_url`，或加上登录。
6. 响应没有点击劫持和内容类型方面的安全头（本次探测三个头都是 None）。修法：加中间件设置 `X-Frame-Options`、`X-Content-Type-Options` 和一份贴合本页的 CSP。
7. 过期会话只在查询时判断，不删除。app.py:94-98。修法：登录或启动时删掉 `expires_at` 已过的行。
8. README 三处文档：测试覆盖过称（README.md:7、README.md:15）、live selftest 没有 Windows 命令（README.md:70）、数据库路径语义（README.md:46）。修法：改对应句子，使它和代码一致。
9. 单条正文上限 10000 没写进 README。app.py:25、app.py:264-265。修法：在功能清单里补一句。
10. tests/live_selftest.py:52 把登录响应前 120 个字符打到标准输出，里面含完整 token。测试文件本次不许改。
