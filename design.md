# 债券行情聚合系统 (BondView) - 设计文档

## 1. 项目概述

### 1.1 项目定位
BondView 是一款面向债券交易员的多源行情聚合系统。系统接入银行间市场、货币经纪商、交易所、场外衍生品市场及中金所等多个行情源，将相同债券的行情数据进行整合展示，帮助交易员在统一视图中快速获取全市场信息，提升交易决策效率。

### 1.2 目标用户
- 银行间市场债券交易员
- 券商固定收益部交易员
- 基金公司债券投资经理
- 保险资管债券交易人员

---

## 2. 功能需求

### 2.1 行情源接入

| 行情源 | 数据类型 | 数据内容 |
|:---|:---|:---|
| **银行间市场 xBond** | 报价 + 成交 | 买卖价、收益率、面额、对手方、成交价、成交量 |
| **货币经纪商** | 报价 + 成交 | 经纪商名称、买卖报价、最优价、成交记录 |
| **交易所 (上交所/深交所)** | 报价 + 成交 | 盘口数据、最新价、涨跌幅、成交量、成交额 |
| **场外衍生品 (收益互换)** | 报价 | 交易商名称、互换利率、期限、标的债券 |
| **中金所 (国债期货)** | 行情 | 合约代码、最新价、持仓量、结算价、基差 |

### 2.2 核心功能模块

#### 2.2.1 行情看板 (Dashboard)
- **全市场概览**：展示债券市场关键指标（国债收益率曲线、利率互换曲线、市场成交量统计）
- **热门债券排行**：按成交量/成交额排序的热门债券
- **行情异动提醒**：价格波动超过阈值的债券高亮提示

#### 2.2.2 债券行情聚合 (核心)
- **统一搜索**：按债券代码、简称、发行人进行搜索
- **多源整合展示**：对同一债券，将所有行情源的数据聚合到同一视图
  - 横向对比各源报价差异
  - 高亮最优买卖价
  - 展示各源最新成交
- **行情明细**：点击债券可查看详细的多源行情数据
  - xBond 报价列表
  - 经纪商报价列表
  - 交易所实时行情
  - 收益互换报价
  - 关联国债期货行情

#### 2.2.3 债券信息管理
- **债券基本信息**：代码、简称、发行人、期限、票面利率、信用评级等
- **债券分类筛选**：按品种（国债/金融债/企业债/可转债）、期限、评级等筛选
- **债券收藏夹**：交易员可自定义关注债券列表

#### 2.2.4 成交记录
- **全市场成交流水**：各行情源的成交数据汇总展示
- **按债券查看成交**：查看特定债券在各市场的成交历史
- **成交统计**：成交量/成交额的时间维度统计图表

#### 2.2.5 国债期货模块
- **实时合约行情**：T、TF、TS 合约实时行情
- **基差分析**：最便宜可交割券 (CTD) 及基差走势
- **持仓分析**：多空持仓变动

#### 2.2.6 系统管理
- **用户管理**：交易员账号管理、角色权限
- **行情源管理**：行情源连接状态监控、开关控制
- **系统配置**：预警阈值设置、显示偏好

---

## 3. 技术架构

### 3.1 技术栈选型

| 层次 | 技术选型 | 说明 |
|:---|:---|:---|
| **前端框架** | Vue 3 + TypeScript | 用户指定，Composition API |
| **UI 组件库** | Ant Design Vue 4.x | 专业金融级组件库 |
| **CSS 框架** | Tailwind CSS 3.x | 快速样式开发 |
| **状态管理** | Pinia | Vue 3 官方推荐状态管理 |
| **图表库** | ECharts 5.x | 收益率曲线、成交统计可视化 |
| **实时通信** | WebSocket | 行情数据实时推送 |
| **后端框架** | Python FastAPI | 高性能异步框架，适合实时数据处理 |
| **ORM** | SQLAlchemy 2.0 | Python 主流 ORM |
| **数据库** | PostgreSQL 15 | 结构化行情数据存储 |
| **缓存** | Redis 7 | 实时行情缓存、WebSocket 消息队列 |
| **容器化** | Docker + Docker Compose | 100% 容器化交付 |

### 3.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│                    Vue3 + AntD + Tailwind                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ 行情看板  │ │ 聚合行情  │ │ 成交记录  │ │ 国债期货模块  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└──────────────────┬──────────────────┬───────────────────────┘
                   │ HTTP/REST        │ WebSocket
┌──────────────────┴──────────────────┴───────────────────────┐
│                     Nginx 反向代理                           │
└──────────────────┬──────────────────┬───────────────────────┘
                   │                  │
┌──────────────────┴──────────────────┴───────────────────────┐
│                   FastAPI 后端服务                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ 行情接口  │ │ 债券管理  │ │ 用户认证  │ │ WebSocket服务 │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              行情源适配层 (Adapter Pattern)             │   │
│  │  xBond | 经纪商 | 交易所 | 收益互换 | 国债期货          │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
┌──────────┴──────────┐  ┌────────────┴──────────────────────┐
│   PostgreSQL 15     │  │          Redis 7                   │
│  - 债券基本信息      │  │  - 实时行情缓存                     │
│  - 历史行情数据      │  │  - WebSocket 会话管理               │
│  - 成交记录         │  │  - 行情推送队列                     │
│  - 用户信息         │  │                                    │
└─────────────────────┘  └───────────────────────────────────┘
```

### 3.3 数据库设计

#### 核心数据表

**bonds (债券信息表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| code | VARCHAR(20) | 债券代码 |
| name | VARCHAR(100) | 债券简称 |
| full_name | VARCHAR(200) | 债券全称 |
| bond_type | ENUM | 品种(国债/金融债/企业债/可转债/地方债) |
| issuer | VARCHAR(200) | 发行人 |
| issue_date | DATE | 发行日 |
| maturity_date | DATE | 到期日 |
| coupon_rate | DECIMAL(8,4) | 票面利率 |
| coupon_type | ENUM | 付息方式(固定/浮动/零息) |
| face_value | DECIMAL(15,2) | 面值 |
| credit_rating | VARCHAR(10) | 信用评级 |
| remaining_term | DECIMAL(8,4) | 剩余期限(年) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**market_sources (行情源表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| name | VARCHAR(50) | 行情源名称 |
| source_type | ENUM | 类型(xbond/broker/exchange/swap/futures) |
| status | ENUM | 状态(online/offline/error) |
| description | TEXT | 描述 |

**quotes (报价表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| bond_id | UUID | 关联债券 |
| source_id | UUID | 行情源 |
| bid_price | DECIMAL(10,4) | 买入净价 |
| ask_price | DECIMAL(10,4) | 卖出净价 |
| bid_yield | DECIMAL(8,4) | 买入收益率 |
| ask_yield | DECIMAL(8,4) | 卖出收益率 |
| bid_volume | DECIMAL(15,2) | 买入面额(万元) |
| ask_volume | DECIMAL(15,2) | 卖出面额(万元) |
| counterparty | VARCHAR(100) | 对手方/经纪商 |
| quote_time | TIMESTAMP | 报价时间 |
| is_best | BOOLEAN | 是否最优报价 |

**trades (成交表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| bond_id | UUID | 关联债券 |
| source_id | UUID | 行情源 |
| price | DECIMAL(10,4) | 成交净价 |
| yield_rate | DECIMAL(8,4) | 成交收益率 |
| volume | DECIMAL(15,2) | 成交面额(万元) |
| amount | DECIMAL(18,2) | 成交金额(万元) |
| direction | ENUM | 方向(buy/sell) |
| counterparty | VARCHAR(100) | 对手方 |
| trade_time | TIMESTAMP | 成交时间 |

**futures_quotes (国债期货行情表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| contract_code | VARCHAR(20) | 合约代码(如T2406) |
| contract_type | ENUM | 合约类型(T/TF/TS) |
| latest_price | DECIMAL(10,4) | 最新价 |
| settlement_price | DECIMAL(10,4) | 结算价 |
| open_price | DECIMAL(10,4) | 开盘价 |
| high_price | DECIMAL(10,4) | 最高价 |
| low_price | DECIMAL(10,4) | 最低价 |
| volume | INTEGER | 成交量(手) |
| open_interest | INTEGER | 持仓量 |
| basis | DECIMAL(8,4) | 基差 |
| quote_time | TIMESTAMP | 行情时间 |

**swap_quotes (收益互换报价表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| bond_id | UUID | 标的债券 |
| dealer | VARCHAR(100) | 交易商名称 |
| swap_rate | DECIMAL(8,4) | 互换利率 |
| tenor | VARCHAR(20) | 期限 |
| direction | ENUM | 方向(pay_fixed/receive_fixed) |
| notional_min | DECIMAL(18,2) | 最小名义金额 |
| quote_time | TIMESTAMP | 报价时间 |

**users (用户表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| display_name | VARCHAR(50) | 显示名称 |
| role | ENUM | 角色(admin/trader/viewer) |
| department | VARCHAR(100) | 部门 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |

**user_favorites (用户收藏表)**
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| id | UUID | 主键 |
| user_id | UUID | 用户 |
| bond_id | UUID | 债券 |
| created_at | TIMESTAMP | 收藏时间 |

---

## 4. API 设计

### 4.1 RESTful API

#### 认证模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/logout | 用户登出 |
| GET | /api/auth/me | 获取当前用户信息 |

#### 债券模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/bonds | 获取债券列表(分页/筛选/搜索) |
| GET | /api/bonds/{id} | 获取债券详情 |
| GET | /api/bonds/{id}/quotes | 获取某债券的所有行情源报价 |
| GET | /api/bonds/{id}/trades | 获取某债券的成交记录 |
| GET | /api/bonds/{id}/aggregated | 获取某债券的聚合行情(核心) |

#### 行情模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/quotes/latest | 获取最新报价列表 |
| GET | /api/quotes/best | 获取最优报价排行 |
| GET | /api/trades/recent | 获取最近成交列表 |
| GET | /api/trades/statistics | 获取成交统计 |

#### 国债期货模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/futures/contracts | 获取所有合约行情 |
| GET | /api/futures/{code} | 获取单个合约详情 |
| GET | /api/futures/basis | 获取基差分析数据 |

#### 收益互换模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/swaps | 获取收益互换报价列表 |
| GET | /api/swaps/bond/{bond_id} | 获取某债券的互换报价 |

#### 看板模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/dashboard/overview | 获取市场概览数据 |
| GET | /api/dashboard/yield-curve | 获取收益率曲线数据 |
| GET | /api/dashboard/hot-bonds | 获取热门债券排行 |
| GET | /api/dashboard/alerts | 获取行情异动提醒 |

#### 收藏模块
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/favorites | 获取收藏列表 |
| POST | /api/favorites/{bond_id} | 添加收藏 |
| DELETE | /api/favorites/{bond_id} | 取消收藏 |

#### 系统管理
| 方法 | 路径 | 说明 |
|:---|:---|:---|
| GET | /api/admin/sources | 获取行情源状态 |
| PUT | /api/admin/sources/{id} | 更新行情源设置 |
| GET | /api/admin/users | 获取用户列表 |

### 4.2 WebSocket 接口
| 路径 | 说明 |
|:---|:---|
| /ws/quotes | 实时报价推送 |
| /ws/trades | 实时成交推送 |
| /ws/futures | 国债期货行情推送 |
| /ws/alerts | 异动提醒推送 |

---

## 5. 前端页面设计

### 5.1 页面结构

```
├── 登录页 (/login)
├── 主布局
│   ├── 行情看板 (/dashboard)          -- 默认首页
│   ├── 聚合行情 (/market)             -- 核心功能页
│   │   └── 债券详情 (/market/:id)     -- 单券多源聚合详情
│   ├── 成交记录 (/trades)
│   ├── 国债期货 (/futures)
│   ├── 收益互换 (/swaps)
│   ├── 我的关注 (/favorites)
│   └── 系统管理 (/admin)              -- 仅管理员可见
│       ├── 用户管理 (/admin/users)
│       └── 行情源管理 (/admin/sources)
```

### 5.2 UI 设计规范
- **主题色**：深蓝色系 (#1a1a2e → #16213e → #0f3460)，符合金融终端专业感
- **强调色**：买入绿 (#52c41a)、卖出红 (#ff4d4f)
- **字体**：等宽数字字体 (tabular-nums)，确保行情数据对齐
- **布局**：侧边栏导航 + 内容区域，支持全屏模式
- **数据密度**：高信息密度设计，紧凑行距，最大化屏幕利用率

### 5.3 关键交互
- 行情数据闪动效果（价格变动时闪绿/闪红）
- 表格支持列拖拽排序、固定列
- 债券搜索支持模糊匹配和下拉补全
- 支持键盘快捷操作

---

## 6. 项目目录结构

```
bond-market-aggregator/
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── README.md
├── design.md
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router/
│       │   └── index.ts
│       ├── stores/
│       │   ├── auth.ts
│       │   ├── bond.ts
│       │   └── market.ts
│       ├── api/
│       │   ├── index.ts
│       │   ├── auth.ts
│       │   ├── bonds.ts
│       │   ├── quotes.ts
│       │   └── websocket.ts
│       ├── views/
│       │   ├── Login.vue
│       │   ├── Dashboard.vue
│       │   ├── MarketView.vue
│       │   ├── BondDetail.vue
│       │   ├── TradesView.vue
│       │   ├── FuturesView.vue
│       │   ├── SwapsView.vue
│       │   ├── FavoritesView.vue
│       │   └── admin/
│       │       ├── UserManagement.vue
│       │       └── SourceManagement.vue
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppLayout.vue
│       │   │   └── SideMenu.vue
│       │   ├── bond/
│       │   │   ├── BondSearch.vue
│       │   │   ├── BondTable.vue
│       │   │   └── QuoteAggregation.vue
│       │   ├── market/
│       │   │   ├── SourceBadge.vue
│       │   │   ├── PriceCell.vue
│       │   │   └── TradeList.vue
│       │   └── charts/
│       │       ├── YieldCurve.vue
│       │       └── TradeVolume.vue
│       ├── composables/
│       │   ├── useWebSocket.ts
│       │   └── useMarketData.ts
│       └── utils/
│           ├── format.ts
│           └── constants.ts
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── bond.py
│   │   │   ├── quote.py
│   │   │   ├── trade.py
│   │   │   ├── futures.py
│   │   │   ├── swap.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── bond.py
│   │   │   ├── quote.py
│   │   │   ├── trade.py
│   │   │   └── user.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── auth.py
│   │   │   ├── bonds.py
│   │   │   ├── quotes.py
│   │   │   ├── trades.py
│   │   │   ├── futures.py
│   │   │   ├── swaps.py
│   │   │   ├── dashboard.py
│   │   │   ├── favorites.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py
│   │   │   └── websocket.py
│   │   └── seed/
│   │       └── seed_data.py
│   └── entrypoint.sh
└── db/
    └── init.sql
```

---

## 7. 容器化部署

### 7.1 服务编排
| 服务 | 端口 | 说明 |
|:---|:---|:---|
| frontend | 3000:80 | Vue3 + Nginx |
| backend | 8000:8000 | FastAPI |
| db | 5432:5432 | PostgreSQL 15 |
| redis | 6379:6379 | Redis 7 |

### 7.2 数据持久化
- PostgreSQL 数据挂载到 Docker Volume
- Redis 开启 AOF 持久化

### 7.3 服务依赖
- backend 依赖 db 和 redis
- frontend 依赖 backend
- 使用 healthcheck 确保启动顺序

---

## 8. 安全设计

- JWT Token 认证，Token 有效期 24 小时
- 密码使用 bcrypt 加密存储
- API 接口统一鉴权中间件
- SQL 注入防护（ORM + 参数化查询）
- CORS 配置白名单
- 输入校验（Pydantic Schema）

---

## 9. 种子数据设计

系统启动时自动填充以下演示数据：
- **20+ 只债券**：覆盖国债、政金债、企业债、可转债等品种
- **5 个行情源**：xBond、中诚宝捷思、交易所、收益互换、中金所
- **200+ 条报价数据**：每只债券在多个行情源有报价
- **100+ 条成交记录**：模拟真实成交流水
- **国债期货合约**：T、TF、TS 各主力合约行情
- **收益互换报价**：主流交易商的互换报价
- **2 个测试账号**：admin/123456 (管理员), trader/123456 (交易员)
