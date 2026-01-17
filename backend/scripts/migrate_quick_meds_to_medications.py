from sqlalchemy.orm import Session

from database import SessionLocal
from models.quick_medication import QuickMedication
from models.medication import Medication


def migrate():
    db: Session = SessionLocal()
    try:
        quick_meds = db.query(QuickMedication).all()
        for quick in quick_meds:
            existing = db.query(Medication).filter(
                Medication.name == quick.name,
                Medication.recipient_id == quick.recipient_id
            ).first()
            if existing:
                existing.is_quick_med = True
                if not existing.default_dose and quick.dosage:
                    existing.default_dose = quick.dosage
                db.add(existing)
                continue

            med = Medication(
                name=quick.name,
                default_dose=quick.dosage,
                dose_unit=None,
                interval_hours=4,
                early_warning_minutes=15,
                notes=None,
                is_prn=False,
                is_active=quick.is_active,
                auto_start_reminder=False,
                is_quick_med=True,
                recipient_id=quick.recipient_id,
                created_by_user_id=quick.created_by_user_id
            )
            db.add(med)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
