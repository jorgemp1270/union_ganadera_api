from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated

from .. import crud, models, schemas, auth, database

router = APIRouter(
    tags=["users"],
)

@router.post("/signup", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.curp)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=user_credentials.curp)
    if not user or not auth.verify_password(user_credentials.contrasena, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.curp}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: Annotated[models.Usuario, Depends(auth.get_current_user)]):
    return current_user
