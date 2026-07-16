from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


async def delete_student_data(session: AsyncSession, user: User) -> None:
    if user.role != "student":
        raise ValueError("teacher account cannot be deleted through student privacy flow")
    await session.execute(delete(User).where(User.id == user.id))
