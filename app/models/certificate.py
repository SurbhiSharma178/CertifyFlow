from datetime import date, datetime 
from sqlalchemy import Date, DateTime, DateTime, ForeignKey, Integer,String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.job import GenerateJobs

class Certificate(Base):
  __tablename__ = "certificates"

  id: Mapped[int]= mapped_column(
    Integer,
    primary_key= True,
    index= True
  )

  job_id:Mapped[int]= mapped_column(
    ForeignKey("generation_jobs.id"),
    nullable= False
  )

  recipient_name: Mapped[str]= mapped_column(
    String(255),
    nullable= False
  )


  status: Mapped[str]= mapped_column(
    String(50),
    default= "Pending",
    nullable=False
  )
  folder_path:Mapped[str | None]= mapped_column(
    String(255),
    nullable=True
  )

  error_message: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=datetime.utcnow
  )

  updated_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
  )

  job = relationship(
  "GenerateJobs",
  back_populates="certificates"
  )