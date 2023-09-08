from typing import List

from fastapi import APIRouter, HTTPException, status, Body 
from sqlmodel import Session, select
from dundie.models.user import (
    User, 
    UserPasswordPatchRequest, 
    UserResponse, UserRequest, 
    UserProfilePatchRequest
)
from dundie.db import ActiveSession
from dundie.auth import AuthenticatedUser, CanChangeUserPassword, SuperUser
from dundie.tasks.user import try_to_send_pwd_reset_email
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.get("/", response_model=List[UserResponse], dependencies=[AuthenticatedUser])
async def list_users(*, session: Session = ActiveSession):
    """List all users from database"""
    users = session.exec(select(User)).all()
    return users

@router.get("/{username}/", response_model=UserResponse)
async def get_user_by_username(
    *,
    session: Session = ActiveSession, 
    username:str,
):
    """GEt sigle user by username"""
    query = select(User).where(User.username == username)
    user = session.exec(query).first()
    return user

@router.post("/", response_model=UserResponse, status_code=201, dependencies=[SuperUser])
async def create_user(*, session: Session = ActiveSession, user: UserRequest):
    """Create a new user"""
    # LBYL
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already existes")
    
    db_user = User.from_orm(user)
    session.add(db_user)
    # EAFP
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Database IntegrationError"
        )
    session.refresh(db_user)
    return db_user

@router.patch("/{username}/", response_model=UserResponse)
async def update_user(
    *,
    session: Session = ActiveSession,
    patch_data: UserProfilePatchRequest,
    current_user: User = AuthenticatedUser,
    username: str
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id != current_user.id and not current_user.superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own profile")

    # Update
    if patch_data.avatar is not None:
        user.avatar = patch_data.avatar
    if patch_data.bio is not None:
        user.bio = patch_data.bio

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/{username}/password/", response_model=UserResponse)
async def change_password(
    *,
    session: Session = ActiveSession,
    patch_data: UserPasswordPatchRequest,
    user: User = CanChangeUserPassword
):
    user.password = patch_data.hashed_password  # pyright: ignore
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/pwd_reset_token/")
async def send_password_reset_token(*, email: str = Body(embed=True)):
    """Sends an email with the token to reset password."""
    try_to_send_pwd_reset_email(email)
    return {
        "message": "If we found a user with that email, we sent a password reset token to it."
    }