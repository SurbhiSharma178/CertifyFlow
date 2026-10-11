
from app.db.database import session_local
from app.models.job import GenerateJobs
from app.models.certificate import Certificate
from app.services.certificate_generator import generate_certificate


def process_job(job_id: int) -> None:
    db = session_local()

    try:
        job = db.get(GenerateJobs, job_id)

        if job is None:
            return

        job.status = "Processing"
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        )

        success_count = 0
        failure_count = 0

        for certificate in certificates:
            try:
                certificate.status = "Processing"
                db.commit()

                # Generate and save one PDF for this recipient.
                pdf_path = generate_certificate(job, certificate)

                certificate.folder_path = pdf_path
                certificate.status = "Completed"
                certificate.error_message = None
                success_count += 1

            except Exception as exc:
                # One failed recipient must not stop the batch.
                db.rollback()

                # Reload this recipient after rollback.
                certificate = db.get(Certificate, certificate.id)
                if certificate is not None:
                    certificate.status = "Failed"
                    certificate.error_message = str(exc)[:2000]

                failure_count += 1

            finally:
                # Persist each recipient's outcome independently.
                db.commit()

        job = db.get(GenerateJobs, job_id)
        if job is not None:
            job.success = success_count
            job.failure = failure_count

            if failure_count == 0:
                job.status = "Completed"
            elif success_count == 0:
                job.status = "Failed"
            else:
                job.status = "Partially Completed"

            db.commit()

    except Exception:
        db.rollback()
        job = db.get(GenerateJobs, job_id)

        if job is not None:
            job.status = "Failed"
            db.commit()

    finally:
        db.close()
