from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class SignInRequest(BaseModel):
    email: EmailStr
    password: str
    
class RefreshRequest(BaseModel):
    refresh_token: str
    
class JwtAuthResponse(BaseModel):
    access_token: str
    refresh_token: str