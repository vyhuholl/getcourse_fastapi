import os
import json
import base64
import requests
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from .models import Token, TokenData, User, UserInDB, Deal
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm


SECRET_KEY = '7a8d0d8437093c60d789ee617c616a54ca2f8077e807b0072094b4e87dfc37ca'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    'johndoe': {
        'username': 'johndoe',
        'email': 'johndoe@example.com',
        'hashed_password': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    }
}

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()
        ):
    user = authenticate_user(
        fake_users_db, form_data.username, form_data.password
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def import_deal(account_name: str, deal: Deal):
    url = f'https://{account_name}.getcourse.ru/pl/api/deals'
    secret_key = os.environ.get('getcourse_secret')
    params = base64.b64encode(json.dumps({
        'user': {
            'email': deal.user_email,
        },
        'system': {
            'refresh_if_exists': 1,
        },
        'deal': {
            'deal_number': deal.deal_number,
            'offer_code': deal.offer_code,
            'product_title': deal.product_title,
            'product_description': deal.product_description,
            'quantity': deal.quantity,
            'deal_cost': deal.deal_cost,
            'deal_currency': deal.deal_currency,
        }
    }).encode('UTF-8'))
    data = {'action': 'add', 'key': secret_key, 'params': params}
    response = requests.post(url, data=data)
    return response.json()


@app.post('/{account_name}/deals')
def post_deal(
        current_user: User = Depends(get_current_user),
        deal: dict = Depends(import_deal)
        ):
    return deal
