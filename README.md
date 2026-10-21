# dailymemo · 碎片笔记

一句话定位：一个轻量、可自己部署的碎片笔记工具——随手记下一句话，按时间线攒起来，用 `#标签` 归类，随时搜回来。

本项目的设计学习了开源社区碎片笔记工具的通行思路——如短内容记录、时间线汇集、正文标签这类核心概念；代码为独立实现。上游溯源与署名见 [UPSTREAM.md](UPSTREAM.md)。

## 功能清单（与代码实现一一对应，均已测试覆盖）

- **登录**：单用户账号，Token 登录（24 小时有效），首次登录提示改密
- **记碎片**：写一条短笔记（纯文本、可多行），自动记录创建时间；列表按时间倒序排列
- **编辑 / 删除**：自己的笔记可随时改、随时删；编辑后标签会重新识别
- **标签**：正文里写 `#标签` 即自动识别成标签（`#` 后跟中英文、数字、下划线或连字符；`## 标题`、`a#b` 不算标签），点左侧标签栏或正文里的标签即可筛选
- **搜索**：按关键词搜正文内容
- **置顶**：一条笔记可置顶，置顶的排在时间线最前面
- **时间线**：笔记按日期分组展示（今天 / 昨天 / 具体日期）

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
| `DAILYMEMO_DB_PATH` | SQLite 数据库文件位置 | `data/dailymemo.db` |
| `DM_INITIAL_USERNAME` / `DM_INITIAL_PASSWORD` | 首次启动创建的初始账号 | admin / admin123 |

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

共 17 项自动化测试（登录/改密、发笔记、编辑、删除、#标签 识别与边界、标签筛选与统计、搜索、置顶排序）。

真实流程自测（脚本会自己在 8129 端口起一个临时服务、跑完整流程再关掉）：

```bash
.venv/bin/python tests/live_selftest.py
```

## 后续可扩展项

- 按天数统计的记录热力图
- 随机回顾一条旧笔记
- Markdown 渲染与代码块高亮
- 导入 / 导出（JSON、Markdown）

## 许可证

MIT（见 [LICENSE](LICENSE)）。本项目为独立实现；设计时学习的上游同为 MIT 许可证，其版权归因见 [UPSTREAM.md](UPSTREAM.md)。
