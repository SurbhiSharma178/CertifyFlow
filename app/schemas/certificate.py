from datetime import date, datetime 
from pydantic import BaseModel, ConfigDict

class CertificateResponse(BaseModel):
  id:int
  job_id:int
  recipient_name:str
  recipient_email:str
  status:str
  folder_path:str | None= None
  error_message:str | None= None
  created_at:datetime
  updated_at:datetime

  model_config= ConfigDict(from_attributes=True)