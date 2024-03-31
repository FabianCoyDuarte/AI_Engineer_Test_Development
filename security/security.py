from pydantic import BaseModel
from typing import Union
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from lib.utils import  load_config, load_json
from fastapi import Depends, HTTPException, status


# Load configuration from config.yaml file
config = load_config('./config.yaml')

# Set the secret key and algorithm for JWT token
SECRET_KEY = config['secure']['SECRET_KEY']
ALGORITHM = config['secure']['ALGORITHM']

# Load dummy user database from JSON file
db_dummy = load_json('./data/dummy_users_database.json')

# Create a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the OAuth2 password bearer scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the Token model for representing the access token
class Token(BaseModel):
    access_token: str
    token_type: str


# Define the TokenData model for representing the token data
class TokenData(BaseModel):
    username: Union[str, None] = None


# Define the User model for representing the user data
class User(BaseModel):
    username: str
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


# Define the UserInDB model for representing the user data in the database
class UserInDB(User):
    hashed_password: str

# Verify if the plain password matches the hashed password
def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password.

    Parameters:
    - plain_password (str): The plain password.
    - hashed_password (str): The hashed password.

    Returns:
    - bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

# Generate the hash of a password
def get_password_hash(password):
    """
    Generate the hash of a password.

    Parameters:
    - password (str): The password to be hashed.

    Returns:
    - str: The hashed password.
    """
    return pwd_context.hash(password)

# Retrieve a user from the database based on the username
def get_user(db, username: str):
    """
    Retrieve a user from the database based on the username.

    Parameters:
    - db (dict): The user database.
    - username (str): The username of the user to retrieve.

    Returns:
    - UserInDB: The user object if found, None otherwise.
    """
    users = [db[i] for i in db]
    username_db = [users[n]["username"] for n in range(len(users))]
    if username in username_db:
        user_dict = users[username.index(username)]
        return UserInDB(**user_dict)

# Authenticate a user based on the provided username and password
def authenticate_user(db, username: str, password: str):
    """
    Authenticate a user based on the provided username and password.

    Parameters:
    - db (dict): The user database.
    - username (str): The username of the user to authenticate.
    - password (str): The password of the user to authenticate.

    Returns:
    - Union[UserInDB, bool]: The authenticated user object if successful, False otherwise.
    """
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Create an access token using the provided data and expiration delta
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """
    Creates an access token using the provided data and expiration delta.

    Args:
        data (dict): The data to be encoded in the access token.
        expires_delta (timedelta, None): Optional expiration delta for the access token.
            If not provided, a default expiration of 15 minutes will be used.

    Returns:
        str: The encoded access token.

    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Return the current user based on the provided token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Retrieves the current user based on the provided token.

    Parameters:
    - token (str): The authentication token.

    Returns:
    - user (User): The user associated with the token.

    Raises:
    - HTTPException: If the credentials cannot be validated.
    """
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
    user = get_user(db_dummy, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Return the current active user based on the provided token
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current active user based on the provided token.

    Parameters:
    - current_user (User): The current user object.

    Returns:
    - User: The current active user.

    Raises:
    - HTTPException: If the user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
