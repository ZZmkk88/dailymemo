"""dailymemo: a lightweight self-hosted fragment-notes app.

Capture short notes on a personal timeline; tags are parsed from `#tag`
markers in the text. Single-file FastAPI backend + SQLite + one static page.
Design notes live in NOTES.md.
"""
import hashlib
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DAILYMEMO_DB_PATH", str(BASE_DIR / "data" / "dailymemo.db"))


def resolve_host() -> str:
    """Bind address for the built-in server.

    Defaults to the loopback interface so a default install is not reachable
    over the LAN while the README ships a default password. Set ``HOST`` to
    ``0.0.0.0`` explicitly when LAN access is wanted.
    """
    return os.environ.get("HOST") or "127.0.0.1"
TOKEN_TTL_SECONDS = 24 * 60 * 60
INITIAL_USERNAME = os.environ.get("DM_INITIAL_USERNAME", "admin")
INITIAL_PASSWORD = os.environ.get("DM_INITIAL_PASSWORD", "admin123")
MAX_CONTENT_LENGTH = 10000
MAX_LIST_LIMIT = 500

# A tag is `#` followed by word characters (unicode, so Chinese works) or
# hyphens. The `#` must not be preceded by a word char or another `#`,
# so markdown headings like `## title` and `a#b` are not tags.
TAG_RE = re.compile(r"(?<![\w#])#([\w-]+)", re.UNICODE)

app = FastAPI(title="dailymemo")


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def extract_tags(content: str) -> list[str]:
    """Parse `#tag` markers out of note content, dedupe, keep first-seen order."""
    seen = set()
    result = []
    for match in TAG_RE.finditer(content or ""):
        name = match.group(1).strip("-")
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


# ---------------------------------------------------------------------------
# database
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 200_000
    ).hex()


def init_db() -> None:
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                expires_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                content TEXT NOT NULL,
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memo_tags (
                memo_id INTEGER NOT NULL REFERENCES memos(id) ON DELETE CASCADE,
                tag TEXT NOT NULL,
                tag_lower TEXT NOT NULL,
                PRIMARY KEY (memo_id, tag_lower)
            );
            """
        )
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        if row["c"] == 0:
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, must_change_password, created_at)"
                " VALUES (?, ?, ?, 1, ?)",
                (INITIAL_USERNAME, hash_password(INITIAL_PASSWORD, salt), salt, iso(utcnow())),
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def _startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------

class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


def current_user(request: Request) -> sqlite3.Row:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = auth[len("Bearer "):].strip()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token = ? AND s.expires_at > ?",
            (token, time.time()),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
        return row
    finally:
        conn.close()


@app.post("/api/login")
def login(body: LoginIn):
    init_db()
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (body.username.strip(),)
        ).fetchone()
        if not user or hash_password(body.password, user["salt"]) != user["password_hash"]:
            raise HTTPException(status_code=401, detail="用户名或密码不正确")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user["id"], time.time() + TOKEN_TTL_SECONDS),
        )
        conn.commit()
        return {
            "token": token,
            "username": user["username"],
            "must_change_password": bool(user["must_change_password"]),
        }
    finally:
        conn.close()


@app.post("/api/logout")
def logout(request: Request, user: sqlite3.Row = Depends(current_user)):
    token = request.headers.get("Authorization", "")[len("Bearer "):].strip()
    conn = get_db()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/change-password")
def change_password(
    body: ChangePasswordIn,
    request: Request,
    user: sqlite3.Row = Depends(current_user),
):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if hash_password(body.old_password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=400, detail="旧密码不正确")
    if body.new_password == body.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    salt = secrets.token_hex(16)
    current_token = request.headers.get("Authorization", "")[len("Bearer "):].strip()
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?, must_change_password = 0 WHERE id = ?",
            (hash_password(body.new_password, salt), salt, user["id"]),
        )
        # 密码已变：让其他地方用旧密码签发的 token 立即失效，本次请求的会话保留。
        conn.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token != ?",
            (user["id"], current_token),
        )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {
        "username": user["username"],
        "must_change_password": bool(user["must_change_password"]),
    }


# ---------------------------------------------------------------------------
# memos
# ---------------------------------------------------------------------------

class MemoIn(BaseModel):
    content: str


class PinIn(BaseModel):
    pinned: bool


def _memo_out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    tags = [
        r["tag"]
        for r in conn.execute(
            "SELECT tag FROM memo_tags WHERE memo_id = ? ORDER BY tag_lower",
            (row["id"],),
        ).fetchall()
    ]
    return {
        "id": row["id"],
        "content": row["content"],
        "pinned": bool(row["pinned"]),
        "tags": tags,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _validate_content(content: str) -> str:
    content = (content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    if len(content) > MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=400, detail="内容太长了")
    return content


def _save_tags(conn: sqlite3.Connection, memo_id: int, content: str) -> None:
    conn.execute("DELETE FROM memo_tags WHERE memo_id = ?", (memo_id,))
    for tag in extract_tags(content):
        conn.execute(
            "INSERT OR IGNORE INTO memo_tags (memo_id, tag, tag_lower) VALUES (?, ?, ?)",
            (memo_id, tag, tag.lower()),
        )


def _contains_like(keyword: str) -> str:
    """Literal substring for SQLite LIKE. Escape \\ first, then % and _."""
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _get_own_memo(conn: sqlite3.Connection, memo_id: int, user_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM memos WHERE id = ? AND user_id = ?", (memo_id, user_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return row


@app.post("/api/memos")
def create_memo(body: MemoIn, user: sqlite3.Row = Depends(current_user)):
    content = _validate_content(body.content)
    now = iso(utcnow())
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO memos (user_id, content, pinned, created_at, updated_at)"
            " VALUES (?, ?, 0, ?, ?)",
            (user["id"], content, now, now),
        )
        memo_id = cur.lastrowid
        _save_tags(conn, memo_id, content)
        conn.commit()
        row = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
        return _memo_out(conn, row)
    finally:
        conn.close()


@app.get("/api/memos")
def list_memos(
    tag: str = "",
    q: str = "",
    limit: int = 200,
    user: sqlite3.Row = Depends(current_user),
):
    limit = max(1, min(limit, MAX_LIST_LIMIT))
    clauses = ["m.user_id = ?"]
    params: list = [user["id"]]
    if tag.strip():
        clauses.append(
            "EXISTS (SELECT 1 FROM memo_tags t WHERE t.memo_id = m.id AND t.tag_lower = ?)"
        )
        params.append(tag.strip().lower())
    if q.strip():
        clauses.append("m.content LIKE ? ESCAPE '\\'")
        params.append(_contains_like(q.strip()))
    sql = (
        "SELECT m.* FROM memos m WHERE " + " AND ".join(clauses)
        + " ORDER BY m.pinned DESC, m.created_at DESC, m.id DESC LIMIT ?"
    )
    params.append(limit)
    conn = get_db()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_memo_out(conn, r) for r in rows]
    finally:
        conn.close()


@app.get("/api/memos/{memo_id}")
def get_memo(memo_id: int, user: sqlite3.Row = Depends(current_user)):
    conn = get_db()
    try:
        row = _get_own_memo(conn, memo_id, user["id"])
        return _memo_out(conn, row)
    finally:
        conn.close()


@app.put("/api/memos/{memo_id}")
def update_memo(memo_id: int, body: MemoIn, user: sqlite3.Row = Depends(current_user)):
    content = _validate_content(body.content)
    conn = get_db()
    try:
        _get_own_memo(conn, memo_id, user["id"])
        conn.execute(
            "UPDATE memos SET content = ?, updated_at = ? WHERE id = ?",
            (content, iso(utcnow()), memo_id),
        )
        _save_tags(conn, memo_id, content)
        conn.commit()
        row = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
        return _memo_out(conn, row)
    finally:
        conn.close()


@app.delete("/api/memos/{memo_id}")
def delete_memo(memo_id: int, user: sqlite3.Row = Depends(current_user)):
    conn = get_db()
    try:
        _get_own_memo(conn, memo_id, user["id"])
        conn.execute("DELETE FROM memos WHERE id = ?", (memo_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/memos/{memo_id}/pin")
def pin_memo(memo_id: int, body: PinIn, user: sqlite3.Row = Depends(current_user)):
    conn = get_db()
    try:
        _get_own_memo(conn, memo_id, user["id"])
        conn.execute(
            "UPDATE memos SET pinned = ? WHERE id = ?", (1 if body.pinned else 0, memo_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM memos WHERE id = ?", (memo_id,)).fetchone()
        return _memo_out(conn, row)
    finally:
        conn.close()


@app.get("/api/tags")
def list_tags(user: sqlite3.Row = Depends(current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT t.tag AS tag, COUNT(*) AS cnt FROM memo_tags t"
            " JOIN memos m ON m.id = t.memo_id WHERE m.user_id = ?"
            " GROUP BY t.tag_lower ORDER BY cnt DESC, t.tag_lower ASC",
            (user["id"],),
        ).fetchall()
        return [{"tag": r["tag"], "count": r["cnt"]} for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# static page
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=resolve_host(), port=int(os.environ.get("PORT", "8000")))
