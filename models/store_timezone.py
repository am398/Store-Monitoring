from models import db
from models.base import Base
class StoreTimezone(Base):
    __tablename__ = 'store_timezones'

    store_id = db.Column(db.Integer, nullable=False)
    timezone_str = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<StoreTimezone {self.id} {self.store_id} {self.timezone_str}>"