# dailymemo 修复记录

只改 review.md 里 P1-1、P1-2、P1-3。P0 无。P2 未动。

## P1-1 搜索通配符

- 问题：关键词里的 `%`、`_` 被 SQLite LIKE 当成通配符，`%` 会命中全部笔记。
- 文件：`app.py:300-303` 新增 `_contains_like`；`app.py:350-352` 改为 `LIKE ? ESCAPE '\'` 并传入转义后的模式。原问题位置是修复前的 `app.py:343-344`。
- 改法：先把 `\` 转成 `\\`，再转义 `%` 和 `_`，前后仍加未转义的 `%` 做子串匹配。
- 验证：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests/test_app.py::test_search_by_keyword tests/test_app.py::test_search_no_hit tests/test_app.py::test_create_and_list_order -q
```

exit 0。`3 passed, 3 warnings in 0.83s`。

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\verify_p1_1.py
```

exit 0。输出：

```
OK '%' => ['score 100%']
OK '_' => ['file_name']
OK '100%' => ['score 100%']
OK 'file_name' => ['file_name']
OK '爬山' => []
OK 'secret' => ['alpha secret']
OK '\\' => ['path\\to\\note']
OK 'to' => ['path\\to\\note']
P1-1 VERIFY PASS
```

修复前同样的 `%` / `_` 会命中库里全部笔记（见 review.md 探针：count 2）。

## P1-2 改密不能与旧密码相同

- 问题：新旧密码相同仍返回成功，并把 `must_change_password` 清成 0。
- 文件：`app.py:223-224`。在旧密码校验通过之后、写库之前拒绝。
- 改法：相同则 `400`，详情「新密码不能与旧密码相同」，不更新哈希、不清标记。
- 验证：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests/test_app.py::test_change_password tests/test_app.py::test_change_password_revokes_other_sessions tests/test_app.py::test_login_ok_and_must_change -q
```

这次 exit 1：`1 failed, 2 passed, 3 warnings in 1.70s`。失败的是 `test_login_ok_and_must_change`，断言 `must_change_password is True` 得到 False。原因：这三条共用 `tests/test_app.py` 模块级的同一个数据库，我把改密用例排在首次登录用例前面，改密成功后标记已是 0。不是「相同密码被拒绝」这条逻辑把登录弄坏。

单独再跑首次登录（新进程，exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests/test_app.py::test_login_ok_and_must_change -q
```

`1 passed, 3 warnings in 0.66s`。

改密行为探针（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\work\TASK-023-dailymemo\verify_p1_2.py
```

```
same 400 {"detail":"新密码不能与旧密码相同"}
me 200 {"username":"admin","must_change_password":true}
short 400 {"detail":"新密码至少 6 位"}
bad-old 400 {"detail":"旧密码不正确"}
changed 200 {"ok":true}
me-after 200 {"username":"admin","must_change_password":false}
old-login 401
new-login 200 False
P1-2 VERIFY PASS
```

## P1-3 标签渲染多出一个 #

- 问题：`#工作` 被画成可见的 `##工作`。
- 文件：`static/index.html:250-261`（`renderTag`）。原错误返回在修复前的 `:256`。
- 改法：没有前导连字符时，高亮里只保留原文的那一个 `#`；有前导连字符时按原文顺序输出，不再额外前置 `#`。`<` `>` `&` 仍先走 `esc`。
- 验证：pytest 不覆盖页面 HTML。用 node 执行页面里的 `renderContent`：

```
node E:\muse-bridge\work\TASK-023-dailymemo\verify_p1_3.js
```

exit 0。片段：

```
OK "#工作"
  html <span class="tag" data-tag="工作">#工作</span>
  text "#工作"
OK "#tag-"
  text "#tag-"
OK "#-tag"
  text "#-tag"
OK "<script>alert(1)</script> #tag"
  html &lt;script&gt;alert(1)&lt;/script&gt; <span class="tag" data-tag="tag">#tag</span>
P1-3 VERIFY PASS
```

## 全量测试

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe -m pytest tests -q
```

exit 0。结果行：

```
21 passed, 3 warnings in 2.76s
```

警告仍是修复前就有的三条：`app.py:138` 的 `on_event` DeprecationWarning，FastAPI 内部同一条，以及 `StarletteDeprecationWarning`（httpx / TestClient）。没有失败项。

另跑 README 里的真实流程脚本（exit 0）：

```
E:\muse-bridge\work\TASK-023-dailymemo\.venv\Scripts\python.exe E:\muse-bridge\in\TASK-023-dailymemo\tests\live_selftest.py
```

末行 `LIVE SELFTEST: ALL PASS`。

## git status

收尾命令：

```
git status --porcelain
```

输出：

```
 M app.py
 M static/index.html
```

