from src.models import db

class Country(db.Model):
    __tablename__ = "countries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    iso_code = db.Column(db.String(2), nullable=False, unique=True)
    iso_code_3 = db.Column(db.String(3), nullable=True)
    iso_num = db.Column(db.String(3), nullable=True)
    calling_code = db.Column(db.String(8), nullable=True)

    def __repr__(self):
        return f"<Country {self.name} ({self.iso_code}) - {self.calling_code}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "iso_code": self.iso_code,
            "iso_code_3": self.iso_code_3,
            "iso_num": self.iso_num,
            "calling_code": self.calling_code
        }
