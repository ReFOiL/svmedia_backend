from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from codes.models import AccessCode

class User(Base):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    access_codes: Mapped[list["AccessCode"]] = relationship(back_populates="created_by") 