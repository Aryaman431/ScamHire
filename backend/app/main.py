from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager
from mangum import Mangum

from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.jobs import router as jobs_router
from app.api.health import router as health_router
from app.api.analysis import router as analysis_router
from app.api.history import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DynamoDB table exists on startup
    try:
        from app.core.dynamodb import ensure_table_exists
        ensure_table_exists()
    except Exception as e:
        print(f'WARNING: Could not ensure DynamoDB table: {e}')
        print('The app will still work if the table already exists.')
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f'{settings.API_V1_STR}/openapi.json',
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS for frontend access
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',') if origin.strip()]
is_wildcard = '*' in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if not is_wildcard else ['*'],
    allow_origin_regex=r'^https:\/\/.*\.vercel\.app$' if not is_wildcard else None,
    allow_credentials=not is_wildcard,
    allow_methods=['*'],
    allow_headers=['*'],
)

# API v1 routes (frontend compatibility)
app.include_router(jobs_router, prefix=f'{settings.API_V1_STR}/jobs', tags=['jobs'])

# New API routes (per requirements)
app.include_router(health_router, tags=['health'])
app.include_router(analysis_router, prefix='/api', tags=['analysis'])
app.include_router(history_router, prefix='/api', tags=['history'])


@app.get('/')
async def root():
    return {'message': 'Welcome to the HireShield API', 'version': '2.0.0'}


# Lambda handler
handler = Mangum(app)
