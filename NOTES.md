# dailymemo 调研笔记

## 上游对象（2026-10-21 通过 GitHub 接口实查）

- 项目：Memos（github.com/usememos/memos），MIT 许可证。
- 默认分支 HEAD：`ccc1f82393ab50d2c8fea40865d8c2fbe05472a8`（2026-10-20 的提交）。
- LICENSE 原文版权行：`Copyright (c) 2025 Memos`（逐字复制，见 UPSTREAM.md）。
- 上游技术栈：Go 后端 + React 前端 + Protobuf 接口，支持 SQLite/MySQL/PostgreSQL。
  体量很大（多用户、空间、附件、评论、反应、分享、SSO 等），云端轻量复刻不照搬栈，
  只借核心产品思路，用 Python + FastAPI + SQLite 独立重写。

## 从上游读到的核心设计（通读 README 与 proto/store/memo.proto）

- 产品定位：一句话也能成一条笔记；所有笔记按天汇成个人时间线，方便回望。
- 标签不是单独填写的字段，而是**从正文内容里解析**出来的（`MemoPayload.tags`），
  标签的作用是把不同日子的同主题想法串起来。
- 内容属性也是从正文算出来的（`Property`：是否含链接/任务列表/代码块、取首个 H1 作标题）。
- 笔记本体（上游 API 层 Memo 资源）核心字段：content、create_time / update_time、
  pinned（置顶）、visibility（可见性）、creator、tags、attachments、relations。
- 数据为自托管，用户对数据有完全控制权。

## 本项目 MVP 取舍（任务书范围，做全不扩）

借鉴的核心概念：碎片短笔记、正文 #标签 自动识别、时间线流、关键词搜索、置顶。

明确不做（超出单用户 MVP）：多用户/注册、空间与协作、附件上传、评论、反应、
公开分享、可见性分级、Markdown 渲染管线、位置/链接预览等内容属性计算、
MySQL/PostgreSQL、Docker 打包。

## 实现方案

- 后端：单文件 FastAPI（app.py）+ SQLite，结构与登录方式沿用本团队
  bookmark-manager 已验证的做法（pbkdf2 密码哈希、自研 Token 会话表、24 小时过期、
  首次登录 must_change_password=1）。环境变量：`DAILYMEMO_DB_PATH`、
  `DM_INITIAL_USERNAME` / `DM_INITIAL_PASSWORD`、`PORT`。
- 数据表：users / sessions（同 bookmark-manager）；memos（id、user_id、content、
  pinned、created_at、updated_at）；memo_tags（memo_id、tag）——标签存解析结果，
  发/改笔记时从正文重算。
- 标签识别规则（自己定，写进 README）：`#` 后跟连续的非空白、非 `#`、非标点字符
  （中英文、数字、下划线、连字符），如 `#工作`、`#idea-2026`；`##` 不算标签开头；
  同一条笔记内去重。
- 列表排序：置顶在前，各自按创建时间倒序；支持 tag 筛选、q 关键词（LIKE）搜索。
- 前端：单页 static/index.html，自行设计布局（顶部编辑器卡 + 左侧标签栏 +
  时间线按日期分组），配色与操作排布与上游明显不同。

## 资源核对结论

云端实测：2 核 CPU、7.7G 内存、Python 3.12。本方案运行时仅需数十 MB 内存、
单个 SQLite 文件，无 GPU、无重型依赖，云端完全带得动。
