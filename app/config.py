import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'beslove.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 微信小程序配置
    WX_APP_ID = os.environ.get('WX_APP_ID')
    WX_APP_SECRET = os.environ.get('WX_APP_SECRET')
    
    # 阿里云短信配置
    ALIYUN_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID')
    ALIYUN_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
    ALIYUN_SMS_SIGN_NAME = 'BesLove'
    ALIYUN_SMS_TEMPLATE_CODE = os.environ.get('ALIYUN_SMS_TEMPLATE_CODE')
    
    # 加密配置
    AES_KEY = os.environ.get('AES_KEY') or 'a32-byte-encryption-key-for-aes-256-cbc'
    AES_IV = os.environ.get('AES_IV') or 'a-16-byte-iv-value'
    
    # 风控配置
    SENDER_DAILY_LIMIT = 3  # 同一发送者24小时最多发送3条
    RECEIVER_DAILY_LIMIT = 2  # 同一接收者24小时最多接收2条
    
    # 短信模板
    SMS_TEMPLATE = '''【BesLove】💌 你有一条来自心动之人的消息：

{content}

—— 愿每一份真心都不被辜负'''
