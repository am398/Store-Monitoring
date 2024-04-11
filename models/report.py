from models import db
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.String(36), primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(255))

    def __repr__(self):
        return f"<Report {self.id} {self.status}>"