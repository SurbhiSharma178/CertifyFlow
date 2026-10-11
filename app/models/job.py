from datetime import date, datetime 
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class GenerateJobs(Base):
  __tablename__= "generation_jobs"

  id:Mapped[int]= mapped_column(
    Integer,
    primary_key= True,
    index= True
  )
  event_name:Mapped[str]= mapped_column(
    String(255),
    nullable= False
  )
  event_date:Mapped[date]= mapped_column(
    Date,
    nullable=False
  )
  certificate_title:Mapped[str] = mapped_column(
    String(255),
    nullable=False
  )
  issuer:Mapped[str] = mapped_column(
    String(255),
    nullable=False
  )
  status:Mapped[str]= mapped_column(
    String(50),
    default= "Pending",
    nullable= False
  )
  total_count:Mapped[int]=mapped_column(
    Integer,
    default= 0,
    nullable= False
  )
  success:Mapped[int]= mapped_column(
    Integer,
    default=0,
    nullable= False
  )
  failure:Mapped[int]= mapped_column(
      Integer,
      default=0,
      nullable= False
    )
  created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

  updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

  certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan"
    ) 