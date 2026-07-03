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

class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[str] = mapped_column(String(11), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    taking_exam_as: Mapped[str] = mapped_column(String(50), nullable=False)
    t1_score: Mapped[int | None] = mapped_column(Integer)
    t2_score: Mapped[int | None] = mapped_column(Integer)
    t3_score: Mapped[int | None] = mapped_column(Integer)
    first_partial_score: Mapped[int | None] = mapped_column(Integer)
    second_partial_score: Mapped[int | None] = mapped_column(Integer)
    which_tx: Mapped[str | None] = mapped_column(String(2))
    correct_tx: Mapped[int | None] = mapped_column(Integer)
