from fastapi.testclient import TestClient

from app.Main import app


from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.database import get_db
from app.database import Base
import pytest

SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base = declarative_base()
#https://fastapi.tiangolo.com/advanced/testing-dependencies/
# Dependency
#def override_get_db():
#    db = TestingSessionLocal()
#    try:
#        yield db
#    finally:
#        db.close()



# The session fixture ensures a clean state for each test by recreating the database schema.
# fixtures default have function scope means they are going to run before every test function means
# fixtures run before test_create_user, test_login, test_root, so user created by test_create_user is lost when test_login begins
# https://docs.pytest.org/en/stable/how-to/index.html
#(scope="function")
@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# The client fixture creates a test client that uses this session, allowing tests to make requests to the FastAPI application as if it were running normally, 
# but with a controlled test environment.
#(scope="function")
@pytest.fixture
def client(session):
    #Base.metadata.drop_all(bind=engine) # before test completion drop all tables 
    # run our code before we return our test
    #Base.metadata.create_all(bind=engine) # tells sqlalchemy to build all tables based of on the models 
    #means before our code runs i can create my tables 
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # run our code after our test finishes 