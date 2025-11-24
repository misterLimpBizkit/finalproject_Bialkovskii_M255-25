import hashlib
import secrets
from datetime import datetime


class User:
    def __init__(self, user_id: int, username: str, password: str, registration_date: datetime):
        if len(password) < 4:
            raise ValueError("Пароль должен быть больше 4 символов")
        self._user_id = user_id
        self._username = username
        self._salt = secrets.token_hex(16)
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now() 
        

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    @property
    def get_user_info(self):
        '''Display user info'''
        return {
            'user_id': self._user_id,
            'username': self._username,
            'registraion_date': self._registration_date
            }
    
    @property.setter
    def change_password(self, new_password: str):
        '''Change user password'''
        if new_password < 4:
            raise ValueError('Пароль должен быть больше 4 символов')
        self._salt = secrets.token_hex(16)
        self._hashed_password = self._hash_password(new_password, self._salt)

    def varify_password(self, password: str) -> bool:
        '''Verify user password'''
        if password < 4:
            return False
        return self._hashed_password == self._hash_password(password, self._salt)
    
    @property
    def user_id(self) -> int:
        '''Get user id'''
        return self._user_id
    
    @property
    def username(self) -> str:
        '''Get username'''
        return self._username
    
    @property.setter
    def change_username(self, new_username: str):
        '''Change username'''
        if not new_username:
            return ValueError("Имя не может быть пустым")
        self._username = new_username

    @property
    def salt(self) -> str:
        '''Display salt'''
        return self._salt
    
    @property
    def hashed_password(self) -> str:
        '''Display hashed password'''
        return self._hashed_password
    
    @property
    def registration_date(self) -> datetime:
        '''Display registration date'''
        return self._registration_date




        
        

