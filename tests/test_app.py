"""Automated tests for dailymemo. Run: .venv/bin/python -m pytest tests/ -q"""
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp(prefix="dm-test-")
os.environ["DAILYMEMO_DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["DM_INITIAL_USERNAME"] = "admin"
os.environ["DM_INITIAL_PASSWORD"] = "admin123"

import app as appmod  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(appmod.app) as c:
        yield c


def do_login(client, password="admin123"):
    res = client.post("/api/login", json={"username": "admin", "password": password})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture(scope="function")
def auth(client):
    """每个用例独立登录：避免用例之间共享 token（TASK-008 P1-1 之后，
    改密会吊销其他会话，共享 token 会互相踩）。"""
    data = do_login(client)
    return {"Authorization": f"Bearer {data['token']}"}


def create(client, auth, content):
    res = client.post("/api/memos", json={"content": content}, headers=auth)
    assert res.status_code == 200, res.text
    return res.json()


# ---------------------------------------------------------------- auth ----

def test_login_wrong_password(client):
    res = client.post("/api/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_login_ok_and_must_change(client):
    data = do_login(client)
    assert data["token"]
    assert data["must_change_password"] is True


def test_unauthenticated_rejected(client):
    assert client.get("/api/memos").status_code == 401
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/memos", json={"content": "x"}).status_code == 401


def test_logout_invalidates_token(client, auth):
    res = client.post("/api/logout", headers=auth)
    assert res.status_code == 200
    assert client.get("/api/me", headers=auth).status_code == 401


def test_change_password(client, auth):
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "newpass456"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    assert do_login(client, "newpass456")["must_change_password"] is False
    # restore for later tests
    token2 = do_login(client, "newpass456")["token"]
    res = client.post(
        "/api/change-password",
        json={"old_password": "newpass456", "new_password": "admin123"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 200


def test_change_password_rejects_same_password(client, auth):
    """P1-2: 新密码与旧密码相同 → 400，不更新哈希、不清改密标记。"""
    before = client.get("/api/me", headers=auth).json()["must_change_password"]
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "admin123"},
        headers=auth,
    )
    assert res.status_code == 400
    assert "不能与旧密码相同" in res.json()["detail"]
    assert client.get("/api/me", headers=auth).json()["must_change_password"] == before
    assert do_login(client)["token"]  # 旧密码仍可用


def test_docs_disabled_by_default(client):
    """P2-6: 交互式文档默认关闭，未登录打不开。"""
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_change_password_revokes_other_sessions(client):
    """P1-1: 改密后，用旧密码签发的其他会话 token 立即失效；
    本次改密请求的会话保留可用。"""
    tok_current = do_login(client)["token"]
    tok_other = do_login(client)["token"]
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123", "new_password": "admin123x"},
        headers={"Authorization": f"Bearer {tok_current}"},
    )
    assert res.status_code == 200, res.text
    assert client.get("/api/me", headers={"Authorization": f"Bearer {tok_other}"}).status_code == 401
    assert client.get("/api/me", headers={"Authorization": f"Bearer {tok_current}"}).status_code == 200
    # restore password for later tests
    res = client.post(
        "/api/change-password",
        json={"old_password": "admin123x", "new_password": "admin123"},
        headers={"Authorization": f"Bearer {tok_current}"},
    )
    assert res.status_code == 200


# -------------------------------------------------------------- memos ----

def test_create_and_list_order(client, auth):
    a = create(client, auth, "第一条笔记")
    b = create(client, auth, "第二条笔记")
    items = client.get("/api/memos", headers=auth).json()
    ids = [m["id"] for m in items]
    assert ids.index(b["id"]) < ids.index(a["id"])  # newest first
    first = [m for m in items if m["id"] == a["id"]][0]
    assert first["content"] == "第一条笔记"
    assert first["pinned"] is False
    assert first["tags"] == []


def test_create_empty_rejected(client, auth):
    res = client.post("/api/memos", json={"content": "   "}, headers=auth)
    assert res.status_code == 400


def test_edit_memo(client, auth):
    m = create(client, auth, "待编辑的内容")
    res = client.put(
        f"/api/memos/{m['id']}", json={"content": "改过的内容 #新标签"}, headers=auth
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["content"] == "改过的内容 #新标签"
    assert body["tags"] == ["新标签"]
    assert body["updated_at"] >= body["created_at"]


def test_edit_missing_memo_404(client, auth):
    res = client.put("/api/memos/999999", json={"content": "x"}, headers=auth)
    assert res.status_code == 404


def test_delete_memo(client, auth):
    m = create(client, auth, "要删掉的")
    res = client.delete(f"/api/memos/{m['id']}", headers=auth)
    assert res.status_code == 200
    assert client.get(f"/api/memos/{m['id']}", headers=auth).status_code == 404


# --------------------------------------------------------------- tags ----

def test_tag_extraction_from_content(client, auth):
    m = create(client, auth, "今天读了一本书 #阅读 很有收获 #生活记录")
    assert sorted(m["tags"]) == ["生活记录", "阅读"]


def test_tag_edge_cases(client, auth):
    # markdown heading is not a tag; a#b is not a tag; duplicates deduped
    m = create(client, auth, "## 标题\n正文 a#b 不是标签 #重复 #重复 #ok-tag")
    assert sorted(m["tags"]) == ["ok-tag", "重复"]
    assert "标题" not in m["tags"]
    assert "b" not in m["tags"]
    assert m["tags"].count("重复") == 1


def test_tag_filter(client, auth):
    create(client, auth, "工作记录一 #工作")
    create(client, auth, "生活记录一 #生活")
    items = client.get("/api/memos", params={"tag": "工作"}, headers=auth).json()
    assert items
    assert all("工作" in m["tags"] for m in items)
    assert all("#工作" in m["content"] for m in items)


def test_tags_endpoint_counts(client, auth):
    create(client, auth, "计数用 #计数标签")
    create(client, auth, "计数用二 #计数标签")
    tags = client.get("/api/tags", headers=auth).json()
    entry = [t for t in tags if t["tag"] == "计数标签"]
    assert entry and entry[0]["count"] == 2


# -------------------------------------------------------------- search ----

def test_search_by_keyword(client, auth):
    create(client, auth, "周末去爬山，天气很好")
    create(client, auth, "周一开会讨论预算")
    items = client.get("/api/memos", params={"q": "爬山"}, headers=auth).json()
    assert len(items) == 1
    assert "爬山" in items[0]["content"]


def test_search_escapes_like_wildcards(client, auth):
    """P1-1: `%`、`_`、`\\` 按字面匹配，不被当成 LIKE 通配符。"""
    create(client, auth, "score 100%")
    create(client, auth, "file_name here")
    create(client, auth, "plain note")
    got = client.get("/api/memos", params={"q": "%"}, headers=auth).json()
    assert [m["content"] for m in got] == ["score 100%"]
    got = client.get("/api/memos", params={"q": "_"}, headers=auth).json()
    assert [m["content"] for m in got] == ["file_name here"]
    got = client.get("/api/memos", params={"q": "100%"}, headers=auth).json()
    assert [m["content"] for m in got] == ["score 100%"]
    create(client, auth, "back\\slash")
    got = client.get("/api/memos", params={"q": "\\"}, headers=auth).json()
    assert [m["content"] for m in got] == ["back\\slash"]


def test_search_no_hit(client, auth):
    items = client.get("/api/memos", params={"q": "不存在的词xyz"}, headers=auth).json()
    assert items == []


# ---------------------------------------------------------------- pin ----

def test_pin_sorts_first(client, auth):
    older = create(client, auth, "较早的一条")
    create(client, auth, "较晚的一条")
    res = client.post(
        f"/api/memos/{older['id']}/pin", json={"pinned": True}, headers=auth
    )
    assert res.status_code == 200
    assert res.json()["pinned"] is True
    items = client.get("/api/memos", headers=auth).json()
    assert items[0]["id"] == older["id"]  # pinned beats recency
    # unpin restores normal order
    client.post(f"/api/memos/{older['id']}/pin", json={"pinned": False}, headers=auth)
    items = client.get("/api/memos", headers=auth).json()
    assert items[0]["id"] != older["id"]


def test_extract_tags_unit():
    assert appmod.extract_tags("没有标签") == []
    assert appmod.extract_tags("#a #b-c #中文") == ["a", "b-c", "中文"]
    assert appmod.extract_tags("## 不是标签") == []


def test_extract_tags_strips_surrounding_hyphens():
    # 首尾连字符被剥掉（前后端渲染规则一致），只剩连字符则不算标签
    assert appmod.extract_tags("#-tag") == ["tag"]
    assert appmod.extract_tags("#tag-") == ["tag"]
    assert appmod.extract_tags("#--") == []
    assert appmod.extract_tags("#2026计划 #计划-2026") == ["2026计划", "计划-2026"]


def test_host_env_override(monkeypatch):
    # P1-2: 默认只监听本地回环，HOST 环境变量可覆盖
    monkeypatch.delenv("HOST", raising=False)
    assert appmod.resolve_host() == "127.0.0.1"
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert appmod.resolve_host() == "0.0.0.0"
