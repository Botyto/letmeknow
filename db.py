import os
import sqlalchemy.orm


class Model(sqlalchemy.orm.DeclarativeBase):
    pass

os.makedirs("data", exist_ok=True)
connection_str = "sqlite:///data/test.db"
engine = sqlalchemy.create_engine(connection_str, pool_recycle=1800)
sessionmaker = sqlalchemy.orm.sessionmaker(engine)
