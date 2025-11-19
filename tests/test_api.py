# tests/test_api.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_hello(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'Hello, DevOps' in r.data

def test_echo(client):
    r = client.post('/echo', json={'x': 1})
    assert r.status_code == 200
    assert b'you_sent' in r.data
