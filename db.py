from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

class AudioBook(db.Model):
    __tablename__ = 'audiobooks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255))
    authors: Mapped[list[str]] = mapped_column(db.JSON, nullable=False)
    narrators: Mapped[list[str]] = mapped_column(db.JSON, nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(255))
    publish_date: Mapped[str | None] = mapped_column(DateTime)
    description: Mapped[str | None] = mapped_column(db.Text)
    genres: Mapped[list[str]] = mapped_column(db.JSON)
    languages: Mapped[list[str]] = mapped_column(db.JSON)
    duration: Mapped[int | None] = mapped_column(Integer)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    sample_url: Mapped[str | None] = mapped_column(String(500))
    is_series: Mapped[bool] = mapped_column(Boolean, default=False)
    series_id: Mapped[str | None] = mapped_column(String(100))
    series_name: Mapped[str | None] = mapped_column(String(255))
    reading_order: Mapped[int | None] = mapped_column(Integer)
    

