from models import db
from models.base import Base

class BusinessHour(Base):
    __tablename__ = 'business_hours'

    store_id = db.Column(db.Integer, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time_local = db.Column(db.Time, nullable=False)
    end_time_local = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f"<BusinessHour {self.store_id} {self.day_of_week} {self.start_time_local} {self.end_time_local}>"