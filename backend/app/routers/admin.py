from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user
from ..schemas import RoundCreate, RoundOut, RoundResultsUpdate
from ..email_utils import send_results_email
 
router = APIRouter(prefix="/admin", tags=["admin"])
 
def require_admin(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user
 
@router.post("/rounds", response_model=RoundOut)
def create_round(round_in: RoundCreate, db: Session = Depends(get_db),
                 _=Depends(require_admin)):
    existing = db.query(models.Round).filter(
        models.Round.status.in_([models.RoundStatus.open,
                                  models.RoundStatus.tiebreak])
    ).first()
    if existing:
        raise HTTPException(400, "A round is already in progress.")
    new_round = models.Round(
        opens_at=round_in.opens_at,
        closes_at=round_in.closes_at,
        status=models.RoundStatus.open,
    )
    db.add(new_round); db.commit(); db.refresh(new_round)
    return new_round
 
@router.get("/rounds/current", response_model=RoundOut)
def get_current_round(db: Session = Depends(get_db), _=Depends(require_admin)):
    round_obj = db.query(models.Round).filter(
        models.Round.status.in_([models.RoundStatus.open,
                                  models.RoundStatus.tiebreak])
    ).first()
    if not round_obj:
        raise HTTPException(404, "No active round.")
    return round_obj
 
@router.patch("/rounds/{round_id}/results", response_model=RoundOut)
def set_results(round_id: int, results: RoundResultsUpdate,
                db: Session = Depends(get_db), _=Depends(require_admin)):
    round_obj = db.query(models.Round).filter(
        models.Round.id == round_id,
        models.Round.status == models.RoundStatus.finished
    ).first()
    if not round_obj:
        raise HTTPException(404, "Finished round not found.")
    round_obj.meeting_date     = results.meeting_date
    round_obj.meeting_location = results.meeting_location
    db.commit(); db.refresh(round_obj)
    users  = db.query(models.User).filter(models.User.is_verified == True).all()
    emails = [u.email for u in users]
    if emails:
        try:
            send_results_email(
                to_emails=emails,
                winner_title=round_obj.winner_title,
                winner_author=round_obj.winner_author,
                winner_cover_url=round_obj.winner_cover_url,
                meeting_date=round_obj.meeting_date,
                meeting_location=round_obj.meeting_location,
            )
        except Exception as e:
            print(f"[WARN] Results email failed: {e}")
    return round_obj
 
@router.get("/rounds/latest-finished", response_model=RoundOut)
def get_latest_finished(db: Session = Depends(get_db)):
    round_obj = db.query(models.Round).filter(
        models.Round.status == models.RoundStatus.finished
    ).order_by(models.Round.id.desc()).first()
    if not round_obj:
        raise HTTPException(404, "No finished rounds yet.")
    return round_obj

