# dailymemo · 碎片笔记

一句话定位：一个轻量、可自己部署的碎片笔记工具——随手记下一句话，按时间线攒起来，用 `#标签` 归类，随时搜回来。

本项目的设计学习了开源社区碎片笔记工具的通行思路——如短内容记录、时间线汇集、正文标签这类核心概念；代码为独立实现。上游溯源与署名见 [UPSTREAM.md](UPSTREAM.md)。

## 功能清单（与代码实现一一对应；后端接口均有自动化测试覆盖）

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录提示改密
- **记碎片**：写一条短笔记（纯文本、可多行），自动记录创建时间；列表按时间倒序排列
- **编辑 / 删除**：自己的笔记可随时改、随时删；编辑后标签会重新识别
- **标签**：正文里写 `#标签` 即自动识别成标签。`#` 后可跟字母（不限语种，中文可以）、
  数字、下划线或连字符；首尾多余的连字符会被自动去掉（如 `#tag-` 记为 `tag`）；
  `#` 前不能紧邻词字符（字母、数字、下划线，如 `a#b`、`_#tag` 都不算标签），
  也不能是 `## 标题` 这样的双井号；
  点左侧标签栏或正文里的标签即可筛选
- **搜索**：按关键词搜正文内容（`%`、`_` 按字面匹配，不会被当成通配符）；列表默认最多返回 200 条（上限 500，可用 `limit` 参数调小）
- **置顶**：一条笔记可置顶，置顶的排在时间线最前面（单独的"📌 置顶"区）
- **时间线**：笔记按日期分组展示（今天 / 昨天 / 具体日期）
- **记碎片**：一条笔记最多 10000 字

## 安装与启动

需要 Python 3.10 或更高版本。

**Linux / macOS（bash）:**

```bash
cd dailymemo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # 默认监听 8000 端口
```

**Windows（PowerShell）:**

```powershell
cd dailymemo
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py        # 默认监听 8000 端口
```

启动后打开 http://localhost:8000 ，默认账号 **admin / admin123**，首次登录会提示改密码。

可选环境变量：

| 变量 | 说明 | 默认 |
|---|---|---|
| `PORT` | 监听端口（Windows PowerShell 里用 `$env:PORT=8123` 设置） | 8000 |
| `HOST` | 监听地址（PowerShell 里用 `$env:HOST="0.0.0.0"` 设置） | `127.0.0.1`（默认只允许本机访问；局域网要用再设 `0.0.0.0`） |
| `DAILYMEMO_DB_PATH` | SQLite 数据库文件位置 | `app.py` 所在目录下的 `data/dailymemo.db`（绝对路径，不跟随启动目录） |
| `DM_INITIAL_USERNAME` / `DM_INITIAL_PASSWORD` | 首次启动创建的初始账号 | admin / admin123 |
| `DM_ENABLE_DOCS` | 设为 `1` 则打开 FastAPI 交互式文档（`/docs`） | 默认关闭 |

## 测试

先装测试依赖（两个系统的命令只是路径写法不同）：

```bash
# Linux / macOS
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q
```

```powershell
# Windows (PowerShell)
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest tests/ -q
```

共 27 项自动化测试（登录/登出/改密、改密吊销其他会话、新旧密码相同拒绝、token 入库哈希、发笔记、编辑、删除、#标签 识别与边界、标签筛选与统计、搜索通配符转义、置顶排序、监听地址环境变量、文档默认关闭、X-Frame-Options 响应头、时间戳微秒）。

真实流程自测（脚本会自己在 8129 端口起一个临时服务、跑完整流程再关掉）：

```bash
# Linux / macOS
.venv/bin/python tests/live_selftest.py
```

```powershell
# Windows (PowerShell)
.venv\Scripts\python tests\live_selftest.py
```

## 后续可扩展项

- 按天数统计的记录热力图
- 随机回顾一条旧笔记
- Markdown 渲染与代码块高亮
- 导入 / 导出（JSON、Markdown）

## 许可证

MIT（见 [LICENSE](LICENSE)）。本项目为独立实现；设计时学习的上游同为 MIT 许可证，其版权归因见 [UPSTREAM.md](UPSTREAM.md)。
