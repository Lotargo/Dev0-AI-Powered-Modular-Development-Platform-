
import pytest
from project.core.swarm.schemas import NetworkLesson, KnowledgePayload, NetworkMeta
from project.core.swarm.sanitizer import PrivacyFilter

# --- Schema Tests ---

def test_network_lesson_creation():
    payload = KnowledgePayload(
        problem_pattern="ImportError: No module named 'cv2'",
        solution_snippet="import cv2",
        dependencies=["opencv-python"],
        key_insight="Use opencv-python for cv2"
    )
    meta = NetworkMeta(author_hash="node123")

    lesson = NetworkLesson(
        id="hash123",
        vector_hash="vhash123",
        topic_embedding=[0.1] * 384,
        payload=payload,
        meta=meta
    )

    assert lesson.payload.dependencies == ["opencv-python"]
    assert lesson.meta.validation_score == 0.0

# --- Sanitizer Tests ---

@pytest.fixture
def filter():
    return PrivacyFilter()

def test_sanitize_ips(filter):
    text = "Connect to 192.168.1.1 database."
    assert filter.sanitize(text) == "Connect to <IP_REDACTED> database."

def test_sanitize_emails(filter):
    text = "Contact admin@example.com for help."
    assert filter.sanitize(text) == "Contact <EMAIL_REDACTED> for help."

def test_sanitize_api_keys(filter):
    text = "Key: sk-1234567890abcdef1234567890abcdef (secret)"
    assert filter.sanitize(text) == "Key: <KEY_REDACTED> (secret)"

    text2 = "Tavily: tvly-1234567890abcdef1234567890abcdef"
    assert filter.sanitize(text2) == "Tavily: <KEY_REDACTED>"

def test_sanitize_paths(filter):
    text = "Error in /app/project/main.py at line 10."
    assert filter.sanitize(text) == "Error in <PROJECT_ROOT>/project/main.py at line 10."

    text2 = "File /home/jules/secret.txt"
    assert filter.sanitize(text2) == "File <HOME_DIR>/secret.txt"

def test_sanitize_complex_log(filter):
    log = """
    DB connection failed at 10.0.0.5.
    User jules (jules@corp.com) reported error in /app/src/db.py.
    API key sk-abcdef12345678901234567890 was used.
    """
    cleaned = filter.sanitize(log)
    assert "10.0.0.5" not in cleaned
    assert "jules@corp.com" not in cleaned
    assert "/app/src/db.py" not in cleaned
    assert "sk-abcdef" not in cleaned

    assert "<IP_REDACTED>" in cleaned
    assert "<EMAIL_REDACTED>" in cleaned
    assert "<PROJECT_ROOT>" in cleaned
    assert "<KEY_REDACTED>" in cleaned
