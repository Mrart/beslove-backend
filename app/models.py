from app.app import db
from datetime import datetime, timedelta

class User(db.Model):
    __tablename__ = 'users'
    
    openid = db.Column(db.String(100), primary_key=True, unique=True, nullable=False)
    phone_number = db.Column(db.String(200), nullable=False)  # 加密存储的手机号
    nick_name = db.Column(db.String(50), nullable=True)  # 用户微信昵称
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
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)  # 是否被发送者删除
    
    # 建立关系
    sender = db.relationship('User', backref=db.backref('blessings', lazy=True))
    
    def __repr__(self):
        return f'<BlessingMessage {self.id}>'

class SmsVerification(db.Model):
    __tablename__ = 'sms_verifications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(200), nullable=False)  # 加密存储的手机号
    verification_code = db.Column(db.String(10), nullable=False)  # 验证码
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 创建时间
    expires_at = db.Column(db.DateTime, nullable=False)  # 过期时间
    used = db.Column(db.Boolean, nullable=False, default=False)  # 是否已使用
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置默认过期时间为10分钟后
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    def __repr__(self):
        return f'<SmsVerification {self.id}>'
    
    def is_valid(self):
        """检查验证码是否有效"""
        return not self.used and datetime.utcnow() < self.expires_at
