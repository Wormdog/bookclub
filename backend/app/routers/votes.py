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

    # 1. Check if user already participated (voted or nominated)
    if db.query(models.Vote).filter(
            models.Vote.user_id == current_user.id,
            models.Vote.round_id == round_obj.id).first():
        raise HTTPException(400, "You already participated in this round.")

    # 2. Create the nomination
    new_nom = models.Nomination(
        **nom.model_dump(), 
        user_id=current_user.id, 
        round_id=round_obj.id
    )
    db.add(new_nom)
    db.flush() # Flush to get the new_nom.id before committing

    # 3. Automatically assign the nominator's vote to this book
    auto_vote = models.Vote(
        user_id=current_user.id,
        nomination_id=new_nom.id,
        round_id=round_obj.id
    )
    db.add(auto_vote)
    
    db.commit()
    db.refresh(new_nom)
    
    # Set count to 1 for the response since they just voted for it
    new_nom.vote_count = 1 
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

