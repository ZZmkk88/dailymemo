# 上游溯源（UPSTREAM）

本项目在设计时学习了开源项目 Memos 的核心思路。按接力规范记录上游信息如下：

- **source_url**: https://github.com/usememos/memos
- **source_commit**: ccc1f82393ab50d2c8fea40865d8c2fbe05472a8
- **license**: MIT
- **attribution**: Copyright (c) 2025 Memos

## 说明

- `source_commit` 是 2026-10-21 通过 GitHub 接口实查的上游默认分支 HEAD 提交
  （提交说明 "refactor: keep link preview and double-click edit as device
  preferences"，提交时间 2026-10-20）；当日做设计调研时通读的上游内容正是
  这一提交，包括 README、`proto/store/memo.proto`（数据模型）与仓库目录结构。
- `attribution` 的版权行逐字复制自上游仓库 `LICENSE` 原文，未做任何改动。
- 本项目代码为独立重写（Python + FastAPI + SQLite），未复制上游源码；
  借鉴的是碎片笔记的产品思路：短内容记录、按时间线汇集、正文 `#标签`
  自动识别、关键词检索、置顶。调研细节见 NOTES.md。
