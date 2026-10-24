from datetime import datetime

from app.utils.datetime_utils import utc_now_naive

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="pendente",
        nullable=False,
        index=True,
    )

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, 
        nullable=True
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )   
    last_error: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True
    )
