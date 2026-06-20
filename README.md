# BondView - 债券行情聚合系统

面向债券交易员的多源行情聚合平台，接入银行间市场xBond、货币经纪商、交易所、收益互换、国债期货等多个行情源，将相同债券的行情数据整合展示。

## 🛠 技术栈

- **Frontend**: Vue 3 + TypeScript + Ant Design Vue 4.x + Tailwind CSS + ECharts
- **Backend**: Python FastAPI + SQLAlchemy 2.0 + Pydantic
- **Database**: PostgreSQL 15 + Redis 7
- **Containerization**: Docker + Docker Compose

## 🚀 启动指南 (How to Run)

1. 确保 Docker Desktop 已启动
2. 在根目录执行：
   ```bash
   docker compose up --build
   ```
3. 等待容器启动完成（首次构建约 3-5 分钟）
4. 系统会自动创建数据库表并填充演示数据

## 🔗 服务地址 (Services)

- **Frontend**: http://localhost:3000
- **Backend Swagger**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: bondview / pass: bondview123 / db: bondview)
- **Redis**: localhost:6379

## 🧪 测试账号

| 角色 | 用户名 | 密码 |
|:---|:---|:---|
| 管理员 | admin | 123456 |
| 交易员 | trader | 123456 |
| 交易员 | trader2 | 123456 |
| 只读用户 | viewer | 123456 |

## 📋 功能特性

### 核心功能
- **行情看板**: 全市场概览、收益率曲线、热门债券排行、异动提醒
- **聚合行情**: 多源报价整合展示、最优价高亮、债券搜索筛选
- **债券详情**: 单券多源对比、各源报价明细、成交记录
- **成交记录**: 全市场成交流水、成交统计分析
- **国债期货**: T/TF/TS 合约行情、基差分析
- **收益互换**: 场外衍生品交易商报价汇总
- **我的关注**: 自定义债券收藏列表

### 行情源接入
| 行情源 | 数据类型 |
|:---|:---|
| 银行间xBond | 报价 + 成交 |
| 中诚宝捷思 | 报价 + 成交 |
| 平安利顺 | 报价 + 成交 |
| 上海国利 | 报价 + 成交 |
| 上交所 / 深交所 | 报价 + 成交 |
| 收益互换 | 报价 |
| 中金所期货 | 行情 |

### 系统管理
- 用户管理（仅管理员）
- 行情源状态监控与控制

## 🏗 项目结构

```
bond-market-aggregator/
├── docker-compose.yml          # 容器编排
├── .dockerignore
├── .gitignore
├── README.md
├── design.md                   # 设计文档
├── frontend/                   # Vue3 前端
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── views/              # 页面组件
│       ├── components/         # 通用组件
│       ├── stores/             # Pinia 状态管理
│       ├── api/                # API 请求层
│       ├── router/             # 路由配置
│       └── utils/              # 工具函数
└── backend/                    # FastAPI 后端
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py             # 入口
        ├── models/             # SQLAlchemy 模型
        ├── schemas/            # Pydantic 数据校验
        ├── api/                # API 路由
        ├── services/           # 业务服务
        └── seed/               # 种子数据
```

## 🐳 Docker 镜像源配置

- Python 依赖：清华大学镜像源
- npm 依赖：淘宝镜像源
- Docker 基础镜像：官方 Docker Hub
