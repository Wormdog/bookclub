from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from .email_utils import (send_results_email, send_tiebreak_email,
                          send_tiebreak_ineligible_email)
 
scheduler = BackgroundScheduler()
 
def _get_db() -> Session:
    return SessionLocal()
 
def _tally_votes(round_obj, db: Session):
    noms = db.query(models.Nomination).filter(
        models.Nomination.round_id == round_obj.id).all()
    tallied = []
    for nom in noms:
        count = db.query(models.Vote).filter(
            models.Vote.nomination_id == nom.id,
            models.Vote.round_id == round_obj.id).count()
        tallied.append((nom, count))
    # Most votes first; earliest nomination as tie-fallback
    tallied.sort(key=lambda x: (-x[1], x[0].created_at))
    return tallied
 
def _finish_round(round_obj, winner_nom, db: Session):
    round_obj.status            = models.RoundStatus.finished
    round_obj.winner_ol_work_id = winner_nom.ol_work_id
    round_obj.winner_title      = winner_nom.title
    round_obj.winner_author     = winner_nom.author
    round_obj.winner_cover_url  = winner_nom.cover_url
    db.commit()
 
def _send_results(round_obj, db: Session):
    if not round_obj.meeting_date or not round_obj.meeting_location:
        return  # admin has not set meeting info yet — skip email for now
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
 
def check_rounds():
    db = _get_db()
    try:
        now = datetime.utcnow()
 
        # ── Check open rounds ─────────────────────────────────────────────────
        open_round = db.query(models.Round).filter(
            models.Round.status == models.RoundStatus.open).first()
 
        if open_round and now >= open_round.closes_at:
            tallied   = _tally_votes(open_round, db)
            if not tallied:
                return
            top_count = tallied[0][1]
            tied      = [nom for nom, cnt in tallied if cnt == top_count]
 
            if len(tied) == 1:
                # Clear winner
                _finish_round(open_round, tied[0], db)
                _send_results(open_round, db)
            else:
                # Tie — start 24hr tiebreak
                open_round.status             = models.RoundStatus.tiebreak
                open_round.tiebreak_closes_at = now + timedelta(hours=24)
                tied_ids = {n.id for n in tied}
                for nom in db.query(models.Nomination).filter(
                        models.Nomination.round_id == open_round.id).all():
                    nom.is_tied = nom.id in tied_ids
                db.commit()
 
                tied_books   = [{"title": n.title, "author": n.author} for n in tied]
                close_str    = open_round.tiebreak_closes_at.strftime(
                                   "%A %B %d at %I:%M %p UTC")
                tied_nom_ids = {n.user_id for n in tied}
 
                all_participants = set()
                for nom in db.query(models.Nomination).filter(
                        models.Nomination.round_id == open_round.id).all():
                    all_participants.add(nom.user_id)
                for vote in db.query(models.Vote).filter(
                        models.Vote.round_id == open_round.id).all():
                    all_participants.add(vote.user_id)
 
                eligible_ids   = all_participants - tied_nom_ids
                ineligible_ids = all_participants & tied_nom_ids
 
                eligible_users   = db.query(models.User).filter(
                    models.User.id.in_(eligible_ids)).all()
                ineligible_users = db.query(models.User).filter(
                    models.User.id.in_(ineligible_ids)).all()
 
                if eligible_users:
                    try:
                        send_tiebreak_email(
                            [u.email for u in eligible_users], tied_books, close_str)
                    except Exception as e:
                        print(f"[WARN] Tiebreak email failed: {e}")
                if ineligible_users:
                    try:
                        send_tiebreak_ineligible_email(
                            [u.email for u in ineligible_users], tied_books)
                    except Exception as e:
                        print(f"[WARN] Ineligible email failed: {e}")
 
        # ── Check tiebreak rounds ─────────────────────────────────────────────
        tb_round = db.query(models.Round).filter(
            models.Round.status == models.RoundStatus.tiebreak).first()
 
        if tb_round and tb_round.tiebreak_closes_at and                 now >= tb_round.tiebreak_closes_at:
            tied_noms = db.query(models.Nomination).filter(
                models.Nomination.round_id == tb_round.id,
                models.Nomination.is_tied == True).all()
            tallied = []
            for nom in tied_noms:
                count = db.query(models.Vote).filter(
                    models.Vote.nomination_id == nom.id,
                    models.Vote.round_id == tb_round.id).count()
                tallied.append((nom, count))
            # Sort: votes desc, then earliest nomination as final fallback
            tallied.sort(key=lambda x: (-x[1], x[0].created_at))
            winner = tallied[0][0]
            _finish_round(tb_round, winner, db)
            _send_results(tb_round, db)
    finally:
        db.close()
 
def start_scheduler():
    scheduler.add_job(check_rounds, "interval", seconds=60, id="round_checker")
    scheduler.start()
    print("[INFO] APScheduler started — checking rounds every 60 seconds.")
