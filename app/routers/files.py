from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, List
import os
import uuid
import mimetypes
from io import BytesIO
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
def _build_doc_response(doc: models.Documento, db: Session) -> schemas.DocumentoResponse:
    """Build a complete document response with presigned URL and revision info."""
    try:
        download_url = s3_public_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': doc.storage_key},
            ExpiresIn=3600
        )
    except Exception:
        download_url = None

    ultima = crud.get_ultima_revision(db, doc_id=str(doc.id))
    
    ultima_revision = None
    if ultima:
        try:
            ultima_revision = schemas.DocumentoRevisionResponse(
                id=ultima.id,
                documento_id=ultima.documento_id,
                admin_id=ultima.admin_id,
                status=ultima.status,
                comentario=ultima.comentario,
                fecha=ultima.fecha,
            )
        except Exception as e:
            # If we can't create the revision response, just ignore it
            print(f"[WARNING] Could not create revision response: {e}")
            ultima_revision = None

    try:
        return schemas.DocumentoResponse(
            id=doc.id,
            doc_type=doc.doc_type,
            original_filename=doc.original_filename,
            created_at=doc.created_at,
            authored=doc.authored,
            download_url=download_url,
            ultima_revision=ultima_revision,
        )
    except Exception as e:
        # If validation fails, provide detailed error info
        print(f"[ERROR] Failed to create DocumentoResponse: {e}")
        print(f"[DEBUG] doc.id={doc.id} (type: {type(doc.id)})")
        print(f"[DEBUG] doc.doc_type={doc.doc_type} (type: {type(doc.doc_type)})")
        print(f"[DEBUG] doc.created_at={doc.created_at} (type: {type(doc.created_at)})")
        raise


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


@router.get("/health/s3", response_model=dict)
def check_s3_connection(current_user: models.Usuario = Depends(auth.get_current_user)):
    """
    Test S3 connection and return configuration information.
    Useful for debugging upload and preview issues.
    """
    try:
        # Test basic S3 connectivity
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        
        return {
            "status": "connected",
            "bucket": S3_BUCKET_NAME,
            "available_buckets": buckets,
            "s3_endpoint": os.getenv("S3_ENDPOINT_URL", "http://localstack:4566"),
            "s3_public_url": os.getenv("S3_PUBLIC_URL", "http://localhost:4566"),
            "message": "S3 connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "bucket": S3_BUCKET_NAME,
            "error": str(e),
            "s3_endpoint": os.getenv("S3_ENDPOINT_URL", "http://localstack:4566"),
            "s3_public_url": os.getenv("S3_PUBLIC_URL", "http://localhost:4566"),
            "message": "S3 connection failed - check logs"
        }


@router.post("/upload", response_model=schemas.DocumentoResponse)
async def upload_file(
    doc_type: schemas.DocTypeEnum = Form(...),
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Upload a document file for the current user."""
    try:
        # Reemplazar doc_type solo si es explícitamente único por usuario
        unique_user_doc_types = [
            schemas.DocTypeEnum.identificacion_frente,
            schemas.DocTypeEnum.identificacion_reverso,
            schemas.DocTypeEnum.comprobante_domicilio,
            schemas.DocTypeEnum.predio,
            schemas.DocTypeEnum.cedula_veterinario
        ]
        
        if doc_type in unique_user_doc_types:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload error: {type(e).__name__}: {str(e)}"
        )


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
    """Delete a document owned by the current user."""
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delete error: {type(e).__name__}: {str(e)}"
        )


@router.get("/{doc_id}/preview", response_model=dict)
async def get_document_preview(
    doc_id: str,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Get a presigned URL for document preview.
    The URL is valid for 1 hour and can be used to view/download the file.
    """
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Allow access if it's the user's document or if user is admin
    if db_doc.usuario_id != current_user.id and current_user.rol not in [models.RolEnum.administrador, models.RolEnum.superadministrador]:
        raise HTTPException(status_code=403, detail="Not authorized to preview this document")

    try:
        # Generate presigned URL valid for 1 hour (3600 seconds)
        preview_url = s3_public_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': db_doc.storage_key},
            ExpiresIn=3600
        )
        
        return {
            "doc_id": doc_id,
            "filename": db_doc.original_filename,
            "doc_type": db_doc.doc_type,
            "preview_url": preview_url,
            "expires_in": 3600,
            "message": "Preview URL generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Could not generate preview URL: {str(e)}"
        )


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Stream file content directly from API (no CORS issues).
    Returns the file with proper MIME type for preview in browsers/apps.
    Supports: images, PDFs, text files, all formats.
    Cache: 1 hour
    
    Usage in HTML:
    - Images: <img src="/api/files/{id}/content">
    - PDFs: <iframe src="/api/files/{id}/content">
    - Download: <a href="/api/files/{id}/content">Download</a>
    """
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Allow access if it's the user's document or if user is admin
    if db_doc.usuario_id != current_user.id and current_user.rol not in [models.RolEnum.administrador, models.RolEnum.superadministrador]:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")

    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=db_doc.storage_key)
        file_content = response['Body'].read()
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(db_doc.original_filename)
        if mime_type is None:
            # Default to binary for unknown types
            mime_type = 'application/octet-stream'
        
        # Return streaming response with proper headers
        return StreamingResponse(
            iter([file_content]),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={db_doc.original_filename}",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve file content: {str(e)}"
        )
