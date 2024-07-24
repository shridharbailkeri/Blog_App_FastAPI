from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import schemas, database, models
from sqlalchemy.orm import Session
from .config import settings

# tokenUrl= endpoint of our login url with slash removed 
#You are specifying that the endpoint for obtaining the token is login. 
# FastAPI will automatically handle the extraction of the token from incoming requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#SECRET_KEY ultimate verification of data integrity of our token which recides on our server only 
# Algorithm we want to use 
#Expiration time without it user is logged in forever , to dictate how long user should be logged in 

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # adding extra property to the data that is expiration time 
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# Decoding and Verification: When the jwt.decode method is called, 
# it automatically checks the exp claim. If the current time is past the expiration time specified in the token, 
# the jwt.decode method will raise a JWTError, specifically a ExpiredSignatureError.

# he jwt.decode method tries to decode the token and verify its claims, including exp.
# Since the token is expired, jwt.decode raises a ExpiredSignatureError (a subclass of JWTError).
# The except JWTError block catches this error.
# The function raises the credentials_exception, which is an HTTP 401 Unauthorized error.

def verify_access_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")

        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception
    return token_data

# anytime we have specific endpoint that needs to be protected means user needs to login to use it 
# we can add an extra dependency Depends() to the path operation function , we say get current user 
# so anytime anyone wants to access a resource that requires them to be logged in 
# we r going to expect they provide an access token
# Depends and Dependency Injection
# FastAPI uses dependency injection to handle dependencies within your application. 
# Dependencies are pieces of code (functions, classes, etc.) that are "injected" into your path 
# operation functions by FastAPI. 
# The Depends function is a special utility that FastAPI provides to declare these dependencies.
# oauth2_scheme is an instance of OAuth2PasswordBearer. This class is part of FastAPI's 
# security utilities and handles the extraction of a token from the request. 
# It expects the token to be provided in the Authorization header with a Bearer prefix.
# Depends(oauth2_scheme) tells FastAPI to use the oauth2_scheme dependency to get the token from the request
# token: str means that the result of the oauth2_scheme dependency 
# (which is the token string) will be passed as an argument to the get_current_user function.
# example HTTP login request 
#GET /protected-endpoint HTTP/1.1
#Host: example.com
#Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail=f"could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    token = verify_access_token(token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == token.id).first()

    return user

    

    

