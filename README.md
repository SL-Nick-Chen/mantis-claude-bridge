# Mantis Proxy — Railway 部署說明

## 部署步驟

### 1. 上傳到 GitHub
把這個資料夾（`main.py`、`requirements.txt`、`Procfile`）推到一個 GitHub repo。

### 2. 在 Railway 建立新專案
1. 前往 [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo → 選擇你的 repo
3. Railway 會自動偵測並部署

### 3. 設定環境變數（重要！）
在 Railway 的 Variables 頁面設定以下三個環境變數：

| 變數名稱 | 值 | 說明 |
|---|---|---|
| `MANTIS_URL` | `https://mantis.cloud.softleader.com.tw` | Mantis 主機網址 |
| `MANTIS_API_KEY` | `你的 Mantis API Key` | Mantis 認證 token |
| `PROXY_SECRET` | `自訂一個隨機字串` | 保護這個 proxy 的密碼，給 Claude 用 |

> `PROXY_SECRET` 可以用任意字串，例如 `my-secret-2026`，之後告訴 Claude 這個值。

### 4. 取得網址
部署完成後，Railway 會給一個網址，格式如：
```
https://mantis-proxy-xxxx.railway.app
```

### 5. 告訴 Claude
把以下資訊提供給 Claude：
- **網址**：`https://mantis-proxy-xxxx.railway.app`
- **PROXY_SECRET**：你設定的值

---

## API 使用方式

### 查詢單一問題單
```
GET /issues/36720
Header: Authorization: Bearer <PROXY_SECRET>
```

### 批次查詢多個問題單
```
GET /issues?issue_ids=36720,35923,34955
Header: Authorization: Bearer <PROXY_SECRET>
```

### 健康檢查
```
GET /
```
回傳 `{"status": "ok"}` 代表服務正常運作。
