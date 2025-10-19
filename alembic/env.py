import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Caminho absoluto para o diretório do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importa a Base e os modelos
from src.database import Base
from src.utilizadores import models as utilizadores_models  
from src.perfis import models as perfis_models  
from src.auditoria import models as auditoria_models  
from src.clinica import models as clinica_models
from src.stock import models as stock_models
from src.pacientes import models as pacientes_models
from src.categoria import models as categoria_models
from src.entidades import models as entidades_models
from src.artigos import models as artigos_models
from src.precos import models as precos_models
from src.dentes import models as dentes_models
from src.orcamento import models as orcamento_models
from src.marcacoes import models as marcacoes_models
from src.consultas import models as consultas_models
from src.faturacao import models as faturacao_models
from src.caixa import models as caixa_models
from src.mensagens import models as mensagens_models

# Carrega a config do .ini
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# METADATA usada para autogeração
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use DATABASE_URL environment variable if available
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
