from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile , ZIP_DEFLATED


from app.db.database import get_db
from app.models.job import GenerateJobs
from app.models.certificate import Certificate
from app.schemas.job import JobResponseSchema, JobSchema 
from app.services.job_service import process_job 

router= APIRouter(prefix="/jobs", tags=["Jobs"])
APP_DIR= Path(__file__).resolve().parents[2]
GENERATED_DIR= APP_DIR /"generated"

@router.post("/", response_model= JobResponseSchema, status_code=201)
def create_job(job:JobSchema,background_tasks:BackgroundTasks, db:Session= Depends(get_db)):
    try:
        new_job= GenerateJobs(
        event_name= job.event_name,
        event_date= job.event_date,
        certificate_title= job.certificate_title,
        issuer= job.issuer,
        status= "Pending",
        total_count= len(job.recipients),
        success= 0,
        failure= 0
    )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        for cert in job.recipients:
            new_cert= Certificate(
            job_id= new_job.id,
            recipient_name= cert.recipient_name,
            status= "Pending"
            )
            db.add(new_cert)

        db.commit()
        db.refresh(new_job)

        background_tasks.add_task(process_job, new_job.id)
        return new_job
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


def get_certificate_pdf(certificate):
    "Resolve a stored PDF path safely within the generated folder."
    if not certificate.folder_path:
        raise HTTPException(
            status_code=404,
            detail="Certificate has not been generated yet."
        )
    pdf_path= Path(APP_DIR/certificate.folder_path).resolve()

    try:
        pdf_path.relative_to(GENERATED_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid certificate path."
        )

    if not pdf_path.is_file():
        raise HTTPException(
            status_code= 404,
            detail= "Certificate file not found."
        )
    return pdf_path

@router.get("/{job_id}/status")
def get_job_status(job_id:int, db:Session= Depends(get_db)):
    """Return job status and counts of success and failure. """
    job= db.get(GenerateJobs, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )
    certificates= db.query(Certificate).filter(Certificate.job_id==job_id).all()

    total= len(certificates)
    success= sum(
        1 for cert in certificates
        if cert.status.lower() == "completed"
    )
    failed = sum(
        1 for cert in certificates
        if cert.status.lower() == "failed"
    )
    processed = success + failed

    progress = round(processed / total * 100, 2) if total else 100.0

    return {
        "job_id":job.id,
        "event_name": job.event_name,
        "status": job.status,
        "total": total,
        "success": success,
        "failed": failed,
        "processing": sum(
            1 for cert in certificates
            if cert.status.lower() == "processing"
        ),
        "pending": sum(
            1 for cert in certificates
            if cert.status.lower() == "pending"
        ),
        "progress_percentage": progress
    }



@router.get("/{job_id}/download-all")
def download_all_certificates(job_id: int,     db: Session = Depends(get_db)):
    """Download all generated certificates for a job as a zip file."""
    job = db.get(GenerateJobs, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    certificates = db.query(Certificate).filter(Certificate.job_id == job_id, Certificate.status == "Completed",).order_by(Certificate.id).all()

    if not certificates:
        raise HTTPException(
            status_code=404,
            detail="No completed certificates found for this job."
        )

    zip_buffer = BytesIO()
    added_files = 0
    with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as zip_file:
        for cert in certificates:
            try:
                pdf_path = get_certificate_pdf(cert)
                zip_file.write(pdf_path, arcname=pdf_path.name)
                added_files+=1
            except HTTPException as e:
                # Skip certificates that haven't been generated yet
                continue

    if added_files==0:
        raise HTTPException(
            status_code=404,
            detail="No valid certificate files found to include in the zip."
        )
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={job.event_name.replace(' ', '_')}_certificates.zip"
        }
    )