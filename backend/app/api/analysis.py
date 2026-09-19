from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from io import BytesIO
from typing import Optional

from pypdf import PdfReader

from app.auth.dependencies import get_current_user_id
from app.services.analysis_service import AnalysisService
from app.core.config import settings
from app.api.schemas import AnalyzeTextRequest, AnalyzeTextResponse
from app.core.rate_limit import limiter

router = APIRouter()

ALLOWED_MIME_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf']
CHUNK_SIZE = 1024 * 1024


async def _read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    '''Read at most max_bytes + 1 so oversized uploads are never fully buffered.'''
    chunks = []
    bytes_read = 0
    while bytes_read <= max_bytes:
        chunk = await file.read(min(CHUNK_SIZE, max_bytes - bytes_read + 1))
        if not chunk:
            break
        chunks.append(chunk)
        bytes_read += len(chunk)
    if bytes_read > max_bytes:
        raise HTTPException(status_code=413, detail='Uploaded file exceeds maximum size.')
    return b''.join(chunks)


def _detect_file_type(file_bytes: bytes) -> str | None:
    if file_bytes.startswith(b'%PDF-'):
        return 'application/pdf'
    if file_bytes.startswith(b'\\x89PNG\\r\\n\\x1a\\n'):
        return 'image/png'
    if file_bytes.startswith(b'\\xff\\xd8\\xff'):
        return 'image/jpeg'
    if len(file_bytes) >= 12 and file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'WEBP':
        return 'image/webp'
    return None


def _validate_image(file_bytes: bytes, detected_type: str) -> None:
    if detected_type == 'image/png':
        if len(file_bytes) < 33 or file_bytes[12:16] != b'IHDR' or file_bytes[16:24] == b'\\x00' * 8:
            raise HTTPException(status_code=400, detail='Unsupported file type or invalid file contents.')
    elif detected_type == 'image/jpeg':
        if len(file_bytes) < 4 or not file_bytes.endswith(b'\\xff\\xd9'):
            raise HTTPException(status_code=400, detail='Unsupported file type or invalid file contents.')
    elif detected_type == 'image/webp':
        if len(file_bytes) < 16 or file_bytes[12:16] not in {b'VP8 ', b'VP8L', b'VP8X'}:
            raise HTTPException(status_code=400, detail='Unsupported file type or invalid file contents.')


def _validate_pdf(file_bytes: bytes) -> None:
    try:
        reader = PdfReader(BytesIO(file_bytes), strict=True)
        if reader.is_encrypted or len(reader.pages) == 0:
            raise ValueError
        if len(reader.pages) > settings.MAX_PDF_PAGES:
            raise HTTPException(status_code=400, detail='PDF exceeds the maximum allowed page count.')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail='Uploaded PDF is invalid or unreadable.')


@router.post('/analyze', response_model=AnalyzeTextResponse)
@limiter.limit('60/hour')
async def analyze_text(
    request: Request,
    analyze_request: AnalyzeTextRequest,
    current_user: str = Depends(get_current_user_id),
):
    '''Analyze job posting text for suspicious risk signals.'''
    try:
        service = AnalysisService()
        result = await service.analyze_job_text_new_format(analyze_request.text, user_id=current_user)
        return AnalyzeTextResponse(**result)
    except Exception as e:
        import logging
        logging.error(f'Text analysis error: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An error occurred during text analysis.',
        )


@router.post('/analyze/file', response_model=AnalyzeTextResponse)
@limiter.limit('60/hour')
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user_id),
):
    '''Analyze job opportunity from an uploaded document (image or PDF).'''
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_bytes = await _read_upload_with_limit(file, max_bytes)
    detected_type = _detect_file_type(file_bytes)

    if detected_type not in ALLOWED_MIME_TYPES or detected_type != file.content_type:
        raise HTTPException(status_code=400, detail='Unsupported file type or invalid file contents.')

    if detected_type == 'application/pdf':
        _validate_pdf(file_bytes)
    else:
        _validate_image(file_bytes, detected_type)

    try:
        service = AnalysisService()
        result = await service.analyze_job_file_new_format(
            file_bytes, file.filename, detected_type, user_id=current_user
        )
        return AnalyzeTextResponse(**result)
    except Exception as e:
        import logging
        logging.error(f'File analysis error: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An error occurred during file analysis.',
        )
