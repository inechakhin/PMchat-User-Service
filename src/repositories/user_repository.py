from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from typing import Dict, Any, Optional

from entities.user import User

class UserRepository:
    
    def __init__(self, session: AsyncSession):
        self.db = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def exists_by_email(self, email: str) -> bool:
        result = await self.db.execute(
            select(exists().where(User.email == email))
        )
        return result.scalar()
    
    async def create(self, create_data: Dict[str, Any]) -> User:
        user = User(**create_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, update_data: Dict[str, Any]) -> User:        
        for key, value in update_data.items():
            if value is not None:
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()