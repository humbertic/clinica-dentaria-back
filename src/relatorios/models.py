from sqlalchemy import Table, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine
from src.database import engine, Base

# usar engine síncrono se estiver em modo async
reflect_engine = engine.sync_engine if isinstance(engine, AsyncEngine) else engine
metadata_obj = MetaData()

# ------------------------------------------------------------------------
class RevenueSummary(Base):
    __table__ = Table("vw_revenue_summary", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {"primary_key": [__table__.c.dia]}

class TopServices(Base):
    __table__ = Table("vw_top_services", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {"primary_key": [__table__.c.servico]}

class CashShift(Base):
    __table__ = Table("vw_cash_shift", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {"primary_key": [__table__.c.session_id]}

class OverdueInstallment(Base):
    __table__ = Table("vw_overdue_installments", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {"primary_key": [__table__.c.parcela_id]}

class StockCritical(Base):
    __table__ = Table("vw_stock_critical", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {"primary_key": [__table__.c.id]}

class ProductivityClinical(Base):
    __table__ = Table("vw_productivity_clinical", metadata_obj, autoload_with=reflect_engine)
    __mapper_args__ = {                    # chave composta
        "primary_key": [
            __table__.c.mes,
            __table__.c.medico_id
        ]
    }
