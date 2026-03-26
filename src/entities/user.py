from sqlalchemy import Column, Integer, String, DateTime, func
from typing import Dict, Any

from db.postgres import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    @property
    def jwt_subject(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
        }