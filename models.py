from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    openid = db.Column(db.String(100), primary_key=True, unique=True, nullable=False)
    phone_number = db.Column(db.String(200), nullable=False)  # 加密存储的手机号
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.openid}>'

class BlessingMessage(db.Model):
    __tablename__ = 'blessing_messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_openid = db.Column(db.String(100), db.ForeignKey('users.openid'), nullable=False)
    receiver_phone = db.Column(db.String(200), nullable=False)  # 加密存储的手机号
    content = db.Column(db.String(100), nullable=False)  # 祝福内容，最多80个字符
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, sent, failed
    
    # 建立关系
    sender = db.relationship('User', backref=db.backref('blessings', lazy=True))
    
    def __repr__(self):
        return f'<BlessingMessage {self.id}>'
