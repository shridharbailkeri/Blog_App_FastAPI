import email
from pydoc import cli
from urllib import response

from click import password_option
from app import schemas

import pytest
from jose import JWTError, jwt
from app.config import settings


def test_root(client):
    response = client.get("/")
    print(response.json().get('message'))
    assert response.json().get('message') == "Hello Tom!!!J"
    assert response.status_code == 200

def test_create_user(client):
    res = client.post("/users/", json={"email": "cindyB@gmail.com", "password": "sdf"})
    print(res.json())
    new_user = schemas.UserResponse(**res.json())
    #assert res.json().get("email") == "cindyA@gmail.com"
    assert new_user.email == "cindyB@gmail.com"
    assert res.status_code == 201

# whenever you want to run something before a test create fixtures 
# order run session first then run client then run test user 
def test_login_user(client, test_user):
    # remember for login we are not sending data in request body rather as form data 
    res = client.post("/login", data={"username": test_user['email'], "password": test_user['password']})
    print(res.json())
    login_res = schemas.Token(**res.json()) # will perform validation
    payload = jwt.decode(login_res.access_token, settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    assert id == test_user['id']
    assert login_res.token_type == "bearer"
    assert res.status_code == 200

@pytest.mark.parametrize("email, password, status_code", [
    ("wrongEmail@mail.com", "wrongPw", 403),
    ("wrong@mail.com", "wrong", 403),
    ("helloWorld@mail.com", "OUT", 403),
    (None, "OUT", 422),
    ("helloWorld@mail.com", None, 422)
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post("/login", data={"username": email, "password": password})
    assert res.status_code == status_code
    #assert res.json().get('detail') == 'Invalid credentials'