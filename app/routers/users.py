from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import timedelta, date
from typing import Annotated
import json

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

@router.post("/signup/veterinario", response_model=schemas.UserResponse)
async def create_veterinario(
    curp: str = Form(...),
    contrasena: str = Form(...),
    nombre: str = Form(...),
    apellido_p: str = Form(...),
    apellido_m: str = Form(None),
    sexo: str = Form(...),
    fecha_nac: str = Form(...),
    clave_elector: str = Form(...),
    idmex: str = Form(...),
    cedula: str = Form(...),
    cedula_file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    """
    Register a new veterinarian with cedula number and file upload.

    The cedula (professional license number) is saved to the veterinarios table.
    The cedula_file (document) is stored in S3 and referenced in the documentos table.
    """
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=curp)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Parse fecha_nac
    try:
        parsed_fecha_nac = date.fromisoformat(fecha_nac)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid fecha_nac format. Use YYYY-MM-DD")

    # Validate password length
    if len(contrasena) > 72 or len(contrasena) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be between 8 and 72 characters"
        )

    # Validate sexo
    if sexo not in ["M", "F", "X"]:
        raise HTTPException(status_code=400, detail="Invalid sexo value. Use M, F, or X")

    # Create VeterinarioCreate schema instance
    vet_data = schemas.VeterinarioCreate(
        curp=curp,
        contrasena=contrasena,
        nombre=nombre,
        apellido_p=apellido_p,
        apellido_m=apellido_m,
        sexo=schemas.SexoEnum(sexo),
        fecha_nac=parsed_fecha_nac,
        clave_elector=clave_elector,
        idmex=idmex,
        cedula=cedula
    )

    # Create veterinario with cedula number and file
    return crud.create_veterinario(db=db, veterinario=vet_data, cedula_file=cedula_file)

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
