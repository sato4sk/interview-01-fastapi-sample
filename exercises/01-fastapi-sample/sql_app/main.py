from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session

from . import auth, crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session, token: str):
    """トークンの認証とユーザーの取得"""
    if token is None:
        raise HTTPException(status_code=404, 
                            detail="X-API-TOKEN is None")

    user = auth.authenticate_user_by_token(db, token)
    if user is None:
        raise HTTPException(status_code=404, 
                            detail="User is not authenticated")
    if not user.is_active:
        raise HTTPException(status_code=404, 
                    detail="User is not active")
    return user


@app.get("/health-check")
def health_check(db: Session = Depends(get_db), 
                 X_API_TOKEN: str = Header(None)):
    _ = get_current_user(db, X_API_TOKEN)
    return {"status": "ok"}


@app.get("/login/")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=404, 
                            detail="User is not active")

    token = auth.create_user_token(user.id)
    return {"login_status": "success", "X-API-TOKEN": token}


@app.post("/users/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db=db, user=user)
    token = auth.create_user_token(new_user.id)
    return {"X-API-TOKEN": token, 'user': new_user}


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               X_API_TOKEN: str = Header(None)):
    # fastAPI.Headerの仕様でX_API_TOKENの_は-に変換される
    _ = get_current_user(db, X_API_TOKEN)
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db),
              X_API_TOKEN: str = Header(None)):
    _ = get_current_user(db, X_API_TOKEN)
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/delete", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db),
                X_API_TOKEN: str = Header(None)):
    _ = get_current_user(db, X_API_TOKEN)
    return crud.delete_user(db, user_id)
    

@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(user_id: int, item: schemas.ItemCreate, 
                         db: Session = Depends(get_db),
                         X_API_TOKEN: str = Header(None)):
    _ = get_current_user(db, X_API_TOKEN)
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db),
               X_API_TOKEN: str = Header(None)):
    _ = get_current_user(db, X_API_TOKEN)
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/me/items", response_model=List[schemas.Item])
def read_my_items(db: Session = Depends(get_db),
                  X_API_TOKEN: str = Header(None)):
    user = get_current_user(db, X_API_TOKEN)
    items = crud.get_items_by_owner_id(db, owner_id=user.id)
    return items
