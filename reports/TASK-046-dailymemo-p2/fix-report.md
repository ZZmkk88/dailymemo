# 修复记录

## P1-1 会话 token 明文入库（上一轮 P2-8）

- 文件：`app.py:110-112` 新增 `hash_token`；`app.py:186` 查询改为哈希；`app.py:210` 入库改为哈希；`app.py:227` 登出按哈希删除；`app.py:259` 改密吊销其他会话时按哈希排除当前会话。
- 改法：`sessions.token` 改存原文 token 的 sha256 十六进制。登录响应仍返回原文。校验、登出、吊销都先对请求头里的原文做同一种哈希。不改表结构。库里已有的明文会话对不上哈希，会变成未登录，需要重新登录。
- 本条改完后的全量 pytest（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-046-dailymemo-p2\run_pytest.py
```

```
24 passed, 1 warning in 3.54s
ELAPSED_S 3.81
```

- 库存核对（exit 0，`probe_token_after.py`）：`me_with_raw 200`；拿库存哈希当 Bearer 访问为 `401`；`stored_equals_raw False`；`stored_equals_sha256 True`；改密后其他会话 `401`、当前会话 `200`；登出后 `401`。

## 不修

上一轮 P2-1 到 P2-7、P2-9 到 P2-12 已在当前代码落地，理由和行号见 `review.md`。不重复改。

不采用的另一修法：列表超过 200 条时给界面做翻页。`README.md:17` 已写明默认 200、上限 500，上一轮修法是文档或翻页二选一。

不改功能清单里的「退出」、`NOTES.md` 的标签口径、httpx / Starlette 弃用警告、LICENSE、UPSTREAM。警告来自依赖里的 `fastapi/testclient.py:1`，要消掉就得改测试依赖版本或改 `tests/`。上游 commit 与版权原文未联网核实，没有确凿错误，不改事实性声明。

没有改 `tests/`，没有加 skip / xfail，没有放宽断言。

## 收尾全量 pytest

改完后的第二次全量（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-046-dailymemo-p2\run_pytest.py
```

```
24 passed, 1 warning in 3.54s
ELAPSED_S 3.80
```

## git status --porcelain

```
 M app.py
```
