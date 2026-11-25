from .BaseDataModel import BaseDataModel
from .db_schemes import User
from sqlalchemy.future import select
from typing import Optional
from uuid import UUID

class UserModel(BaseDataModel):

    def __init__(self, db_client):
        """Initialize the user model.

        Args:
            db_client: The asynchronous database session factory.
        """
        super().__init__(db_client=db_client)

    @classmethod
    async def create_instance(cls,db_client: object):
        """Create a user model instance.

        Args:
            db_client (object): The asynchronous database session factory.

        Returns:
            UserModel: The initialized user model.
        """
        instance = cls(db_client)
        return instance

    async def create_user(self, user: User) -> User:
        """Persist a user and refresh its database-generated fields.

        Args:
            user (User): The user to create.

        Returns:
            User: The created user.
        """
        async with self.db_client() as session:
            async with session.begin():
                session.add(user)

            await session.refresh(user)
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user from the database by its ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Optional[User]: The user, or None if no user with that ID exists.
        """
        async with self.db_client() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user from the database by email.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            Optional[User]: The user, or None if no user with that email exists.
        """
        async with self.db_client() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_user_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        """Retrieve a user from the database by UUID.

        Args:
            user_uuid (UUID): The UUID of the user to retrieve.

        Returns:
            Optional[User]: The user, or None if no user with that UUID exists.
        """
        async with self.db_client() as session:
            query = select(User).where(User.user_uuid == user_uuid)
            result = await session.execute(query)
            return result.scalar_one_or_none()
