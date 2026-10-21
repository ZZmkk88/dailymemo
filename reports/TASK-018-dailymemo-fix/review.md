# dailymemo P1-2 修复验收

结论：P1-2 已修好。不设 `HOST` 时进程监听 `127.0.0.1`，设 `HOST=0.0.0.0` 时监听所有网卡。pytest 17 项通过。P1-1 保持原样。

## 改了什么

- `app.py:420`：`uvicorn.run` 的 host 从 `"0.0.0.0"` 改为 `os.environ.get("HOST") or "127.0.0.1"`。`os` 在 `app.py:8` 已导入。
- `README.md:27`、`README.md:36`：启动注释改为默认 `127.0.0.1:8000`。
- `README.md:39`：打开地址改为 `http://127.0.0.1:8000`。
- `README.md:46`：环境变量表增加 `HOST`，默认 `127.0.0.1`，局域网访问再设 `0.0.0.0`。

`git diff --name-only` 在写入 `fix-report.md` 之前只有 `README.md` 和 `app.py`。`tests/`、依赖文件、`LICENSE`、`UPSTREAM.md` 没有改。

## 验证

环境：Python 3.11.9。解释器 `E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe`。本轮没有执行 pip install。

全量测试（工作目录是仓库根，退出码 0）：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe -m pytest tests/ -q --tb=short -o cache_dir=E:\muse-bridge\work\TASK-018-dailymemo-fix\pytest_cache
```

```
.................                                                        [100%]
17 passed, 3 warnings in 1.51s
```

3 条警告都是原有的：`app.py:128` 的 `on_event` 弃用（site-packages 里再报一次），以及 Starlette 提示 TestClient 要换 httpx2。没有失败项。pytest 自报 1.51s。

真实监听（退出码 0，端口 18771，数据库在 `E:\muse-bridge\work\TASK-018-dailymemo-fix`）：

```
E:\muse-bridge\work\TASK-008-dailymemo\venv\Scripts\python.exe E:\muse-bridge\work\TASK-018-dailymemo-fix\probe_host.py
```

```
CASE default
HOST_ENV None
LISTEN 127.0.0.1:18771 pid=27912
HTTP 200
TITLE True
INFO:     Uvicorn running on http://127.0.0.1:18771 (Press CTRL+C to quit)
AFTER_STOP none
CASE override
HOST_ENV '0.0.0.0'
LISTEN 0.0.0.0:18771 pid=20228
HTTP 200
TITLE True
INFO:     Uvicorn running on http://0.0.0.0:18771 (Press CTRL+C to quit)
AFTER_STOP none
```

首页是 dailymemo 页面。两个进程都已退出，端口上没有 LISTEN。

## 未改

P1-1：`app.py:212-216` 改密仍不删除其他会话。`tests/test_app.py:28-31` 的模块级 token 在 `tests/test_app.py:68-74` 第二次改密之后还要给后面的用例用（下一处是 `tests/test_app.py:79`）。吊销其他会话会让这些用例 401，而 `tests/` 不能改。

P2 项本次不在修改范围内。

## 限制

`tests/live_selftest.py` 本轮没有重跑。绑定行为以上面的 uvicorn 探测为准。

`tests/test_app.py` 用 `tempfile.mkdtemp` 建库。测试文件不能改，本轮 pytest 也没有改 `TEMP`，这些库在系统临时目录。pytest 缓存和探测用的数据库、日志在 `E:\muse-bridge\work\TASK-018-dailymemo-fix`。

没有访问外网。没有测试因外网失败。
