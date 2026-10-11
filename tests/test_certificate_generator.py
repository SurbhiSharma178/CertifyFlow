from datetime import date
from types import SimpleNamespace

import pytest

from app.services import certificate_generator


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Aarav Sharma", "Aarav_Sharma"),
        ('A/B:C*D?"E', "ABCDE"),
        ("  Meera   Patel  ", "Meera_Patel"),
        ("\x00\x01", "recipient"),
        ("", "recipient"),
    ],
)
def test_safe_filename_removes_unsafe_characters(name, expected):
    assert certificate_generator.safe_filename(name) == expected


def test_get_job_folder_creates_job_specific_directory(tmp_path, monkeypatch):
    generated_dir = tmp_path / "generated"
    monkeypatch.setattr(certificate_generator, "GENERATED_DIR", generated_dir)

    folder = certificate_generator.get_job_folder(42)

    assert folder == generated_dir / "CertifyFlow_42"
    assert folder.is_dir()


def test_generate_certificate_creates_pdf_with_safe_unique_filename(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "app"
    generated_dir = app_dir / "generated"
    monkeypatch.setattr(certificate_generator, "APP_DIR", app_dir)
    monkeypatch.setattr(certificate_generator, "GENERATED_DIR", generated_dir)

    job = SimpleNamespace(
        id=7,
        certificate_title="Achievement",
        event_name="Annual Tech Summit",
        event_date=date(2026, 10, 11),
        issuer="Organizing Committee",
    )
    certificate = SimpleNamespace(id=3, recipient_name='Aarav / Sharma?')

    relative_path = certificate_generator.generate_certificate(job, certificate)
    output_path = app_dir / relative_path

    assert relative_path == (
        "generated/CertifyFlow_7/Aarav_Sharma_3.pdf"
    )
    assert output_path.is_file()
    assert output_path.read_bytes().startswith(b"%PDF")

