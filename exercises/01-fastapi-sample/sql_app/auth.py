from sqlalchemy.orm import Session

from . import crud

PREFIX_ENCODE = "FAKE_ENCODE::"


def fake_encode_token(payload: dict = {}):
    body = [f'{ik}##{ival}' for ik, ival in payload.items()]
    return PREFIX_ENCODE + ','.join(body)


def fake_decode_token(token: str = ''):
    if PREFIX_ENCODE not in token:
        return {}
    payload = {}
    body = token.split(PREFIX_ENCODE)[1].split(',')
    for ibody in body:
        ik, ival = ibody.split('##')
        payload[ik] = ival
    return payload


def create_user_token(user_id: int):
    """トークン生成"""
    payload = {'user_id': user_id}
    # jose.jwtの代わりに簡易エンコード
    return fake_encode_token(payload)


def authenticate_user(db: Session, email: str, password: str):
    db_user = crud.get_user_by_email(db, email)
    if db_user is None:
        return None

    fake_hashed_password = password + crud.FAKE_HASH
    if fake_hashed_password == db_user.hashed_password:
        return db_user
    return None


def authenticate_user_by_token(db: Session, token: str):
    # jose.jwtの代わりに簡易デコード
    payload = fake_decode_token(token)
    if 'user_id' not in payload:
        return None
    user = crud.get_user(db, payload['user_id'])
    return user
