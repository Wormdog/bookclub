import enum
from sqlalchemy import (Column, Integer, String, Boolean,
                        ForeignKey, DateTime, UniqueConstraint)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
 
class RoundStatus(str, enum.Enum):
    open     = "open"
    tiebreak = "tiebreak"
    finished = "finished"
 
class Round(Base):
    __tablename__ = "rounds"
    id                 = Column(Integer, primary_key=True, index=True)
    opens_at           = Column(DateTime, nullable=False)
    closes_at          = Column(DateTime, nullable=False)
    tiebreak_closes_at = Column(DateTime, nullable=True)
    status             = Column(String, default=RoundStatus.open)
    winner_ol_work_id  = Column(String, nullable=True)
    winner_title       = Column(String, nullable=True)
    winner_author      = Column(String, nullable=True)
    winner_cover_url   = Column(String, nullable=True)
    meeting_date       = Column(String, nullable=True)
    meeting_location   = Column(String, nullable=True)
    nominations        = relationship("Nomination", back_populates="round")
 
class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    username        = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin        = Column(Boolean, default=False)
    is_verified     = Column(Boolean, default=False)
    verify_token    = Column(String, nullable=True)
    nominations     = relationship("Nomination", back_populates="nominator")
    votes           = relationship("Vote", back_populates="voter")
 
class Nomination(Base):
    __tablename__ = "nominations"
    id         = Column(Integer, primary_key=True, index=True)
    round_id   = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"))
    ol_work_id = Column(String, nullable=False)
    title      = Column(String, nullable=False)
    author     = Column(String)
    cover_url  = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_tied    = Column(Boolean, default=False)  # flagged during tiebreak
    round      = relationship("Round", back_populates="nominations")
    nominator  = relationship("User", back_populates="nominations")
    votes      = relationship("Vote", back_populates="nomination")
 
class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("user_id", "round_id",
                      name="uq_one_vote_per_user_per_round"),)
    id            = Column(Integer, primary_key=True, index=True)
    round_id      = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    user_id       = Column(Integer, ForeignKey("users.id"))
    nomination_id = Column(Integer, ForeignKey("nominations.id"))
    created_at    = Column(DateTime, default=datetime.utcnow)
    voter         = relationship("User", back_populates="votes")
    nomination    = relationship("Nomination", back_populates="votes")
