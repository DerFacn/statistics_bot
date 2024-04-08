from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from typing import List

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(unique=True, index=True)

    users: Mapped[List['User']] = relationship(back_populates='chat')

    words_count: Mapped[int] = mapped_column(default=0)
    ch_count: Mapped[int] = mapped_column(default=0)
    photo_count: Mapped[int] = mapped_column(default=0)
    video_count: Mapped[int] = mapped_column(default=0)
    audio_count: Mapped[int] = mapped_column(default=0)
    sticker_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[str] = mapped_column(server_default=func.now())


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)

    word_count: Mapped[int] = mapped_column(default=0)
    ch_count: Mapped[int] = mapped_column(default=0)
    photo_count: Mapped[int] = mapped_column(default=0)
    video_count: Mapped[int] = mapped_column(default=0)
    audio_count: Mapped[int] = mapped_column(default=0)
    sticker_count: Mapped[int] = mapped_column(default=0)

    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'))
    chat: Mapped[List['Chat']] = relationship(back_populates='users')

    created_at: Mapped[str] = mapped_column(server_default=func.now())


from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///app.db')
session = scoped_session(sessionmaker(autoflush=False, bind=engine))
Base.metadata.create_all(bind=engine)
Base.session = session.query_property()
