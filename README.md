# 白菜 S5 选手拍卖 Demo

基于名单与拍卖规则的演示程序，包含 **SQLite 数据库**、**FastAPI 后端**、**Vue 3 网页** 和 **Python 命令行**。

## 快速启动（网页 + 数据库）

**终端 1 — 后端 API（SQLite）**

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

- **选人仪式** `/` — 需登录；队长在轮到自己时出价，管理员主持流程
- **名单管理** `/admin` — 仅管理员可访问
- **登录页** `/login` — 选择管理员或队长身份，**免密**一键进入

### 登录身份

| 角色 | 用户名 |
|------|--------|
| 管理员 | `admin` |
| 队长 | `wuyanzu` / `yazi` / `caps` / `baiweiyi` / `mushroom` / `xxts` / `yume` / `pika` |

队长进入后可在密封出价阶段提交自己的出价；管理员可主持全流程，并代队长操作，便于单人模拟。

首次启动后端会自动创建账号（`seed_users.py`）；若需重置账号可执行 `python seed_users.py`。

数据库文件：`server/auction.db`（本地开发，永久保存）。

线上部署（Render）默认使用容器内 SQLite，**服务重启后数据会丢失**。要与 [BidKing](https://github.com/upsydaisy200353/bidking) 共用 Neon PostgreSQL 持久化，在 Render 环境变量中设置与 BidKing 相同的 `DATABASE_URL`；本系统会在同一库中自动创建 `baicai_roster`、`baicai_users` 表（与 BidKing 的 `bidking_*` 表互不干扰）。

## 部署（Render）

仓库根目录包含 `Dockerfile` 与 `render.yaml`，单服务同时提供 API 与前端静态页。

1. 将仓库推送到 GitHub
2. 在 [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint** → 连接仓库
3. 部署完成后访问 https://baicai-s5-auction.onrender.com

环境变量 `AUCTION_JWT_SECRET` 由 Blueprint 自动生成。

在线地址：**https://baicai-s5-auction.onrender.com**  
GitHub：**https://github.com/upsydaisy200353/baicai-s5-auction**

## 名单管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/roster` | 获取完整名单（含拍卖用 players/captains） |
| GET | `/api/roster/entries` | 获取全部条目 |
| POST | `/api/roster/entries` | 新增条目 |
| PUT | `/api/roster/entries/{id}` | 更新条目 |
| DELETE | `/api/roster/entries/{id}` | 删除条目 |
| POST | `/api/roster/reseed` | 恢复默认名单 |

### 数据字段

| 字段 | 选手 | 队长 |
|------|------|------|
| identity | `player` | `captain` |
| serial | A1、B2… | — |
| poolLetter | A~E（上/野/中/下/辅） | A~E |
| startPrice | 起拍价 | 实力分 |
| buyoutPrice | 一口价 | — |
| funds | — | 竞拍资金 |
| sortOrder | 表格展示顺序 | 表格展示顺序 |

**队长不会被拍卖**，仅参与竞价。

## 命令行版（Python，读取 data.py）

```bash
python main.py roster
python main.py          # 自动模拟
python main.py interactive
```

## 规则实现

| 规则 | 说明 |
|------|------|
| 位置池 A~E | 上单 / 打野 / 中单 / 下路 / 辅助 |
| 位置池选择 | 管理员确定 A~E 五个池的拍卖顺序 |
| 同位置限制 | 队长本人位置或已有该位置选手时，不参与该位置拍卖 |
| 出价顺序 | 管理员可设定；未设定时首轮实力强→弱，后续资金少→多 |
| 竞拍方式 | 英式增价拍卖，队长输入出价或快捷加价 |
| 出价规则 | 须为 10 的倍数；高于当前价且满足最低加价（10~100w） |
| 放弃规则 | 放弃后不再参与该选手的后续轮次；其余人均放弃时落槌 |
| 落槌 | 一轮内无人加价 → 最高价者胜出；无人出价 → 流拍 |

## 文件结构

```
├── data.py                 # 命令行默认名单
├── auction.py / main.py
├── server/
│   ├── main.py             # FastAPI
│   ├── db.py               # SQLite
│   ├── seed.py             # 初始名单
│   ├── seed_users.py       # 管理员 + 队长账号
│   ├── auth.py             # JWT 登录
│   ├── auction_engine.py   # 服务端拍卖状态
│   └── auction.db          # 数据库（运行后生成）
└── frontend/
    ├── src/views/AuctionView.vue
    ├── src/views/RosterAdmin.vue
    ├── src/api/roster.ts
    └── src/auctionEngine.ts
```
