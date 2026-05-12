#!/usr/bin/env python3
"""
Mantis Proxy API
部署在 Railway 上，作為 Claude 查詢 Mantis 的中介服務
"""

import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException, Header
from typing import Optional

app = FastAPI(title="Mantis Proxy", version="1.0.0")

# 從環境變數讀取設定（在 Railway 上設定）
MANTIS_URL = os.environ.get("MANTIS_URL", "https://mantis.cloud.softleader.com.tw")
MANTIS_API_KEY = os.environ.get("MANTIS_API_KEY", "")
PROXY_SECRET = os.environ.get("PROXY_SECRET", "")  # 保護這個服務的 token


def verify_token(authorization: Optional[str] = Header(None)):
    """驗證呼叫者的 token"""
    if not PROXY_SECRET:
        return  # 沒設定就不驗證（開發測試用）
    if authorization != f"Bearer {PROXY_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def fetch_mantis(path: str) -> dict:
    """呼叫 Mantis REST API"""
    url = f"{MANTIS_URL}/api/rest/{path}"
    req = urllib.request.Request(url, headers={"Authorization": MANTIS_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"Mantis error: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_issue(issue: dict) -> dict:
    """整理成簡潔格式給 Claude 使用"""
    notes = issue.get("notes", [])
    return {
        "id": issue.get("id"),
        "summary": issue.get("summary"),
        "status": issue.get("status", {}).get("label"),
        "priority": issue.get("priority", {}).get("label"),
        "severity": issue.get("severity", {}).get("label"),
        "handler": issue.get("handler", {}).get("name", "未指派"),
        "reporter": issue.get("reporter", {}).get("name"),
        "project": issue.get("project", {}).get("name"),
        "created_at": issue.get("created_at", "")[:19].replace("T", " "),
        "updated_at": issue.get("updated_at", "")[:19].replace("T", " "),
        "description": issue.get("description", "").strip()[:1000],
        "notes_count": len(notes),
        "notes_latest": [
            {
                "time": n.get("created_at", "")[:19].replace("T", " "),
                "author": n.get("reporter", {}).get("name", "?"),
                "text": n.get("text", "").strip()[:500],
            }
            for n in notes[-5:]  # 最新 5 則
        ],
    }


@app.get("/")
def root():
    return {"status": "ok", "service": "Mantis Proxy"}


@app.get("/issues/{issue_id}")
def get_issue(issue_id: int, authorization: Optional[str] = Header(None)):
    """查詢單一問題單"""
    verify_token(authorization)
    data = fetch_mantis(f"issues/{issue_id}")
    issue = data.get("issues", [data])[0] if "issues" in data else data
    return format_issue(issue)


@app.get("/issues")
def get_issues(
    issue_ids: str,  # 逗號分隔，如 ?issue_ids=36720,35923,34955
    authorization: Optional[str] = Header(None),
):
    """批次查詢多個問題單，如 ?issue_ids=36720,35923"""
    verify_token(authorization)
    ids = [int(i.strip()) for i in issue_ids.split(",") if i.strip().isdigit()]
    if not ids:
        raise HTTPException(status_code=400, detail="請提供有效的 issue_ids")
    if len(ids) > 20:
        raise HTTPException(status_code=400, detail="一次最多查詢 20 筆")

    results = []
    for issue_id in ids:
        try:
            data = fetch_mantis(f"issues/{issue_id}")
            issue = data.get("issues", [data])[0] if "issues" in data else data
            results.append(format_issue(issue))
        except HTTPException as e:
            results.append({"id": issue_id, "error": e.detail})

    return {"count": len(results), "issues": results}
