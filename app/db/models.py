from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    certificate_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    organization: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="QUEUED",
    )

    total_recipients: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    recipients: Mapped[list["Recipient"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Recipient(Base):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("generation_jobs.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="QUEUED",
    )

    certificate_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    job: Mapped["GenerationJob"] = relationship(
        back_populates="recipients",
    )
