from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None


class UserInDB(User):
    hashed_password: str


class Deal(BaseModel):
    user_email: str
    deal_number: Optional[int] = None
    offer_code: str
    product_title: str
    product_description: Optional[str] = Field(
        None, title='описание предложения', max_length=300
    )
    quantity: Optional[int] = 1
    deal_cost: int
    deal_currency: Optional[str] = 'RUB'
