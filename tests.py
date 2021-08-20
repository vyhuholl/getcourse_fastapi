import os
import pytest
from fastapi.testclient import TestClient
from .main import app


secret_key = os.environ.get('getcourse_secret')

client = TestClient(app)


def test_unauthorized():
    response = client.post('/vyhuholl/deals')
    assert response.status_code == 401, response.text
    assert response.json() == {'detail': 'Not authenticated'}


required_params = {
    'detail': [
        {
            'loc': ['body', 'grant_type'],
            'msg': 'field required',
            'type': 'value_error.missing',
        },
        {
            'loc': ['body', 'username'],
            'msg': 'field required',
            'type': 'value_error.missing',
        },
        {
            'loc': ['body', 'password'],
            'msg': 'field required',
            'type': 'value_error.missing',
        },
    ]
}

grant_type_required = {
    'detail': [
        {
            'loc': ['body', 'grant_type'],
            'msg': 'field required',
            'type': 'value_error.missing',
        }
    ]
}

grant_type_incorrect = {
    'detail': [
        {
            'loc': ['body', 'grant_type'],
            'msg': "string does not match regex 'password'",
            'type': 'value_error.str.regex',
            'ctx': {'pattern': 'password'},
        }
    ]
}


@pytest.mark.parametrize(
    'data,expected_status,expected_response',
    [
        (None, 422, required_params),
        (
            {
                'username': 'johndoe',
                'password': 'secret',
            },
            422,
            grant_type_required,
        ),
        (
            {
                'username': 'johndoe',
                'password': 'secret',
                'grant_type': 'incorrect',
            },
            422,
            grant_type_incorrect,
        ),
        (
            {
                'username': 'johndoe',
                'password': 'secret',
                'grant_type': 'password',
            },
            200,
            {
                'grant_type': 'password',
                'username': 'johndoe',
                'password': 'secret',
                'scopes': [],
                'client_id': None,
                'client_secret': None,
            },
        ),
    ],
)
def test_strict_login():
    response = client.post('/token', data=data)
    assert response.status_code == expected_status
    assert response.json() == expected_response


def test_post_deal():
    response = client.post(
        '/vyhuholl/deals',
        json={
            "user_email": "olga-p-98@mail.ru",
            "offer_code": "000000",
            "product_title": "test0",
            "product_description": "string",
            "quantity": 1,
            "deal_cost": 0,
            "deal_currency": "RUB"
        })
    assert response.status_code == 200, response.text
    assert response.json() == {
        "success": True,
        "action": "add",
        "result": {
            "success": True,
            "deal_id": 121161653,
            "deal_number": "",
            "user_id": 189870964,
            "user_status": "added",
            "error_message": "",
            "error": False,
            "payment_link": ""
            }
    }
