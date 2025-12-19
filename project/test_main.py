from fastapi.testclient import TestClient
from project.main import app
import pytest

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_execute_email_validator_valid_email(client):
    """
    Tests executing the email_validator module with a valid email.
    """
    response = client.post(
        "/v1/modules/execute/email_validator",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["result"]["is_valid"] is True

def test_execute_email_validator_invalid_email(client):
    """
    Tests executing the email_validator module with an invalid email.
    """
    response = client.post(
        "/v1/modules/execute/email_validator",
        json={"email": "testexample.com"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["result"]["is_valid"] is False

def test_execute_email_validator_missing_email(client):
    """
    Tests executing the email_validator module with missing inputs.
    """
    response = client.post(
        "/v1/modules/execute/email_validator",
        json={},
    )
    assert response.status_code == 400

def test_execute_non_existent_module(client):
    """
    Tests executing a non-existent module.
    """
    response = client.post(
        "/v1/modules/execute/non_existent_module",
        json={"data": "test"},
    )
    assert response.status_code == 404
