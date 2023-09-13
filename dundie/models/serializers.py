from datetime import datetime
from dundie.db import engine
from dundie.models.user import User 
from pydantic import BaseModel, root_validator
from sqlmodel import select, Session
from typing import Optional


class TransactionResponse(BaseModel):
    id: int
    value: int
    date: datetime
    
    user: Optional[str] = None
    from_user: Optional[str] = None
    
    @root_validator(pre=True)
    def get_username(cls, values):
        with Session(engine) as session:
            user = session.get(User, values['user_id'])
            values['user'] = user and user.username
            from_user = session.get(User, values['from_id'])
            values['from_user'] = from_user and from_user.username
        return values
            