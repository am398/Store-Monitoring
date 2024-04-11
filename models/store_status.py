from models import db
from models.base import Base

class StoreStatus(Base):
    __tablename__ = 'store_status'

    store_id = db.Column(db.Integer, nullable=False)
    timestamp_utc = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<StoreStatus {self.id} {self.store_id} {self.timestamp_utc} {self.status}>"