import uuid
import random
from datetime import datetime, timedelta, date

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.bond import Bond, MarketSource
from app.models.quote import Quote
from app.models.trade import Trade
from app.models.futures import FuturesQuote
from app.models.swap import SwapQuote
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_all(db: AsyncSession):
    existing = await db.execute(select(User).limit(1))
    if existing.scalar_one_or_none():
        logger.info("数据库已有数据，跳过种子填充")
        return

    logger.info("开始填充种子数据...")

    users = await seed_users(db)
    sources = await seed_sources(db)
    bonds = await seed_bonds(db)
    await db.flush()

    await seed_quotes(db, bonds, sources)
    await seed_trades(db, bonds, sources)
    await seed_futures(db)
    await seed_swaps(db, bonds)
    await db.flush()
    await db.commit()

    logger.info("种子数据填充完成")


async def seed_users(db: AsyncSession) -> list[User]:
    users_data = [
        {"username": "admin", "password": "123456", "display_name": "系统管理员", "role": "admin", "department": "信息技术部"},
        {"username": "trader", "password": "123456", "display_name": "张伟", "role": "trader", "department": "固定收益部"},
        {"username": "trader2", "password": "123456", "display_name": "李明", "role": "trader", "department": "资金交易部"},
        {"username": "viewer", "password": "123456", "display_name": "王芳", "role": "viewer", "department": "风险管理部"},
    ]
    users = []
    for u in users_data:
        user = User(
            username=u["username"],
            password_hash=pwd_context.hash(u["password"]),
            display_name=u["display_name"],
            role=u["role"],
            department=u["department"],
        )
        db.add(user)
        users.append(user)
    return users


async def seed_sources(db: AsyncSession) -> list[MarketSource]:
    sources_data = [
        {"name": "银行间xBond", "source_type": "xbond", "description": "银行间市场xBond交易系统报价与成交数据"},
        {"name": "中诚宝捷思", "source_type": "broker", "description": "中诚宝捷思货币经纪公司报价与成交数据"},
        {"name": "平安利顺", "source_type": "broker", "description": "平安利顺国际货币经纪公司报价与成交数据"},
        {"name": "上海国利", "source_type": "broker", "description": "上海国利货币经纪有限公司报价与成交数据"},
        {"name": "上交所", "source_type": "exchange", "description": "上海证券交易所债券行情数据"},
        {"name": "深交所", "source_type": "exchange", "description": "深圳证券交易所债券行情数据"},
        {"name": "收益互换", "source_type": "swap", "description": "场外衍生品交易商债券收益互换报价"},
        {"name": "中金所期货", "source_type": "futures", "description": "中国金融期货交易所国债期货行情"},
    ]
    sources = []
    for s in sources_data:
        source = MarketSource(**s, status="online")
        db.add(source)
        sources.append(source)
    return sources


async def seed_bonds(db: AsyncSession) -> list[Bond]:
    bonds_data = [
        {"code": "240004.IB", "name": "24附息国债04", "full_name": "2024年记账式附息(四期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 2.2850, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 9.5, "issue_date": date(2024, 3, 20), "maturity_date": date(2034, 3, 20)},
        {"code": "240006.IB", "name": "24附息国债06", "full_name": "2024年记账式附息(六期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 2.5700, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 29.8, "issue_date": date(2024, 5, 20), "maturity_date": date(2054, 5, 20)},
        {"code": "240010.IB", "name": "24附息国债10", "full_name": "2024年记账式附息(十期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 2.1200, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 4.8, "issue_date": date(2024, 6, 15), "maturity_date": date(2029, 6, 15)},
        {"code": "240015.IB", "name": "24附息国债15", "full_name": "2024年记账式附息(十五期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 1.9200, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 2.3, "issue_date": date(2024, 8, 10), "maturity_date": date(2027, 2, 10)},
        {"code": "240205.IB", "name": "24国开05", "full_name": "国家开发银行2024年第五期金融债", "bond_type": "政金债", "issuer": "国家开发银行", "coupon_rate": 2.4600, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 9.6, "issue_date": date(2024, 4, 18), "maturity_date": date(2034, 4, 18)},
        {"code": "240210.IB", "name": "24国开10", "full_name": "国家开发银行2024年第十期金融债", "bond_type": "政金债", "issuer": "国家开发银行", "coupon_rate": 2.3500, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 4.7, "issue_date": date(2024, 7, 22), "maturity_date": date(2029, 7, 22)},
        {"code": "240302.IB", "name": "24进出02", "full_name": "中国进出口银行2024年第二期金融债", "bond_type": "政金债", "issuer": "中国进出口银行", "coupon_rate": 2.5100, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 9.3, "issue_date": date(2024, 5, 15), "maturity_date": date(2034, 5, 15)},
        {"code": "240405.IB", "name": "24农发05", "full_name": "中国农业发展银行2024年第五期金融债", "bond_type": "政金债", "issuer": "中国农业发展银行", "coupon_rate": 2.3800, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 6.8, "issue_date": date(2024, 6, 20), "maturity_date": date(2031, 6, 20)},
        {"code": "2480006.IB", "name": "24华能集MTN001", "full_name": "华能国际电力股份有限公司2024年度第一期中期票据", "bond_type": "企业债", "issuer": "华能国际电力", "coupon_rate": 2.8500, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 2.8, "issue_date": date(2024, 3, 8), "maturity_date": date(2027, 3, 8)},
        {"code": "2480012.IB", "name": "24中石油MTN002", "full_name": "中国石油天然气集团有限公司2024年度第二期中期票据", "bond_type": "企业债", "issuer": "中国石油", "coupon_rate": 2.6200, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 4.5, "issue_date": date(2024, 4, 12), "maturity_date": date(2029, 4, 12)},
        {"code": "2480018.IB", "name": "24国电投MTN003", "full_name": "国家电力投资集团有限公司2024年度第三期中期票据", "bond_type": "企业债", "issuer": "国电投集团", "coupon_rate": 2.7800, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 3.2, "issue_date": date(2024, 5, 22), "maturity_date": date(2027, 10, 22)},
        {"code": "113050.SH", "name": "南银转债", "full_name": "南京银行股份有限公司可转换公司债券", "bond_type": "可转债", "issuer": "南京银行", "coupon_rate": 0.4000, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 3.5, "issue_date": date(2021, 7, 1), "maturity_date": date(2027, 7, 1)},
        {"code": "127085.SZ", "name": "中金转债", "full_name": "中金黄金股份有限公司可转换公司债券", "bond_type": "可转债", "issuer": "中金黄金", "coupon_rate": 0.3000, "coupon_type": "固定利率", "credit_rating": "AA+", "remaining_term": 4.2, "issue_date": date(2022, 4, 1), "maturity_date": date(2028, 4, 1)},
        {"code": "2480025.IB", "name": "24万科MTN001", "full_name": "万科企业股份有限公司2024年度第一期中期票据", "bond_type": "公司债", "issuer": "万科企业", "coupon_rate": 3.4500, "coupon_type": "固定利率", "credit_rating": "AA+", "remaining_term": 2.1, "issue_date": date(2024, 2, 15), "maturity_date": date(2026, 8, 15)},
        {"code": "230215.IB", "name": "23地方债广东15", "full_name": "2023年广东省政府一般债券(十五期)", "bond_type": "地方债", "issuer": "广东省财政厅", "coupon_rate": 2.6800, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 6.5, "issue_date": date(2023, 9, 20), "maturity_date": date(2030, 9, 20)},
        {"code": "230220.IB", "name": "23地方债浙江20", "full_name": "2023年浙江省政府专项债券(二十期)", "bond_type": "地方债", "issuer": "浙江省财政厅", "coupon_rate": 2.7200, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 8.2, "issue_date": date(2023, 10, 15), "maturity_date": date(2033, 10, 15)},
        {"code": "112345.SH", "name": "24同业存单AAA01", "full_name": "工商银行2024年第一期同业存单", "bond_type": "同业存单", "issuer": "中国工商银行", "coupon_rate": 2.1000, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 0.5, "issue_date": date(2024, 7, 1), "maturity_date": date(2025, 1, 1)},
        {"code": "112346.SH", "name": "24同业存单AAA02", "full_name": "建设银行2024年第二期同业存单", "bond_type": "同业存单", "issuer": "中国建设银行", "coupon_rate": 2.0800, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 0.8, "issue_date": date(2024, 6, 15), "maturity_date": date(2025, 3, 15)},
        {"code": "240001.IB", "name": "24贴现国债01", "full_name": "2024年记账式贴现(一期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 0, "coupon_type": "贴现", "credit_rating": "AAA", "remaining_term": 0.25, "issue_date": date(2024, 1, 10), "maturity_date": date(2024, 4, 10)},
        {"code": "240008.IB", "name": "24附息国债08", "full_name": "2024年记账式附息(八期)国债", "bond_type": "国债", "issuer": "财政部", "coupon_rate": 2.3600, "coupon_type": "固定利率", "credit_rating": "AAA", "remaining_term": 6.9, "issue_date": date(2024, 6, 1), "maturity_date": date(2031, 6, 1)},
    ]

    bonds = []
    for b in bonds_data:
        bond = Bond(**b)
        db.add(bond)
        bonds.append(bond)
    return bonds


async def seed_quotes(db: AsyncSession, bonds: list[Bond], sources: list[MarketSource]):
    now = datetime.utcnow()
    xbond_sources = [s for s in sources if s.source_type == "xbond"]
    broker_sources = [s for s in sources if s.source_type == "broker"]
    exchange_sources = [s for s in sources if s.source_type == "exchange"]

    counterparties_xbond = ["中国银行", "工商银行", "建设银行", "农业银行", "交通银行", "招商银行", "兴业银行", "民生银行", "中信银行", "浦发银行"]

    for bond in bonds:
        base_price = float(bond.coupon_rate or 2.5) * 40 + random.uniform(90, 105)
        base_yield = float(bond.coupon_rate or 2.5) + random.uniform(-0.3, 0.3)

        for src in xbond_sources:
            for i in range(random.randint(3, 8)):
                spread = random.uniform(0.01, 0.08)
                q = Quote(
                    bond_id=bond.id,
                    source_id=src.id,
                    bid_price=round(base_price - spread, 4),
                    ask_price=round(base_price + spread, 4),
                    bid_yield=round(base_yield + spread * 0.5, 4),
                    ask_yield=round(base_yield - spread * 0.5, 4),
                    bid_volume=round(random.uniform(500, 50000), 2),
                    ask_volume=round(random.uniform(500, 50000), 2),
                    counterparty=random.choice(counterparties_xbond),
                    quote_time=now - timedelta(minutes=random.randint(1, 480)),
                    is_best=(i == 0),
                )
                db.add(q)

        for src in broker_sources:
            for i in range(random.randint(2, 5)):
                spread = random.uniform(0.02, 0.10)
                q = Quote(
                    bond_id=bond.id,
                    source_id=src.id,
                    bid_price=round(base_price - spread + random.uniform(-0.05, 0.05), 4),
                    ask_price=round(base_price + spread + random.uniform(-0.05, 0.05), 4),
                    bid_yield=round(base_yield + spread * 0.4, 4),
                    ask_yield=round(base_yield - spread * 0.4, 4),
                    bid_volume=round(random.uniform(1000, 30000), 2),
                    ask_volume=round(random.uniform(1000, 30000), 2),
                    counterparty=src.name,
                    quote_time=now - timedelta(minutes=random.randint(1, 480)),
                    is_best=(i == 0),
                )
                db.add(q)

        if bond.code.endswith(".SH") or bond.code.endswith(".SZ"):
            for src in exchange_sources:
                spread = random.uniform(0.01, 0.05)
                q = Quote(
                    bond_id=bond.id,
                    source_id=src.id,
                    bid_price=round(base_price - spread, 4),
                    ask_price=round(base_price + spread, 4),
                    bid_yield=round(base_yield + spread * 0.3, 4),
                    ask_yield=round(base_yield - spread * 0.3, 4),
                    bid_volume=round(random.uniform(100, 10000), 2),
                    ask_volume=round(random.uniform(100, 10000), 2),
                    counterparty="交易所匿名",
                    quote_time=now - timedelta(minutes=random.randint(1, 240)),
                    is_best=True,
                )
                db.add(q)


async def seed_trades(db: AsyncSession, bonds: list[Bond], sources: list[MarketSource]):
    now = datetime.utcnow()
    counterparties = ["中国银行", "工商银行", "建设银行", "农业银行", "招商银行", "中信证券", "国泰君安", "华泰证券", "广发证券", "中金公司"]

    tradable_sources = [s for s in sources if s.source_type in ("xbond", "broker", "exchange")]

    for bond in bonds:
        base_price = float(bond.coupon_rate or 2.5) * 40 + random.uniform(90, 105)
        base_yield = float(bond.coupon_rate or 2.5) + random.uniform(-0.3, 0.3)

        for _ in range(random.randint(3, 10)):
            src = random.choice(tradable_sources)
            price = round(base_price + random.uniform(-0.2, 0.2), 4)
            vol = round(random.uniform(500, 80000), 2)
            t = Trade(
                bond_id=bond.id,
                source_id=src.id,
                price=price,
                yield_rate=round(base_yield + random.uniform(-0.1, 0.1), 4),
                volume=vol,
                amount=round(price * vol / 100, 2),
                direction=random.choice(["buy", "sell"]),
                counterparty=random.choice(counterparties),
                trade_time=now - timedelta(minutes=random.randint(1, 1440)),
            )
            db.add(t)


async def seed_futures(db: AsyncSession):
    now = datetime.utcnow()
    contracts = [
        {"code": "T2406", "type": "T", "price": 103.685, "settle": 103.620, "open": 103.550, "high": 103.750, "low": 103.480, "prev": 103.600, "vol": 85432, "oi": 215678, "basis": 0.235},
        {"code": "T2409", "type": "T", "price": 103.420, "settle": 103.380, "open": 103.300, "high": 103.500, "low": 103.250, "prev": 103.360, "vol": 42156, "oi": 128945, "basis": 0.185},
        {"code": "T2412", "type": "T", "price": 103.150, "settle": 103.100, "open": 103.050, "high": 103.230, "low": 102.980, "prev": 103.080, "vol": 18765, "oi": 67234, "basis": 0.142},
        {"code": "TF2406", "type": "TF", "price": 102.325, "settle": 102.280, "open": 102.200, "high": 102.380, "low": 102.150, "prev": 102.270, "vol": 35678, "oi": 89456, "basis": 0.168},
        {"code": "TF2409", "type": "TF", "price": 102.080, "settle": 102.050, "open": 101.980, "high": 102.150, "low": 101.920, "prev": 102.040, "vol": 15234, "oi": 45678, "basis": 0.125},
        {"code": "TS2406", "type": "TS", "price": 101.485, "settle": 101.450, "open": 101.400, "high": 101.520, "low": 101.370, "prev": 101.440, "vol": 28945, "oi": 72345, "basis": 0.098},
        {"code": "TS2409", "type": "TS", "price": 101.320, "settle": 101.290, "open": 101.250, "high": 101.380, "low": 101.220, "prev": 101.280, "vol": 12345, "oi": 38912, "basis": 0.076},
    ]

    for c in contracts:
        fq = FuturesQuote(
            contract_code=c["code"],
            contract_type=c["type"],
            latest_price=c["price"],
            settlement_price=c["settle"],
            open_price=c["open"],
            high_price=c["high"],
            low_price=c["low"],
            prev_close=c["prev"],
            change_pct=round((c["price"] - c["prev"]) / c["prev"] * 100, 4),
            volume=c["vol"],
            open_interest=c["oi"],
            basis=c["basis"],
            quote_time=now - timedelta(minutes=random.randint(1, 60)),
        )
        db.add(fq)


async def seed_swaps(db: AsyncSession, bonds: list[Bond]):
    now = datetime.utcnow()
    dealers = ["中信证券", "中金公司", "高盛高华", "摩根大通", "瑞银证券", "中银国际"]
    tenors = ["3M", "6M", "1Y", "2Y", "3Y", "5Y"]

    selected_bonds = [b for b in bonds if b.bond_type in ("国债", "政金债")][:8]

    for bond in selected_bonds:
        for _ in range(random.randint(2, 4)):
            sq = SwapQuote(
                bond_id=bond.id,
                dealer=random.choice(dealers),
                swap_rate=round(float(bond.coupon_rate or 2.5) + random.uniform(-0.3, 0.5), 4),
                tenor=random.choice(tenors),
                direction=random.choice(["pay_fixed", "receive_fixed"]),
                notional_min=random.choice([1000, 2000, 5000, 10000]),
                quote_time=now - timedelta(minutes=random.randint(1, 720)),
            )
            db.add(sq)
