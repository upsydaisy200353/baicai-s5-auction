# 白菜 S5 选手拍卖

基于名单与拍卖规则的演示程序，包含 **SQLite / PostgreSQL 数据库**、**FastAPI 后端**、**Vue 3 网页**。

## 快速启动（网页 + 数据库）

**终端 1 — 后端 API**

```bash
cd server
pip install -r requirements.txt
python seed.py          # 首次写入默认名单（可选）
python main.py          # http://127.0.0.1:8000
```

**终端 2 — 前端**

```bash
cd frontend
npm install
npm run dev             # http://localhost:5173
```

### 页面

| 路径 | 说明 |
|------|------|
| `/` | 选人仪式（需登录） |
| `/spectator` | 观战大屏（无需登录） |
| `/admin` | 名单管理（仅管理员） |
| `/login` | 登录 |

### 登录

选择管理员或队长身份，**免密**一键进入。

| 角色 | 用户名 |
|------|--------|
| 管理员 | `admin` |
| 队长 | `wuyanzu` / `yazi` / `caps` / …（见登录页列表） |

首次启动会自动创建账号（`seed_users.py`）。新增队长时会自动创建对应登录账号。

环境变量 `AUCTION_JWT_SECRET` 用于 JWT 签名（生产环境请设置强密钥）。

## 拍卖规则（网页版）

| 规则 | 说明 |
|------|------|
| 竞拍方式 | **公开同时叫价**，价高者得 |
| 最低加价 | 每次至少 **10w** |
| 加价倒计时 | 有人出价后 **45s** 内无人继续加价则落槌（管理员可调） |
| 流拍 | 全程 **60s** 无人出价则流拍（管理员可调） |
| 一口价 | 每位队长整场仪式仅可使用 **一次** |
| 同位置限制 | 队长本人位置或已有该位置选手时，不参与该位置拍卖 |
| 资金可见性 | 管理员可见全部资金；队长仅可见自己 |
| 全员放弃 | 所有可竞拍队长放弃后，立即流拍 |

## 数据持久化

- **名单 / 账号**：本地 `server/auction.db`，或线上 PostgreSQL（`DATABASE_URL`）
- **拍卖进度**：仪式进行中会自动写入 `auction_state` 表，服务重启后可恢复（需 PostgreSQL 或 SQLite 均可）

线上部署请设置与 BidKing 相同的 `DATABASE_URL`，本系统使用独立表 `baicai_roster`、`baicai_users`、`baicai_auction_state`。

## 部署（Render）

1. 推送代码到 GitHub
2. Render Dashboard → **New** → **Blueprint** → 连接仓库
3. 配置环境变量：
   - `DATABASE_URL` — Neon PostgreSQL 连接串（**强烈建议**）
   - `AUCTION_JWT_SECRET` — 由 Blueprint 自动生成
   - `CORS_ORIGINS` — 可选，默认含 localhost 与 onrender.com 域名

在线地址：**https://baicai-s5-auction.onrender.com**

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户名登录（免密） |
| GET | `/api/auction/state` | 拍卖状态（需登录） |
| GET | `/api/auction/spectator` | 观战状态（公开） |
| GET | `/api/meta` | 元数据（含是否仪式进行中） |
| GET | `/api/roster` | 名单（需登录，非管理员隐藏资金） |

仪式进行中，名单增删改会被拒绝。

## 测试

```bash
cd server
pytest tests/ -q
```

## 命令行版（历史演示）

根目录 `auction.py` / `data.py` 为旧的**轮流密封竞价**演示，与网页公开叫价规则不同：

```bash
python main.py roster
python main.py
```

## 文件结构

```
├── server/
│   ├── main.py              # FastAPI
│   ├── auction_engine.py    # 公开叫价引擎
│   ├── db.py                # SQLite / PostgreSQL
│   ├── seed_users.py        # 账号与房间口令
│   └── tests/
└── frontend/
    ├── src/views/AuctionView.vue
    ├── src/views/SpectatorView.vue
    └── src/views/RosterAdmin.vue
```
