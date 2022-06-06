from sqlalchemy.orm import Session

from . import models, schemas

FAKE_HASH = "notreallyhashed"


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_active_first_user(db: Session):
    """is_active: Trueで一番小さいidを持つUserを取得"""
    users = db.query(models.User).filter(models.User.is_active == True)
    return users.order_by(models.User.id).first()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + FAKE_HASH
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    del_user = get_user(db, user_id)
    del_user.is_active = False

    # 削除Userが所有するitemのowner_idを変更
    del_user_items = get_items_by_owner_id(db, del_user.id)
    first_user = get_active_first_user(db)
    for iitem in del_user_items:
        iitem.owner_id = first_user.id
    db.commit()
    db.refresh(del_user)
    return del_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def get_items_by_owner_id(db: Session, owner_id: int):
    return db.query(models.Item).filter(models.Item.owner_id == owner_id).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
