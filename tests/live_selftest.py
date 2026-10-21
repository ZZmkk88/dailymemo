"""Live self-test for dailymemo: boots a real uvicorn server on a scratch
database and walks the whole user flow over HTTP.

Run: .venv/bin/python tests/live_selftest.py
"""
import os
import subprocess
import sys
import tempfile
import time

import httpx

BASE = "http://127.0.0.1:8129"
http = httpx.Client(trust_env=False)


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" | {extra}" if extra else ""))
    if not cond:
        raise SystemExit(f"selftest failed at: {name}")


def main():
    tmp = tempfile.mkdtemp(prefix="dm-live-")
    env = dict(os.environ)
    env["DAILYMEMO_DB_PATH"] = os.path.join(tmp, "live.db")
    env["PORT"] = "8129"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # wait for server
        for _ in range(50):
            try:
                if http.get(BASE + "/", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        else:
            raise SystemExit("server did not come up")

        page = http.get(BASE + "/")
        check("首页能打开且是 dailymemo 页面", "dailymemo" in page.text)

        r = http.post(BASE + "/api/login",
                       json={"username": "admin", "password": "admin123"})
        check("登录成功", r.status_code == 200, r.text[:120])
        data = r.json()
        check("首次登录提示改密", data["must_change_password"] is True)
        h = {"Authorization": f"Bearer {data['token']}"}

        seeds = [
            "写周报要点，别忘了附数据 #工作",
            "读到一段接口文档，讲得很清楚 #文档",
            "下班买牛奶和鸡蛋 #生活",
            "又一篇文档笔记，讲缓存的 #文档 #工作",
        ]
        ids = []
        for text in seeds:
            r = http.post(BASE + "/api/memos", json={"content": text}, headers=h)
            check(f"发笔记：{text[:10]}…", r.status_code == 200, r.text[:120])
            ids.append(r.json()["id"])

        r = http.get(BASE + "/api/memos", headers=h)
        items = r.json()
        check("时间线共 4 条且最新在前", len(items) == 4 and items[0]["id"] == ids[-1])

        r = http.get(BASE + "/api/memos", params={"tag": "文档"}, headers=h)
        items = r.json()
        check("按标签 #文档 筛选命中 2 条", len(items) == 2
              and all("文档" in m["tags"] for m in items), f"got {len(items)}")

        r = http.get(BASE + "/api/memos", params={"q": "文档"}, headers=h)
        check("搜索「文档」命中 2 条", len(r.json()) == 2)

        r = http.get(BASE + "/api/tags", headers=h)
        tags = {t["tag"]: t["count"] for t in r.json()}
        check("标签统计正确", tags.get("工作") == 2 and tags.get("文档") == 2
              and tags.get("生活") == 1, str(tags))

        r = http.post(BASE + f"/api/memos/{ids[2]}/pin",
                       json={"pinned": True}, headers=h)
        check("置顶接口成功", r.status_code == 200 and r.json()["pinned"] is True)
        r = http.get(BASE + "/api/memos", headers=h)
        check("置顶后 #生活 那条排第一", r.json()[0]["id"] == ids[2])

        r = http.put(BASE + f"/api/memos/{ids[0]}",
                      json={"content": "写周报要点（已改）#工作 #例行"}, headers=h)
        check("编辑生效且标签重算", r.status_code == 200
              and sorted(r.json()["tags"]) == ["例行", "工作"], r.text[:160])

        r = http.delete(BASE + f"/api/memos/{ids[1]}", headers=h)
        check("删除成功", r.status_code == 200)
        r = http.get(BASE + f"/api/memos/{ids[1]}", headers=h)
        check("删后查不到", r.status_code == 404)
        r = http.get(BASE + "/api/memos", headers=h)
        check("删后剩 3 条", len(r.json()) == 3)

        print("LIVE SELFTEST: ALL PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
