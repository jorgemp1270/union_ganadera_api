from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
import os
import uuid
from .. import crud, models, schemas, auth, database
from ..s3 import s3_client, s3_public_client, S3_BUCKET_NAME

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(auth.get_current_user)]
)

# ---------------------------------------------------------------------------
# Helper: attach presigned URL and ultima_revision to a document dict
# ---------------------------------------------------------------------------
def _build_doc_response(doc: models.Documento, db: Session) -> dict:
    try:
        download_url = s3_public_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': doc.storage_key},
            ExpiresIn=3600
        )
    except Exception:
        download_url = None

    ultima = crud.get_ultima_revision(db, doc_id=str(doc.id))

    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "original_filename": doc.original_filename,
        "created_at": doc.created_at,
        "authored": doc.authored,
        "download_url": download_url,
        "ultima_revision": {
            "id": ultima.id,
            "documento_id": ultima.documento_id,
            "admin_id": ultima.admin_id,
            "status": ultima.status,
            "comentario": ultima.comentario,
            "fecha": ultima.fecha,
        } if ultima else None,
    }


# ---------------------------------------------------------------------------
# Admin: literal paths must be declared before /{doc_id} to avoid conflicts
# ---------------------------------------------------------------------------

@router.get("/admin/pending", response_model=List[schemas.DocumentoResponse])
def list_pending_documents(
    skip: int = 0, limit: int = 100,
    current_user: models.Usuario = Depends(auth.require_admin),
    db: Session = Depends(database.get_db)
):
    """Admin: list all documents that have not yet been approved (authored=False)."""
    docs = crud.get_documentos_pendientes(db, skip=skip, limit=limit)
    return [_build_doc_response(doc, db) for doc in docs]


@router.get("/admin/all", response_model=List[schemas.DocumentoResponse])
def list_all_documents(
    skip: int = 0, limit: int = 100,
    current_user: models.Usuario = Depends(auth.require_admin),
    db: Session = Depends(database.get_db)
):
    """Admin: list every document in the system across all users."""
    docs = crud.get_all_documentos(db, skip=skip, limit=limit)
    return [_build_doc_response(doc, db) for doc in docs]


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.DocumentoResponse])
def list_documents(
    skip: int = 0, limit: int = 100,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    docs = crud.get_documentos_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return [_build_doc_response(doc, db) for doc in docs]


@router.post("/upload", response_model=schemas.DocumentoResponse)
async def upload_file(
    doc_type: schemas.DocTypeEnum = Form(...),
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Replace existing document of the same type if one already exists
    # fierro is the only type that allows multiple uploads per user
    if doc_type != schemas.DocTypeEnum.fierro:
        existing = crud.get_documento_by_user_and_type(db, user_id=str(current_user.id), doc_type=doc_type)
        if existing:
            try:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=existing.storage_key)
            except Exception:
                pass
            crud.delete_documento(db=db, doc_id=str(existing.id))

    file_extension = os.path.splitext(file.filename)[1]
    storage_key = f"{current_user.id}/{doc_type.value}/{uuid.uuid4()}{file_extension}"

    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

    doc_data = {
        "usuario_id": current_user.id,
        "doc_type": doc_type,
        "storage_key": storage_key,
        "original_filename": file.filename
    }

    doc = crud.create_documento(db=db, documento_data=doc_data)
    return _build_doc_response(doc, db)


# ---------------------------------------------------------------------------
# Parameterized document paths
# ---------------------------------------------------------------------------

@router.post("/{doc_id}/review", response_model=schemas.DocumentoRevisionResponse)
async def review_document(
    doc_id: str,
    revision: schemas.DocumentoRevisionCreate,
    current_user: models.Usuario = Depends(auth.require_admin),
    db: Session = Depends(database.get_db)
):
    """Admin: approve or deny a document with an optional comment."""
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return crud.create_revision(
        db=db,
        doc_id=doc_id,
        admin_id=str(current_user.id),
        status=models.DocReviewStatusEnum(revision.status),
        comentario=revision.comentario
    )


@router.get("/{doc_id}/reviews", response_model=List[schemas.DocumentoRevisionResponse])
async def get_document_reviews(
    doc_id: str,
    current_user: models.Usuario = Depends(auth.require_admin),
    db: Session = Depends(database.get_db)
):
    """Admin: retrieve full revision history for a document."""
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return crud.get_revisiones_by_documento(db, doc_id=doc_id)


@router.delete("/{doc_id}", response_model=schemas.DocumentoResponse)
async def delete_document(
    doc_id: str,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_doc.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=db_doc.storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete file from storage: {str(e)}")

    response = _build_doc_response(db_doc, db)
    crud.delete_documento(db=db, doc_id=doc_id)
    return response
