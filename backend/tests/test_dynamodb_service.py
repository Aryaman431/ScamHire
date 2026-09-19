import pytest
from app.core.dynamodb import save_analysis, get_analysis, list_analyses, _local_storage


def setup_function():
    '''Clear local storage before each test.'''
    _local_storage.clear()


def test_save_and_get_analysis():
    '''Test saving and retrieving an analysis.'''
    record = {
        'id': 'test-123',
        'risk_score': 50,
        'risk_level': 'HIGH',
        'user_id': 'test_user',
        'created_at': '2024-01-01T00:00:00Z',
    }
    
    saved_id = save_analysis(record)
    assert saved_id == 'test-123'
    
    retrieved = get_analysis('test-123')
    assert retrieved is not None
    assert retrieved['id'] == 'test-123'
    assert retrieved['risk_score'] == 50
    assert retrieved['risk_level'] == 'HIGH'


def test_save_analysis_generates_id():
    '''Test that save_analysis generates an ID if not provided.'''
    record = {
        'risk_score': 30,
        'risk_level': 'MODERATE',
        'user_id': 'test_user',
    }
    
    saved_id = save_analysis(record)
    assert saved_id is not None
    assert len(saved_id) > 0
    
    retrieved = get_analysis(saved_id)
    assert retrieved is not None
    assert retrieved['id'] == saved_id


def test_get_nonexistent_analysis():
    '''Test retrieving a non-existent analysis returns None.'''
    result = get_analysis('nonexistent-id')
    assert result is None


def test_list_analyses():
    '''Test listing analyses for a user.'''
    save_analysis({'id': '1', 'risk_score': 10, 'risk_level': 'LOW', 'user_id': 'user1', 'created_at': '2024-01-01T00:00:00Z'})
    save_analysis({'id': '2', 'risk_score': 50, 'risk_level': 'HIGH', 'user_id': 'user1', 'created_at': '2024-01-02T00:00:00Z'})
    save_analysis({'id': '3', 'risk_score': 30, 'risk_level': 'MODERATE', 'user_id': 'user2', 'created_at': '2024-01-03T00:00:00Z'})
    
    user1_analyses = list_analyses('user1', limit=10)
    assert len(user1_analyses) == 2
    # Should be sorted by created_at descending
    assert user1_analyses[0]['id'] == '2'
    assert user1_analyses[1]['id'] == '1'
    
    user2_analyses = list_analyses('user2', limit=10)
    assert len(user2_analyses) == 1
    assert user2_analyses[0]['id'] == '3'
    
    # Test limit
    limited = list_analyses('user1', limit=1)
    assert len(limited) == 1
    assert limited[0]['id'] == '2'
