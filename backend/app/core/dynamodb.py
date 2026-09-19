import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings


# In-memory storage for local development without AWS credentials
_local_storage = {}


def _get_dynamodb_resource():
    kwargs = {'region_name': settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID:
        kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.resource('dynamodb', **kwargs)


def _get_table():
    try:
        dynamodb = _get_dynamodb_resource()
        return dynamodb.Table(settings.DYNAMODB_TABLE)
    except NoCredentialsError:
        return None


def _use_local_storage() -> bool:
    '''Check if we should use local in-memory storage.'''
    table = _get_table()
    if table is None:
        return True
    try:
        # Try a quick operation to verify credentials work
        table.table_status
        return False
    except (NoCredentialsError, ClientError):
        return True


def ensure_table_exists():
    '''Create the DynamoDB table if it does not exist.'''
    if _use_local_storage():
        print('Using local in-memory storage (no AWS credentials)')
        return
    
    dynamodb = _get_dynamodb_resource()
    existing = [t.name for t in dynamodb.tables.all()]
    if settings.DYNAMODB_TABLE in existing:
        return

    dynamodb.create_table(
        TableName=settings.DYNAMODB_TABLE,
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )


def save_analysis(record: dict) -> str:
    '''Save an analysis record to DynamoDB or local storage. Returns the record ID.'''
    if _use_local_storage():
        if 'id' not in record:
            record['id'] = str(uuid.uuid4())
        record.setdefault('created_at', datetime.now(timezone.utc).isoformat())
        _local_storage[record['id']] = record
        return record['id']
    
    table = _get_table()
    if 'id' not in record:
        record['id'] = str(uuid.uuid4())
    record.setdefault('created_at', datetime.now(timezone.utc).isoformat())
    table.put_item(Item=record)
    return record['id']


def get_analysis(record_id: str) -> dict | None:
    '''Retrieve a single analysis record by ID.'''
    if _use_local_storage():
        return _local_storage.get(record_id)
    
    table = _get_table()
    resp = table.get_item(Key={'id': record_id})
    return resp.get('Item')


def list_analyses(user_id: str = 'demo_user', limit: int = 20) -> list[dict]:
    '''List analysis records for a user, most recent first.'''
    if _use_local_storage():
        items = [i for i in _local_storage.values() if i.get('user_id') == user_id]
        items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return items[:limit]
    
    table = _get_table()
    try:
        resp = table.scan()
    except ClientError:
        return []
    items = resp.get('Items', [])
    # Filter by user_id if present
    items = [i for i in items if i.get('user_id') == user_id]
    # Sort by created_at descending
    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return items[:limit]
