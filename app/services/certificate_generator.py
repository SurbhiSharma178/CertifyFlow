from pathlib import Path
import re


from reportlab.pdfgen import canvas
from app.template.certificate_generator import (
   PAGE_WIDTH, PAGE_HEIGHT, draw_certificate_template
)

APP_DIR= Path(__file__).resolve().parent.parent

TEMPLATES_DIR= APP_DIR/"template"
GENERATED_DIR= APP_DIR/"generated"


def get_job_folder(job_id:int)->Path:
  folder= GENERATED_DIR/f"CertifyFlow_{job_id}"
  folder.mkdir(parents=True, exist_ok=True )
  return folder

def safe_filename(name:str)->str:
  name= re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
  name = re.sub(r"\s+", "_", name.strip())
  return name or "recipient"

def generate_certificate(job, certificate) -> str:
    folder = get_job_folder(job.id)
    filename= (
       f"{safe_filename(certificate.recipient_name)}"
       f"_{certificate.id}.pdf"
    )
    output_path = folder / filename

    pdf= canvas.Canvas(
       str(output_path),
       pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
    )

    draw_certificate_template(pdf,job,certificate)
    pdf.save()

    return output_path.relative_to(APP_DIR).as_posix()

