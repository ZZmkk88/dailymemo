# TASK-008-dailymemo 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-008-dailymemo`。先读仓库再装环境、跑测试、起服务。

## 1. 环境

命令：

```
python --version
```

输出：

```
Python 3.11.9
```

满足 README 要求的 Python 3.10+。虚拟环境放在 `E:\muse-bridge\work\TASK-008-dailymemo\venv`（不写进仓库）。

命令：

```
python -m venv "E:\muse-bridge\work\TASK-008-dailymemo\venv"
```

输出：exit 0，无报错。

## 2. 安装依赖

命令（在仓库外的 venv 里装 `requirements-dev.txt`，其中 `-r requirements.txt`）：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-008-dailymemo\requirements-dev.txt
```

输出片段（exit 0）：

```
Collecting fastapi==0.156.4
Collecting uvicorn==0.54.0
Collecting httpx==0.28.1
Collecting pytest==9.1.1
Successfully installed ... fastapi-0.156.4 httpx-0.28.1 pytest-9.1.1 starlette-1.9.0 uvicorn-0.54.0 pydantic-2.14.1
```

版本与 requirements 锁定值一致，没有改版本号。

## 3. 全量测试（pytest）

临时目录 `TEMP`/`TMP` 指到 `E:\muse-bridge\work\TASK-008-dailymemo`，`PYTHONDONTWRITEBYTECODE=1`，pytest 缓存写到工作目录。由 `run_pytest.py` 启动。

命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-008-dailymemo\pytest_cache
```

工作目录：`E:\muse-bridge\in\TASK-008-dailymemo`

输出片段（exit 0）：

```
.................                                                        [100%]
app.py:128: DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
17 passed, 3 warnings in 1.64s
```

17 项与 README 宣称的条数一致。3 条是弃用警告，没有失败。

## 4. 真实流程自测（live_selftest，端口 8129）

命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\in\TASK-008-dailymemo\tests\live_selftest.py
```

工作目录：`E:\muse-bridge\in\TASK-008-dailymemo`。`TEMP`/`TMP` 指到工作目录。脚本自己起服务、跑完 `proc.terminate()` 关掉。

输出片段（exit 0）：

```
PASS 首页能打开且是 dailymemo 页面
PASS 登录成功 | {"token":"<已打码>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 发笔记：写周报要点，别忘了附…
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

登录响应里的 token 已打码，其余为原文。数据库在工作目录的 `dm-live-*` 临时目录，服务已退出。

## 5. 改密后旧会话、标签规则（修复前证据）

命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\work\TASK-008-dailymemo\check_session_and_tags.py
```

输出（exit 0）：

```
EXTRACT #a #b-c #中文 ['a', 'b-c', '中文']
EXTRACT #Привет #にほんご ['Привет', 'にほんご']
EXTRACT #work- ['work']
EXTRACT #-工作- ['工作']
EXTRACT ## 标题 a#b []
SECOND_SESSION_BEFORE 200 {'username': 'admin', 'must_change_password': True}
CHANGE 200 {"ok":true}
CURRENT_SESSION_AFTER 200
OTHER_SESSION_AFTER 200 {"username":"admin","must_change_password":false}
```

用 token A 改密后，另一个 token B 调用 `GET /api/me` 仍是 200。数据库：`E:\muse-bridge\work\TASK-008-dailymemo\session-check.db`。

## 6. 前端标签正则（Node v24.21.0）

命令：

```
node E:\muse-bridge\work\TASK-008-dailymemo\check_js_tag_re.js
```

输出（exit 0）：

```
"#工作" []
"#摘抄" []
"#work" ["work"]
"#work-" ["work-"]
"a#b" []
"## 标题" []
"#ok-tag" ["ok-tag"]
```

同一条规则在 Python 里能抽出「工作」，在前端正则里抽不出来。

## 7. 起服务（第一次，端口 8000，HTTP 没打到）

命令：`probe_server.py` 第一次。进程起来了，但脚本用 UTF-8 解码 `netstat` 失败（系统代码页是 GBK），在发 HTTP 请求之前就异常退出。

服务日志原文（本仓库 `app.py:128` 的弃用警告，说明这是 dailymemo 自己的进程）：

```
app.py:128: DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
INFO:     Started server process [3144]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

脚本对 Popen 调了 terminate。随后 `who_listens.py` 只看到 `127.0.0.1:...:8000 TIME_WAIT`，没有 LISTENING。

## 8. 起服务（第二次，端口 8000，打到了别的程序）

第二次探测时 8000 上已经是另一个本地程序。证据：

```
LISTENING
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       28796
GET / STATUS 200
BODY ... <title>书签管理器 · bookmark-manager</title> ...
GET /health STATUS 200
BODY {"ok":true,"app":"bookmark-manager"}
```

dailymemo 的首页标题是「dailymemo · 碎片笔记」，代码里也没有 `/health`。这次 200 不属于本仓库。清理逻辑误把监听 8000 的 PID 28796 停掉了。该进程不是本次 Popen（29388）。没有重启它，避免占用端口或写到别的任务目录。后面改用空闲端口，并且只结束命令行能对上本仓库 `app.py` 的进程。

被停掉的是 `E:\muse-bridge\in\TASK-012-bookmark-manager` 正在 8000 上跑的进程（日志里的应用是 bookmark-manager）。端口空出来之后，用它原来的启动脚本把服务拉了回来，并确认健康检查恢复，这个进程保持运行，不再动它：

```
E:\muse-bridge\work\TASK-012-bookmark-manager\.venv\Scripts\python.exe -u E:\muse-bridge\work\TASK-012-bookmark-manager\start_server.py default
```

输出：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

随后 `check_bm_health.py`：

```
STATUS 200
BODY {"ok":true,"app":"bookmark-manager"}
```

## 9. 起服务（第三次，PORT=18765，确认是 dailymemo 自己）

8000 让给 bookmark-manager。本次用 `PORT=18765`，数据库 `E:\muse-bridge\work\TASK-008-dailymemo\probe.db`。`host` 仍是 `app.py` 里写死的 `0.0.0.0`。

命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\work\TASK-008-dailymemo\probe_server.py
```

输出片段（exit 0）：

```
START 2026-10-21T09:06:31+00:00
PID 28880
PORT 18765
INFO:     Started server process [20020]
INFO:     Uvicorn running on http://0.0.0.0:18765 (Press CTRL+C to quit)
GET / STATUS 200
CONTENT-TYPE text/html; charset=utf-8
BODY ... <title>dailymemo · 碎片笔记</title> ...
LISTENING TCP    0.0.0.0:18765          0.0.0.0:0              LISTENING       20020
LOCAL_IP 192.168.31.86
CONNECT_LOCAL_IP open
GET /health STATUS 404
BODY {"detail":"Not Found"}
GET /api/health STATUS 404
BODY {"detail":"Not Found"}
GET /docs STATUS 200
GET /api/me STATUS 401
BODY {"detail":"未登录"}
STOPPED_PROC 1 2026-10-21T09:06:32+00:00
STILL_LISTENING none
```

首页 200，未登录接口 401，进程已退出，18765 不再 LISTENING。`/health` 与 `/api/health` 都是 404。从 09:06:31 到 09:06:32，约 1 秒。响应头里 `X-Frame-Options`、`Content-Security-Policy`、`X-Content-Type-Options` 均为 None。

## 10. 修改默认监听地址之后

只改了 `app.py` 与 `README.md`。改完立刻重跑 pytest，退出码 0：

```
17 passed, 3 warnings in 1.54s
```

再用未设置 `HOST` 的方式启动 `PORT=18765`（`probe_server.py`，2026-10-21T09:10:43Z 到 09:10:46Z，退出码 0）：

```
INFO:     Uvicorn running on http://127.0.0.1:18765
LISTENING TCP    127.0.0.1:18765        0.0.0.0:0              LISTENING       2784
CONNECT_LOCAL_IP closed TimeoutError
GET / STATUS 200
STILL_LISTENING none
```

live selftest 再跑一次，退出码 0，末行 `LIVE SELFTEST: ALL PASS`。登录 token 已打码。

收尾时再跑一次全量 pytest，退出码 0：

```
17 passed, 3 warnings in 1.62s
```

`git diff --stat`：`README.md | 5 +++--`，`app.py | 7 ++++++-`，共 2 个文件。没有 commit。

bookmark-manager 仍在 8000 上，复查 `GET /health` 为 `200 {"ok":true,"app":"bookmark-manager"}`。这个进程没有关。

