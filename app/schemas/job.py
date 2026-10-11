from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

class RecipientSchema(BaseModel):
  recipient_name:str= Field(min_length=1, max_length=255)

class JobSchema(BaseModel):
  certificate_title:str= Field(min_length=1, max_length=255)
  issuer:str= Field(min_length=1, max_length=255)
  event_name:str= Field(min_length=1, max_length=255)
  event_date:date
  recipients:list[RecipientSchema]= Field(min_length=1)

class JobResponseSchema(BaseModel):
  id:int
  certificate_title:str
  issuer:str
  event_name:str
  event_date:date
  status:str
  total_count:int
  success:int
  failure:int
  created_at:datetime

  model_config= {
    "from_attributes":True
  }