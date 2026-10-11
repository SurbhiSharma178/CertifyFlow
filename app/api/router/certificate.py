from datetime import date
from io import BytesIO
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.certificate import Certificate
from app.models.job import GenerateJobs
from app.schemas.job import JobResponseSchema, RecipientSchema

router= APIRouter(prefix="/upload", tags=["file upload"])
@router.post("/", response_model= JobResponseSchema, status_code=201)
async def upload_recipients(
  certificate_title:str= Form(...),
  event_name:str= Form(...),
  event_date:date=Form(...),
  file:UploadFile= File(...),
  issuer:str=Form(...),
  db:Session= Depends(get_db)
):
  filename= (file.filename or "").lower()
  if not filename.endswith((".xlsx",".csv")):
    raise HTTPException(status_code=400, detail ="Invalid file formate only .xlxs or .csv file allowed")

  try:
    content= await file.read()
    if not content:
      raise HTTPException(status_code=400, detail="File is empty")

    if filename.endswith(".csv"):
      df= pd.read_csv(BytesIO(content))
    else:
      df= pd.read_excel(BytesIO(content), engine="openpyxl")

    df.columns= [str(col).strip().lower() for col in df.columns]

    if "recipient_name" not in df.columns and "name" in df.columns:
      df.rename(columns={"name":"recipient_name"})
    if "recipient_email" not in df.columns and "email" in df.columns:
      df.rename(columns={"email":"recipient_email"})

    if "recipient_name" not in df.columns:
      raise HTTPException(status_code=400, detail="Missing required column: recipient_name")

    if "recipient_email" not in df.columns:
      df["recipient_email"]= None

    if df.empty:
      raise HTTPException(status_code=400, detail="File is empty")

    recipients= []
    for index, row in df.iterrows():
      raw_name= row["recipient_name"]

      if pd.isna(raw_name) or not str(raw_name).strip():
        raise HTTPException(status_code=400, detail=f"Missing recipient_name ")

      
      raw_email= row["recipient_email"]
      email = None if pd.isna(raw_email) else str(raw_email).strip()
      email = email or None

      try:
        recipient= RecipientSchema(
          recipient_name= str(row["recipient_name"]).strip(),
          recipient_email= email
        )
      except Exception as e:
            raise HTTPException(
                    status_code=400,
                    detail=f"Invalid recipient data ",
                ) from e
      recipients.append(recipient)

      job = GenerateJobs(
            certificate_title=certificate_title,
            event_name=event_name,
            issuer=issuer,
            event_date=event_date,
            status="Pending",
            total_count=len(recipients),
            success=0,
            failure=0,
        )

      db.add(job)
      db.flush()

      for recipient in recipients:
          db.add(
                Certificate(
                    job_id=job.id,
                    recipient_name=recipient.recipient_name,
                    recipient_email=recipient.recipient_email,
                    status="Pending",
                )
            )

      db.commit()
      db.refresh(job)
      return job

  except HTTPException:
        db.rollback()
        raise
  except Exception as exc:
        db.rollback()
        print("Upload Error", repr(exc))
        raise HTTPException(
            status_code=400,
            # detail="
            detail= str(exc)
        ) from exc
  finally:
        await file.close()