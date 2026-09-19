from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = " HireShield\
 API_V1_STR: str = \/api/v1\

 # AWS Configuration
 # Uses standard AWS credential provider chain (AWS CLI, env vars, IAM role, etc.)
 # Do NOT commit AWS credentials to source control.
 # For local development: run ws configure or ws sso login
 # For deployment: use IAM execution role or secure env var injection
 AWS_REGION: str = \ap-south-1\

 # S3 Configuration
 S3_BUCKET: str = \hireshield-uploads\

 # DynamoDB Configuration
 DYNAMODB_TABLE: str = \hire-shield-analyses\

 # Bedrock Configuration
 # Model must be available in the configured AWS_REGION
 # Check with: aws bedrock list-foundation-models --region ap-south-1
 BEDROCK_MODEL_ID: str = \anthropic.claude-3-5-sonnet-20241022-v2:0\
 BEDROCK_MAX_TOKENS: int = 4096

 # Auth (demo mode by default)
 CLERK_SECRET_KEY: str | None = None
 CLERK_JWKS_URL: str | None = None
 CLERK_ISSUER_URL: str | None = None

 CORS_ORIGINS: str = \http://localhost:3000\

 # Document Processing
 MAX_UPLOAD_SIZE_MB: int = 10
 MAX_PDF_PAGES: int = 20

 model_config = SettingsConfigDict(
 env_file=(\.env\, \../.env\),
 env_file_encoding=\utf-8\,
 extra=\ignore\,
 )


settings = Settings()
