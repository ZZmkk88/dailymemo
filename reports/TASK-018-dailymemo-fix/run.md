# TASK-018-dailymemo-fix 执行记录

开工：2026-10-21。本轮只改 P1-2（默认监听地址改回 127.0.0.1，环境变量 HOST）。P1-1 不改。

## 1. 读现稿

- app.py:8 已 `import os`。app.py:420 原为 `uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))`。
- README.md:27、README.md:36 原注释为「默认监听 8000 端口」。README.md:39 原为 `http://localhost:8000`。环境变量表原在 README.md:45-47，没有 HOST。
- 仓库内除 app.py:420 外没有其他 `0.0.0.0`。tests/ 未断言监听地址。
- 依赖不重装。复用上一轮已装好的虚拟环境：`E:\muse-bridge\work\TASK-008-dailymemo\venv`。

## 2. 修改

- app.py:420：`host="0.0.0.0"` 改为 `host=os.environ.get("HOST") or "127.0.0.1"`。
- README.md:27、README.md:36：注释改为「默认监听 127.0.0.1:8000」。
- README.md:39：浏览器地址改为 `http://127.0.0.1:8000`。
- README.md:46：环境变量表插入 `HOST`，默认 `127.0.0.1`，说明需要局域网访问时再设 `0.0.0.0`。

## 3. pytest

工作目录：`E:\muse-bridge\in\TASK-018-dailymemo-fix`。未重装依赖。缓存目录在 work 下。退出码 0。pytest 自报耗时 1.51s（没有另计墙钟）。

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-018-dailymemo-fix\pytest_cache
```

```
.................                                                        [100%]
17 passed, 3 warnings in 1.51s
```

警告 3 条，测试没有失败：`app.py:128` 的 `on_event` 弃用（fastapi 0.156.4 仍能跑）；同文件在 site-packages 里再报一次；`starlette.testclient` 提示要装 httpx2。这 3 条与上一轮相同，本次不改。

测试库由 `tests/test_app.py` 的 `tempfile.mkdtemp` 创建。该文件不许改，这次命令没有改 TEMP，所以这些库仍在系统临时目录。pytest 缓存写在 `E:\muse-bridge\work\TASK-018-dailymemo-fix\pytest_cache`。

Python：`E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe --version` → `Python 3.11.9`，退出码 0。

`git diff --name-only` 此时只有 `README.md` 和 `app.py`。

## 4. 监听地址探测（第一次，未完成）

命令：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\work\TASK-018-dailymemo-fix\probe_host.py
```

默认（未设 HOST）已经打出来，退出码 1。脚本在停进程之后再查端口，`Get-NetTCPConnection` 没有匹配时返回退出码 1，`check_output` 把这次查询当成失败，覆盖用例没跑到。

```
PYTHON 3.11.9
CASE default
HOST_ENV None
PID 29388
HTTP 200
TITLE True
LISTEN 127.0.0.1:18771 pid=4684
```

`probe-default.log` 里有：`INFO:     Uvicorn running on http://127.0.0.1:18771`，以及 `GET / HTTP/1.1" 200 OK`。

随后 `Stop-Process -Id 4684` 和 `Stop-Process -Id 29388` 没有留下进程（`Get-Process` 无输出，退出码 1）。脚本已改为空结果不再抛错，并会停掉日志里的 server pid。接着重跑。

## 5. 监听地址探测（第二次）

同一条命令重跑，退出码 0。数据库和日志在 `E:\muse-bridge\work\TASK-018-dailymemo-fix\`（`probe-default.db`、`probe-override.db` 及对应 log）。端口 18771。结束后 `AFTER_STOP none`。墙钟未另计。

```
PYTHON 3.11.9
CASE default
HOST_ENV None
PID 14664 SERVER_PID 27912
HTTP 200
TITLE True
LISTEN 127.0.0.1:18771 pid=27912
AFTER_STOP none
--- log default ---
INFO:     Uvicorn running on http://127.0.0.1:18771 (Press CTRL+C to quit)
--- end default ---
CASE override
HOST_ENV '0.0.0.0'
PID 26896 SERVER_PID 20228
HTTP 200
TITLE True
LISTEN 0.0.0.0:18771 pid=20228
AFTER_STOP none
--- log override ---
INFO:     Uvicorn running on http://0.0.0.0:18771 (Press CTRL+C to quit)
--- end override ---
```

## 6. git status

最后一条命令，退出码 0：

```
git status --porcelain
```

```
 M README.md
 M app.py
?? fix-report.md
```
