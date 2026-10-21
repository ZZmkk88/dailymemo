# TASK-046-dailymemo-p2 执行记录

开工：2026-10-21。工作目录 `E:\muse-bridge\in\TASK-046-dailymemo-p2`。本轮只处理上一轮审查报告中的 P2 条目。

## 步骤 0 — 建立执行记录

已创建本文件。下一步：只读打开 `E:\muse-bridge\out\TASK-023-dailymemo\review.md`。

## 步骤 1 — 只读上一轮报告与当前源码

已读 `E:\muse-bridge\out\TASK-023-dailymemo\review.md`。上一轮 P2 共 12 条。当前仓库 HEAD `cff0aee`，`git status --porcelain` 为空。

环境预检（exit 0）：

```
python --version
Python 3.11.9
```

```
Test-Path E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe
True
```

本任务工作目录下尚无 `.venv`。后续 pytest 复用上一轮已装好的 venv，不往仓库里装依赖。临时库与 pytest 临时目录指到 `E:\muse-bridge\work\TASK-046-dailymemo-p2`。

## 步骤 2 — 基线全量 pytest

命令（仓库根，禁用 pyc 与 pytest 缓存，避免把缓存写进仓库）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-046-dailymemo-p2\run_pytest.py
```

第一次（exit 1，包装脚本的导入路径问题，不是项目缺陷）：`run_pytest.py` 当时没有把仓库根放进 `sys.path`，`tests/test_app.py` 的 `import app` 失败。

```
ERROR tests/test_app.py
ModuleNotFoundError: No module named 'app'
1 error in 0.29s
```

已在包装脚本里 `sys.path.insert(0, 仓库根)` 后重跑。直接在仓库根执行 `python -m pytest tests -q` 不会踩这个路径问题。

探针 `probe_p2.py`（exit 0）同时完成，要点：

- `GET /docs`、`/redoc`、`/openapi.json` 均为 404；`GET /api/memos`、`/api/me` 为 401
- 新旧密码相同：400 `新密码不能与旧密码相同`
- `sessions.token` 与登录返回的原始 token 相同（`stored_equals_raw_token True`）
- Python `\w` 与 Lu/Ll/Lt/Lm/Lo/Nd/Nl/No 加下划线完全一致（extra 0，missing 0）；Pc 仅 `005F`
- 启动警告只有 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`，没有 `on_event` 警告

## 步骤 2b — 重跑基线 pytest

包装脚本补上仓库根路径后（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-046-dailymemo-p2\run_pytest.py
```

```
24 passed, 1 warning in 4.97s
ELAPSED_S 5.27
```

警告只有一条，来自依赖而不是 `app.py`：

```
fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

没有 `on_event is deprecated`。

第一次用 node 抽前端正则时，把源码里的 `\\` 当成了模式正文，样本结果无效，不作为证据。下面改成按 JavaScript 字面量求值后再比。

## 步骤 2c — 前端标签求值，以及 live_selftest

前端第二次求值（exit 0）。第一次失败是探针把 `const TAG_RE` 求值了两遍（`SyntaxError: Identifier 'TAG_RE' has already been declared`），不是页面脚本的错。改正后按页面里的 `esc` / `TAG_RE` / `renderContent` 在 vm 里执行。

正则实际是 `(?<![\p{Lu}\p{Ll}\p{Lt}\p{Lm}\p{Lo}\p{Nd}\p{Nl}\p{No}_#])#([\p{Lu}..._-]+)`，flags `gu`。

样本与后端一致，且可见文本等于原文（`visibleEq true`）：`_#under`、`a#b`、`## 标题` 无标签；`#工作` → `工作`；`#tag-` / `#-tag` → `tag`；`#--`、`#‿x`、`中#文`、`x_#no` 无标签；`#ok_1` → `ok_1`；`#tag#tag` → 只有 `tag`；`#²` → `²`；`#Ⅰ` → `Ⅰ`；`今天 #工作 和 #文档` → `工作`、`文档`。

`probe_extra.py`（exit 0）后端：`#²` → `['²']`，`#Ⅰ` → `['Ⅰ']`，`#‿x` → `[]`，`中#文` → `[]`。

live_selftest（exit 0，2.12s）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-046-dailymemo-p2\run_live.py
```

```
LIVE SELFTEST: ALL PASS
ELAPSED_S 2.12
```

登录 200 且 `must_change_password true`，4 条时间线、标签筛选、搜索、置顶、编辑、删除均 PASS。临时库在工作目录（`TEMP`/`TMP` 已指向该目录）。登录响应里的 token 不写入本记录。

## 步骤 3 — 审查结论与开始改 P1-1

结论已写入 `review.md`。已改 `app.py` 的入库、查询、登出、改密吊销。下一步跑全量 pytest，并核对库存值。

## 步骤 4 — P1-1 改完后的全量 pytest 与库存核对

pytest（exit 0）：

```
24 passed, 1 warning in 3.54s
ELAPSED_S 3.81
```

`probe_token_after.py`（exit 0）：

```
me_with_raw 200
me_with_stored_hash 401
session_count 2
stored_equals_raw False
stored_equals_sha256 True
change 200
other_after 401
current_after 200
logout 200
after_logout 401
```

## 步骤 5 — 收尾全量 pytest 与 git status

pytest（exit 0）：

```
24 passed, 1 warning in 3.54s
ELAPSED_S 3.80
```

`git diff --stat`：

```
 app.py | 13 +++++++++----
 1 file changed, 9 insertions(+), 4 deletions(-)
```

`git status --porcelain`（exit 0，原样）：

```
 M app.py
```


