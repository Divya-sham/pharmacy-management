from datetime import datetime
from extensions import db
from datetime import datetime,timezone

class MedicineDB(db.Model):
    __tablename__ = 'medicine_db'
    id = db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    stock=db.Column(db.Integer,nullable=False)
    price=db.Column(db.Float,nullable=False)
    expiration_date=db.Column(db.Date,nullable=False)
    category=db.Column(db.String(50),nullable=False)

class SaleDB(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    customer_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    doctor_name = db.Column(db.String(100))
    medicine_name = db.Column(db.String(100))
    quantity =  db.Column(db.Integer)
    price_per_unit = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))


