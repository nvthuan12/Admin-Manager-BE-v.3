from project.models import db

class Permission(db.Model):
    __tablename__ = "permission"
    permission_id = db.Column(db.Integer, primary_key=True)
    permission_name = db.Column(db.String(80), nullable=False)
    role_has_permission = db.relationship('RoleHasPermission', backref='permission')