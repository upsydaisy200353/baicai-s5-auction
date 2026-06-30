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
- **登录页** `/login` — 管理员 + 8 位队长账号

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| 队长 | `wuyanzu` / `yazi` / `caps` / `baiweiyi` / `mushroom` / `xxts` / `yume` / `pika` | `captain123` |

队长登录后可在**轮到自己时**出价；管理员可主持全流程，并在竞价阶段**代当前轮次队长**加价/一口价/放弃，便于单人模拟。

首次启动后端会自动创建账号（`seed_users.py`）；若需重置账号可执行 `python seed_users.py`。

数据库文件：`server/auction.db`（本地开发）。Render 部署使用容器内 SQLite，重启后数据会重置。

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
| 同位置限制 | 队长已有该位置选手时，不再参与该位置拍卖 |
| 出价顺序 | 管理员可设定；未设定时首轮实力强→弱，后续资金少→多 |
| 选手抽取 | 从当前池随机抽取（不含队长） |
| 首轮出价 | 实力强 → 弱 |
| 后续轮次 | 资金少 → 多 |
| 加价幅度 | 10w ~ 100w |
| 一口价 | 仅首轮可用 |

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
