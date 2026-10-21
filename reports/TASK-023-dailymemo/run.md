# TASK-023-dailymemo 执行记录

- 开始时间：2026-10-21
- 工作目录：E:\muse-bridge\in\TASK-023-dailymemo
- 临时目录：E:\muse-bridge\work\TASK-023-dailymemo
- 状态：开工。先读仓库与 README，再装环境、跑测试、起服务。

## 1. 环境

- 系统 Python：`python --version` → `Python 3.11.9`（满足 README「3.10+」）。
- 虚拟环境放在工作目录，避免写进仓库：`E:\muse-bridge\work\TASK-023-dailymemo\.venv`。
- `git status --porcelain`（仓库根）输出为空，开工时工作区干净。`.gitignore` 已忽略 `.venv/`、`data/`、`*.db`。

### 安装依赖

命令：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-023-dailymemo\requirements-dev.txt
```

结果：exit 0。装上 fastapi==0.156.4、uvicorn==0.54.0、httpx==0.28.1、pytest==9.1.1，以及传递依赖 starlette==1.9.0、pydantic==2.14.1。末行：

```
Successfully installed annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.19 click-8.5.0 colorama-0.4.6 fastapi-0.156.4 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.1 packaging-26.3 pluggy-1.7.0 pydantic-2.14.1 pydantic-core-2.50.1 pygments-2.21.0 pytest-9.1.1 starlette-1.9.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.54.0
```

## 2. pytest

工作目录即仓库根。命令：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests -q
```

结果：exit 0。`21 passed, 3 warnings in 3.00s`。

警告原文（摘要）：

- `app.py:138 DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.`
- `fastapi/applications.py:4723` 同样的 `on_event` DeprecationWarning。
- `fastapi/testclient.py:1 StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

说明：这次 pytest 由 `tests/test_app.py` 自己调用 `tempfile.mkdtemp`，当时未改 TEMP，数据库落在系统临时目录。事后查到两个目录：`C:\Users\xzm\AppData\Local\Temp\dm-test-g3pvnmxg`、`C:\Users\xzm\AppData\Local\Temp\dm-test-m3_qtd4y`。后续 Python 进程通过 venv 的 `sitecustomize.py` 把 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-023-dailymemo`。

## 3. live_selftest

命令：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\in\TASK-023-dailymemo\tests\live_selftest.py
```

结果：exit 0。末行 `LIVE SELFTEST: ALL PASS`。临时目录：`E:\muse-bridge\work\TASK-023-dailymemo\dm-live-tby2x9rr`。

输出片段（登录 token 属于已退出的临时进程，此处省略中段）：

```
PASS 首页能打开且是 dailymemo 页面
PASS 登录成功 | {"token":"owIt…ncgo","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 时间线共 4 条且最新在前
PASS 按标签 #文档 筛选命中 2 条 | got 2
PASS 搜索「文档」命中 2 条
PASS 标签统计正确 | {'工作': 2, '文档': 2, '生活': 1}
PASS 置顶后 #生活 那条排第一
PASS 删后剩 3 条
LIVE SELFTEST: ALL PASS
```

## 4. 行为探针（不改仓库）

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\probe_api.py
```

exit 0。关键行：

```
'_#under' => []
'#tag-' => ['tag']
'#①num' => ['①num']
'#½half' => ['½half']
'#‿tie' => []
GET / 200 True
/health 404 application/json
unauth memos 401 {"detail":"未登录"}
login 200 {'username': 'admin', 'must_change_password': True}
sqli q 200 []
search percent count 2
search underscore count 2 ['beta other', 'alpha secret']
same password 200 {"ok":true}
me after same pw 200 {'username': 'admin', 'must_change_password': False}
```

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\probe_word.py
```

exit 0。关键行：`Pc matched by \\w: 1 ['U+005F']`，`Pc not matched: 9`。`Ⅳ`（Nl）、`①`/`½`（No）算词字符；`‿`（Pc）不算。

```
node E:\muse-bridge\work\TASK-023-dailymemo\probe_tags.js
```

exit 0。`REGEX_OK`。`#工作` 的 HTML 为 `#<span class="tag" data-tag="工作">#工作</span>`（可见文本是 `##工作`）。`#‿x` 被前端当成标签。`<script>` 被转成 `&lt;script&gt;`。

## 5. 按 README 起服务（端口 8000）

命令：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\smoke_server.py
```

数据库：`E:\muse-bridge\work\TASK-023-dailymemo\smoke.db`。exit 0。服务日志：

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:51877 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:51877 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:51877 - "GET /api/me HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:51877 - "POST /api/login HTTP/1.1" 200 OK
```

探针打印：`GET / 200 len 16040 has_dailymemo True`；`/health`、`/api/health`、`/healthz` 均为 `404 {"detail":"Not Found"}`；`/docs` 与 `/openapi.json` 为 200；`LOGIN 200` 且 `must_change_password:true`。

脚本在请求结束后 `proc.terminate()`。子进程 `EXIT 1` 是被终止的返回码，不是启动失败（终止前日志已有 startup complete 和 200）。进程已退出，没有残留监听。

## 6. 修复后的验证

P1-1 搜索用例 exit 0：`3 passed, 3 warnings in 0.83s`。`verify_p1_1.py` exit 0，末行 `P1-1 VERIFY PASS`。`%` 只命中 `score 100%`，`_` 只命中 `file_name`。

P1-2 三条用例一次跑 exit 1：`1 failed, 2 passed, 3 warnings in 1.70s`。失败的是 `test_login_ok_and_must_change`，因为和改密用例共享数据库且被我排到后面。单独重跑该用例 exit 0：`1 passed, 3 warnings in 0.66s`。`verify_p1_2.py` exit 0，末行 `P1-2 VERIFY PASS`。相同密码返回 `400 {"detail":"新密码不能与旧密码相同"}`，`must_change_password` 仍为 true。

P1-3：`node E:\muse-bridge\work\TASK-023-dailymemo\verify_p1_3.js` exit 0，末行 `P1-3 VERIFY PASS`。`#工作` 的可见文本是 `#工作`。

全量 pytest exit 0：`21 passed, 3 warnings in 2.76s`。`live_selftest.py` exit 0，末行 `LIVE SELFTEST: ALL PASS`。

`git status --porcelain`：

```
 M app.py
 M static/index.html
```

收尾再执行一次，输出与上面相同。

补：`cleanup_temp.py` 删掉了首次 pytest 留在系统临时目录的 `dm-test-g3pvnmxg` 和 `dm-test-m3_qtd4y`。exit 0，两行均为 `removed`。



