# dailymemo 验收报告

结论：按 README 能装上、能测完、能在本机 8000 端口打开首页。pytest **21 passed**（3.00s），`tests/live_selftest.py` **ALL PASS**。没有 `/health`（404），首页 200 即存活信号。没有 P0。P1 修 3 项（搜索通配符、改密可原样通过、标签多渲染一个 `#`）。上游 commit 与版权原文未联网核实。

## 本地跑通记录

环境：系统 `Python 3.11.9`。虚拟环境放在 `E:\muse-bridge\work\TASK-023-dailymemo\.venv`（不放进仓库）。依赖用该环境安装 `requirements-dev.txt`（内含 `requirements.txt`）。

安装命令与结果（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pip install -r E:\muse-bridge\in\TASK-023-dailymemo\requirements-dev.txt
```

装上 `fastapi==0.156.4`、`uvicorn==0.54.0`、`httpx==0.28.1`、`pytest==9.1.1`（以及 starlette==1.9.0、pydantic==2.14.1）。

pytest（仓库根，exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests -q
```

```
21 passed, 3 warnings in 3.00s
```

警告原文要点：`app.py:138 DeprecationWarning: on_event is deprecated`；`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`。警告没有让测试失败。`on_event` 仍然会跑（未登录访问 `/api/memos` 返回 401 而不是缺表 500）。

这次 pytest 发生在改 `TEMP` 之前，`tests/test_app.py:7` 的 `tempfile.mkdtemp(prefix="dm-test-")` 写到了系统临时目录：`dm-test-g3pvnmxg`、`dm-test-m3_qtd4y`。之后的进程把 `TEMP`/`TMP` 指到工作目录。

真实流程自测（exit 0，临时库 `E:\muse-bridge\work\TASK-023-dailymemo\dm-live-tby2x9rr`）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\in\TASK-023-dailymemo\tests\live_selftest.py
```

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

token 中段省略；该进程结束时临时库已废弃。

服务（数据库 `E:\muse-bridge\work\TASK-023-dailymemo\smoke.db`，脚本请求后 `terminate`）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\smoke_server.py
```

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
GET / 200 len 16040 has_dailymemo True
/health 404 {"detail":"Not Found"}
/api/health 404 {"detail":"Not Found"}
/healthz 404 {"detail":"Not Found"}
/docs 200
/openapi.json 200
/api/me 401 {"detail":"未登录"}
LOGIN 200 must_change_password true
```

子进程 `EXIT 1` 是 `terminate()` 的返回码。终止前已有 `Application startup complete` 和首页 200。进程已退出。

README 没有健康检查路径。404 不记为缺陷。

## README 与实际不符处

以下用探针核对过。探针命令见 `run.md` 第 4 节。

1. **`#` 的前置条件比 README 宽。** README.md:14 写「`#` 前不能紧邻字母或数字」。`app.py:41` 的 `(?<![\w#])` 把下划线和其他词字符也算前置。探针：`'_#under' => []`。前端 `static/index.html:249` 同样不匹配 `_#under`。`a#b`、`## 标题` 与 README 一致（探针结果为 `[]`）。

2. **前端标签字符集比 README 和后端宽。** README.md:12-13 允许字母、数字、下划线、连字符。后端 `app.py:41` 的 `\w` 里，连接符（Pc）只有 `U+005F`（探针：`Pc matched by \w: 1 ['U+005F']`，另外 9 个 Pc 不算）。`#‿tie` 后端结果 `[]`。前端 `static/index.html:248` 用了 `\p{Pc}`，`#‿x` 被当成标签。`static/index.html:244-245` 的注释说 Python `\w` 包含整个 Pc，与探针不符。

3. **正文里的标签会多显示一个 `#`。** README.md:12、README.md:15 按原文 `#标签` 描述。`static/index.html:256` 在已含 `#` 的匹配前又拼了一个 `#`。node 探针：`#工作` 的 HTML 是 `#<span class="tag" data-tag="工作">#工作</span>`，可见文本为 `##工作`。`data-tag` 仍是 `工作`，点击筛选的名字是对的，画面是错的。

4. **「均已测试覆盖」覆盖不到时间线分组。** README.md:7 说功能清单均已测试覆盖，README.md:18 的功能是今天 / 昨天 / 具体日期。分组只存在于 `static/index.html:261-267` 与 `:295`。`tests/test_app.py` 没有对分组文案的断言；`:153` 的「今天」是笔记正文，不是日期标题。pytest 的 21 项与 README.md:69 的计数一致，但 69 行的测试清单本身也没写日期分组。

5. **关键词搜索不是字面匹配。** README.md:16 写按关键词搜正文。`app.py:343-344` 把关键词直接放进 `LIKE %...%`，不转义 `%` 和 `_`。探针在只有「alpha secret」「beta other」两条时：`q=%` 命中 2 条，`q=_` 命中 2 条。`' OR 1=1 --` 命中 0 条，参数化查询没有被拼进 SQL。

6. **列表有未写明的条数上限。** README.md:10 只说按时间倒序。`app.py:331` 默认 `limit=200`，`app.py:36` 上限 500。`static/index.html:278` 请求 `/api/memos` 时不传 `limit`，也没有翻页。超过 200 条时界面看不到更老的笔记；超过 500 条时接口也不返回。

7. **功能清单没有写退出，代码有。** README.md:7 称与代码一一对应，README.md:9 只写登录。退出在 `app.py:201` 和 `static/index.html:123`。README.md:69 的测试说明写了「登出」，与功能清单不是同一口径。

已核对、与代码一致的部分：默认端口 8000（`app.py:440`，日志 `127.0.0.1:8000`）、默认只绑 `127.0.0.1`（`app.py:31`）、数据库默认绝对路径 `app.py` 旁的 `data/dailymemo.db`（`app.py:20-21`）、初始账号 admin / admin123（`app.py:33-34`，登录返回 `must_change_password: true`）、会话 24 小时（`app.py:32`）、`#tag-` 存成 `tag`（探针与 README.md:13 的例子一致）、置顶排在最前（live_selftest）。

附：`NOTES.md:39` 写标签是「非空白、非 `#`、非标点」，同时又举连字符。实现是 `\w` 加连字符，不是「连续非空白」。NOTES 不是 README，不单列进上面的编号。

## 许可证与署名核查

仓库内部一致，上游原件未核实。

- `LICENSE:1-3`：MIT，`Copyright (c) 2026 dailymemo contributors`。许可正文与常见 MIT 模板一致（授予、保留版权声明、AS IS 免责）。
- `README.md:92`：本项目 MIT，并指向 LICENSE 与 UPSTREAM。与 LICENSE 一致。
- `UPSTREAM.md:7-8`：上游记为 MIT，归因行 `Copyright (c) 2025 Memos`。`UPSTREAM.md:17-18` 说本仓库是独立重写，未复制上游源码。抽查 `app.py` 与 `static/index.html` 是 Python / FastAPI / 单页 HTML，未见 Go 或 protobuf 源码粘贴。
- `NOTES.md:5-7` 与 UPSTREAM 的项目名、commit、版权行相同。
- 本项目版权（2026 dailymemo contributors）和上游归因（2025 Memos）指的不是同一份作品，两者并列不冲突。

未核实（任务禁止抓取外网，不用训练记忆冒充查证）：

- `UPSTREAM.md:5` 的 `source_commit` `ccc1f82393ab50d2c8fea40865d8c2fbe05472a8` 是否为 2026-10-21 当天 usememos/memos 默认分支 HEAD。
- `UPSTREAM.md:13-14` 引用的提交说明是否与该 commit 一致。
- `UPSTREAM.md:16` 声称归因行逐字来自上游 LICENSE。没有上游原文，不能判定这句是错的，因此不改 LICENSE / UPSTREAM。

## 分级修复清单

行号是修复前的位置。改完之后的行号写在 fix-report.md。

### P0

无。安装、21 项测试、live_selftest、8000 首页均已通过。`on_event` 弃用警告当前不影响启动。

### P1

1. **P1-1** 搜索把 `%`、`_` 当成 LIKE 通配符，返回错误笔记。`app.py:343-344`。修法：先转义 `\`、`%`、`_`，再用 `LIKE ? ESCAPE '\'`。
2. **P1-2** 新旧密码相同仍返回成功，并把 `must_change_password` 清成 0，初始密码警告可以被原密码消掉。`app.py:219-222`（写入在 `:228`）。修法：新旧密码相同则 400，不改库。
3. **P1-3** 时间线把含标签的正文多画出一个 `#`，画面与库存原文不一致。`static/index.html:256`。修法：按匹配到的原文输出 `#` 和连字符，不再额外前置 `#`。

### P2

1. `app.py:138` 仍用已弃用的 `on_event("startup")`。修法：改成 lifespan，在启动时调用现有 `init_db()`。当前仍会执行，所以不是 P0。
2. `app.py:331` 默认只返回 200 条，`app.py:36` 硬顶 500，`static/index.html:278` 无翻页。修法：文档写明上限，或让界面能继续取更老的笔记。
3. README.md:14 与 `app.py:41` 对 `_#标签` 的说法不一致。修法：把 README 改成「`#` 前不能紧邻词字符或另一个 `#`」。不改匹配行为（测试与前端都是现在的行为）。
4. `static/index.html:248` 的 `\p{Pc}` 与后端 `\w` 不一致。修法：前端去掉 `\p{Pc}`，只保留下划线，与 `app.py:41` 对齐。
5. README.md:7 与 README.md:18 声称日期分组已测试，但测试里没有断言。修法：改 README 的「均已测试覆盖」表述。不改测试文件。
6. 未登录可打开 `/docs`、`/redoc`、`/openapi.json`（smoke 均为 200）。修法：生产默认关掉这三个路由，或加上登录。数据接口本身仍要 Bearer。
7. `app.py:184` 用 `!=` 比较密码哈希。修法：改为 `hmac.compare_digest`。
8. `app.py:187-189` 会话 token 明文进 `sessions`。修法：库存哈希，校验时哈希后再查。本地库被拷走时，明文 token 在过期前可直接重放。
9. `static/index.html:46` 给所有 `.tname` 加了 `# ` 前缀，`:130` 的「全部笔记」也会变成「# 全部笔记」。修法：全部笔记不要用这个 `::before`。
10. `static/index.html:295` 置顶笔记不进入日期分组标题，与 README.md:18 的「按日期分组」不完全一致。修法：置顶区单独标题，或置顶项也按天分组。
11. `static/index.html:218` 改密成功后不隐藏 `:136` 的初始密码横幅，要等下次请求 `/api/me`。修法：成功后给横幅加上 `hidden`。
12. `app.py:35` 正文上限 10000，README 未写。修法：在 README 补一句。

只修上面 3 个 P1。P2 不动。不改测试、依赖版本号、LICENSE、UPSTREAM。
