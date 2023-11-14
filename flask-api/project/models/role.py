from project.models import db

class Role(db.Model):
    __tablename__ = "role"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(80), nullable=False)
    user_has_role = db.relationship('UserHasRole', backref='role')
