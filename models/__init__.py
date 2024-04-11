from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    
    from models.business_hour import BusinessHour
    from models.report import Report
    from models.store_status import StoreStatus
    from models.store_timezone import StoreTimezone