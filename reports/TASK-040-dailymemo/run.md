# TASK-040-dailymemo 执行记录

开工时间：2026-10-21
角色：本地验收（Grok Build）
仓库：E:\muse-bridge\in\TASK-040-dailymemo

## 0. 环境探测

命令：`python --version`
输出：
```
Python 3.11.9
```
README 要求 Python 3.10+。本机 3.11.9 满足。

命令：`git status --porcelain`
输出：（空，工作区干净）

命令：`git rev-parse --show-toplevel`
输出：`E:/muse-bridge/in/TASK-040-dailymemo`

## 1. 安装依赖

按 README Windows 步骤，在仓库内创建 `.venv`（.gitignore 已忽略 `.venv/`）。
临时目录：`E:\muse-bridge\work\TASK-040-dailymemo`。

命令（工作目录 `E:\muse-bridge\in\TASK-040-dailymemo`）：
```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```
结果：均 exit 0。
- `fastapi==0.156.4`、`uvicorn==0.54.0` 安装成功
- `httpx==0.28.1`、`pytest==9.1.1` 安装成功
- pip 提示可升级 24.0 -> 26.2.2（未升级，避免改环境）

## 2. 全量测试

命令：
```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\run_pytest.py
```
（脚本把 TEMP/TMP 指到 `E:\muse-bridge\work\TASK-040-dailymemo`，再执行 `pytest tests/ -q`。）

输出末尾：
```
21 passed, 3 warnings in 3.43s
```
警告原文（摘要）：
- `app.py:138` `DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.`
- `fastapi\applications.py:4723` 同一条 on_event 弃用警告
- `fastapi\testclient.py:1` `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

21 项全部通过，无失败。

## 3. 真实流程自测 live_selftest

命令：
```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\run_live.py
```
（同样把临时库指到工作目录，再跑 `tests/live_selftest.py`，脚本自己在 8129 端口起服务并关掉。）

输出（登录响应里的 token 已截断，临时库已随进程销毁）：
```
PASS 首页能打开且是 dailymemo 页面
PASS 登录成功 | {"token":"<已截断>","username":"admin","must_change_password":true}
PASS 首次登录提示改密
PASS 发笔记：写周报要点，别忘了附… 
PASS 发笔记：读到一段接口文档，讲…
PASS 发笔记：下班买牛奶和鸡蛋 #…
PASS 发笔记：又一篇文档笔记，讲缓…
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
exit 0。

## 4. 按 README 起服务（端口 / 首页 / 健康检查）

临时库都放在 `E:\muse-bridge\work\TASK-040-dailymemo`，没有在仓库里生成 `data\`。

### 4.1 默认路径与监听地址（只 import，不建库）

命令：`probe_http.py` 里，cwd=`E:\muse-bridge\work\TASK-040-dailymemo`，未设置 `DAILYMEMO_DB_PATH`：

```
cwd=E:\muse-bridge\work\TASK-040-dailymemo
DB_PATH=E:\muse-bridge\in\TASK-040-dailymemo\data\dailymemo.db
resolve_host=127.0.0.1
```

与 README 一致：默认库是 `app.py` 所在目录下的绝对路径，不跟启动目录。随后确认仓库里不存在 `data\` 目录（`repo_data_exists False`）。

### 4.2 第一次真正听端口

命令要点：cwd 为仓库，`PORT=8000`，`DAILYMEMO_DB_PATH` 指向工作目录，`python app.py`。

服务日志：

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:61437 - "GET / HTTP/1.1" 200 OK
```

同一次启动还有 `app.py:138` 的 `DeprecationWarning: on_event is deprecated`。

这次探测脚本在 netstat 解码处自己抛错（`AttributeError`），随后 `proc.terminate()`。这是探测脚本的问题，服务本身已经 200。

### 4.3 首页、健康检查、登录

命令：

```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\probe_http2.py
```

输出片段：

```
GET / -> 200 text/html; charset=utf-8 '<!DOCTYPE html> ... <titl'
GET /health -> 404 application/json '{"detail":"Not Found"}'
GET /api/health -> 404 application/json '{"detail":"Not Found"}'
GET /docs -> 200 text/html; charset=utf-8
GET /redoc -> 200 text/html; charset=utf-8
GET /openapi.json -> 200 application/json
GET /api/me -> 401 application/json '{"detail":"未登录"}'
HOME 127.0.0.1 -> 200 dailymemo=True
HOME localhost -> 200 dailymemo=True
ROOT_SEC_HEADERS {'server': 'uvicorn', 'content-type': 'text/html; charset=utf-8'}
LOGIN 200 admin True
CREATE 200 ['探针'] 1
DELETE 200
ORPHAN_TAGS_FOR_DELETED 0
SEARCH_SQLISH 200 0
```

`SEARCH_SQLISH` 的查询串是 `' OR 1=1 --`，返回 0 条，没有 SQL 报错。

跨用户（同脚本前半段，独立库 `probe-iso.db`）：

```
other_create 200 1
admin_get_other 404
admin_put_other 404
admin_del_other 404
admin_list_has_secret False
other_still_there 200
expired_token 401
```

### 4.4 监听地址与 LIKE 行为，然后关端口

命令：

```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\probe_like.py
```

输出片段：

```
LOGIN 200 True
SEARCH '100%' 200 ['编号1000无百分号', '百分号 100% 完成']
SEARCH '%' 200 ['甲乙', '甲', '编号1000无百分号', '百分号 100% 完成']
SEARCH '甲_' 200 ['甲乙']
SEARCH '100' 200 ['编号1000无百分号', '百分号 100% 完成']
  TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING       36844
after_parent_terminate TimeoutError None timed out parent_rc 1
```

关停后复查：

```
E:\muse-bridge\in\TASK-040-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-040-dailymemo\check_port.py
NO_LISTENER_ON_8000
```

8129（live_selftest）在进程退出时已由脚本 `terminate`。稍后端口复查时，8000 上出现过另一个任务的进程 `E:\muse-bridge\work\TASK-044-freshfeeds\serve_once.py`（PID 32492），不是 dailymemo，没有动它。

### 4.5 标签规则与前端渲染

`probe_server.py` 调用 `extract_tags` 的结果片段：

```
'#tag-' -> ['tag']
'#-tag' -> ['tag']
'#--' -> []
'a#b' -> []
'_#under' -> []
'## 标题' -> []
'##标题' -> []
'#你好' -> ['你好']
'#Tag #tag' -> ['Tag']
char 0xbd ½ extract ['x½y']
char 0x2461 ② extract ['x②y']
char 0x203f ‿ extract ['x'] precede ['tag']
```

前端用仓库里的 `static/index.html` 函数在 Node v24.21.0 下渲染（`probe_render.js`）：

```
IN  "今天 #工作"
OUT 今天 #<span class="tag" data-tag="工作">#工作</span>
IN  "#x‿y"
OUT #<span class="tag" data-tag="x‿y">#x‿y</span>
IN  "<#lt"
OUT &lt;#<span class="tag" data-tag="lt">#lt</span>
IN  "a#b"
OUT a#b
```

## 5. 收尾前再跑一次全量测试

命令与第 2 节相同（`run_pytest.py`）。

```
21 passed, 3 warnings in 3.55s
```

警告仍是 `app.py:138` 的 `on_event` 弃用，以及 Starlette 提示 TestClient 要换 `httpx2`。没有失败项。
