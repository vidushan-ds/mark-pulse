import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"   
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from app import app, db, limiter

@pytest.fixture(autouse=True)                      
def fresh_database():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    limiter.enabled = False
    with app.app_context():
        db.drop_all()
        db.create_all()

@pytest.fixture                                     
def client():
    return app.test_client()