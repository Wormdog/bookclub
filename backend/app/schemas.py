from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
 
class UserCreate(BaseModel):
    email:    EmailStr
    username: str
    password: str
 
class UserRegister(BaseModel):
    email:       EmailStr
    username:    str
    password:    str
    invite_code: str
 
class UserOut(BaseModel):
    id:       int
    email:    str
    username: str
    is_admin: bool
    model_config = {"from_attributes": True}
 
class NominationCreate(BaseModel):
    ol_work_id: str
    title: str
    author: str | None = None
    cover_url: str | None = None
 
class NominationOut(NominationCreate):
    id: int
    user_id: int
    round_id: int
    created_at: datetime
    vote_count: int = 0
    model_config = {"from_attributes": True}
 
class VoteCreate(BaseModel):
    nomination_id: int
 
class RoundCreate(BaseModel):
    opens_at:  datetime
    closes_at: datetime
 
class RoundResultsUpdate(BaseModel):
    meeting_date:     str
    meeting_location: str
 
class RoundOut(BaseModel):
    id:                 int
    opens_at:           datetime
    closes_at:          datetime
    tiebreak_closes_at: Optional[datetime] = None
    status:             str
    winner_title:       Optional[str] = None
    winner_author:      Optional[str] = None
    winner_cover_url:   Optional[str] = None
    meeting_date:       Optional[str] = None
    meeting_location:   Optional[str] = None
    model_config = {"from_attributes": True}
