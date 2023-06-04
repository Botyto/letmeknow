import sqlalchemy.orm


class Model(sqlalchemy.orm.DeclarativeBase):
    pass

connection_str = "sqlite:///test.db"
engine = sqlalchemy.create_engine(connection_str, pool_recycle=1800)
sessionmaker = sqlalchemy.orm.sessionmaker(engine)
