from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import LargeBinary, String, Integer


class Base(DeclarativeBase):
    pass


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assistant: Mapped[str] = mapped_column(String(255), nullable=False)
    group: Mapped[str] = mapped_column(String(255), nullable=False)
    theme: Mapped[str] = mapped_column(String(255), nullable=False)
    csv_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)