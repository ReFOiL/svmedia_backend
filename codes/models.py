from sqlalchemy import Boolean, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from users.models import User

class AccessCode(Base):
    __tablename__ = "access_code"

    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # IP address or user identifier
    usage_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Additional usage information
    created_by_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    
    # Информация о пользователе
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    squad_number: Mapped[int] = mapped_column(Integer)
    shift_number: Mapped[int] = mapped_column(Integer)

    created_by: Mapped["User"] = relationship(back_populates="access_codes")
