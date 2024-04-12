from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import ForeignKey

Base = declarative_base()


class Record(Base):
    __tablename__ = 'record'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    chat_id: Mapped[int] = mapped_column(ForeignKey('group.id'))
    day: Mapped[int]
    hour: Mapped[int]
    count: Mapped[int] = mapped_column(default=0)


class Group(Base):
    __tablename__ = 'group'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int]
    day: Mapped[int]
    hour: Mapped[int]
    count: Mapped[int] = mapped_column(default=0)


from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///stats.db')
session = scoped_session(sessionmaker(autoflush=True, bind=engine))
Base.metadata.create_all(bind=engine)
Base.session = session.query_property()
