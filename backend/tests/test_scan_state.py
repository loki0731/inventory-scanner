import pytest
from app.services.errors import classify_error

def test_error_classification():
    assert classify_error(TimeoutError('x'))=='TIMEOUT'
    assert classify_error(Exception('authentication failed'))=='AUTH_FAILED'
    assert classify_error(Exception('connection refused'))=='UNREACHABLE'
