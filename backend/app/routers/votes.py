from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from ..auth import get_current_user
from ..schemas import NominationCreate, NominationOut, VoteCreate
 
router = APIRouter(tags=["nominations & votes"])
 
def _get_active_round(db: Session):
    round_obj = db.query(models.Round).filter(
        models.Round.status.in_([models.RoundStatus.open,
                                  models.RoundStatus.tiebreak])
    ).first()
    if not round_obj:
        raise HTTPException(404, "No active voting round at this time.")
    return round_obj
 
@router.post("/nominations", response_model=NominationOut)
def nominate(nom: NominationCreate, db: Session = Depends(get_db),
             current_user=Depends(get_current_user)):
    round_obj = _get_active_round(db)
    if round_obj.status == models.RoundStatus.tiebreak:
        raise HTTPException(400, "Voting is in tiebreak — nominations are closed.")
    if db.query(models.Vote).filter(
            models.Vote.user_id == current_user.id,
            models.Vote.round_id == round_obj.id).first():
        raise HTTPException(400, "You already voted this round — you cannot also nominate.")
    if db.query(models.Nomination).filter(
            models.Nomination.user_id == current_user.id,
            models.Nomination.round_id == round_obj.id).first():
        raise HTTPException(400, "You already nominated a book this round.")
    new_nom = models.Nomination(
        **nom.model_dump(), user_id=current_user.id, round_id=round_obj.id)
    db.add(new_nom); db.commit(); db.refresh(new_nom)
    new_nom.vote_count = 0
    return new_nom
 
@router.get("/nominations", response_model=list[NominationOut])
def list_nominations(db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
    round_obj = _get_active_round(db)
    query = db.query(models.Nomination).filter(
        models.Nomination.round_id == round_obj.id)
    if round_obj.status == models.RoundStatus.tiebreak:
        query = query.filter(models.Nomination.is_tied == True)
    noms = query.all()
    for n in noms: n.vote_count = len(n.votes)
    return noms
 
@router.post("/votes")
def vote(vote_in: VoteCreate, db: Session = Depends(get_db),
         current_user=Depends(get_current_user)):
    round_obj = _get_active_round(db)
    if round_obj.status == models.RoundStatus.tiebreak:
        tied_nom_ids = {n.user_id for n in db.query(models.Nomination).filter(
            models.Nomination.round_id == round_obj.id,
            models.Nomination.is_tied == True).all()}
        if current_user.id in tied_nom_ids:
            raise HTTPException(403,
                "You nominated one of the tied books and cannot vote in the tiebreak.")
        participated = (
            db.query(models.Vote).filter(
                models.Vote.user_id == current_user.id,
                models.Vote.round_id == round_obj.id).first() or
            db.query(models.Nomination).filter(
                models.Nomination.user_id == current_user.id,
                models.Nomination.round_id == round_obj.id).first()
        )
        if not participated:
            raise HTTPException(403,
                "Only members who participated in the original round can vote in the tiebreak.")
    if round_obj.status == models.RoundStatus.open:
        if db.query(models.Nomination).filter(
                models.Nomination.user_id == current_user.id,
                models.Nomination.round_id == round_obj.id).first():
            raise HTTPException(400,
                "You nominated a book this round — you cannot also vote.")
    if db.query(models.Vote).filter(
            models.Vote.user_id == current_user.id,
            models.Vote.round_id == round_obj.id).first():
        raise HTTPException(400, "You already voted this round.")
    nomination = db.query(models.Nomination).filter(
        models.Nomination.id == vote_in.nomination_id,
        models.Nomination.round_id == round_obj.id).first()
    if not nomination:
        raise HTTPException(404, "Nomination not found in this round.")
    db.add(models.Vote(user_id=current_user.id,
                       nomination_id=vote_in.nomination_id,
                       round_id=round_obj.id))
    db.commit()
    return {"detail": "Vote recorded successfully!"}
 
@router.get("/rounds/current-public")
def get_current_round_public(db: Session = Depends(get_db),
                              current_user=Depends(get_current_user)):
    round_obj = db.query(models.Round).filter(
        models.Round.status.in_([models.RoundStatus.open,
                                  models.RoundStatus.tiebreak])
    ).first()
    if not round_obj:
        return {"status": "no_active_round"}
    return {
        "status":             round_obj.status,
        "closes_at":          round_obj.closes_at.isoformat(),
        "tiebreak_closes_at": round_obj.tiebreak_closes_at.isoformat()
                              if round_obj.tiebreak_closes_at else None,
    }

