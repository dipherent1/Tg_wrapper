from sqlalchemy.orm import Session

from app.domain import models, schemas

class UserRepo:

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, user_data: schemas.UserCreate) -> models.User:
        """
        Finds a user by their Telegram ID. If they don't exist, creates them.
        This is the most common pattern for bots.
        """
        db_user = self.db.query(models.User).filter(
            models.User.telegram_user_id == user_data.telegram_user_id
        ).first()

        if db_user:
            # Optionally update fields like first_name or username if they change
            # db_user.first_name = user_data.first_name
            # self.db.commit()
            return db_user
        
        # User does not exist, so create a new one
        db_user = models.User(
            telegram_user_id=user_data.telegram_user_id,
            first_name=user_data.first_name,
            username=user_data.username
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user