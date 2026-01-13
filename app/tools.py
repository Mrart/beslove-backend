from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import re
from app.config import Config

# 加密函数 - AES-256
def encrypt(data):
    """使用AES-256加密数据"""
    cipher = AES.new(Config.AES_KEY.encode('utf-8'), AES.MODE_CBC, Config.AES_IV.encode('utf-8'))
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return encrypted_data.hex()

# 解密函数 - AES-256
def decrypt(encrypted_data):
    """使用AES-256解密数据"""
    cipher = AES.new(Config.AES_KEY.encode('utf-8'), AES.MODE_CBC, Config.AES_IV.encode('utf-8'))
    decrypted_data = cipher.decrypt(bytes.fromhex(encrypted_data))
    unpadded_data = unpad(decrypted_data, AES.block_size)
    return unpadded_data.decode('utf-8')

# 手机号正则验证
def validate_phone(phone):
    """验证是否为中国大陆手机号"""
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

# 敏感词过滤
def filter_sensitive_words(content):
    """过滤敏感词，返回过滤后的内容"""
    # 简单敏感词列表，实际项目中应从数据库或配置文件加载
    sensitive_words = ['敏感词1', '敏感词2', '广告', '联系方式', '政治', '辱骂']
    
    filtered_content = content
    for word in sensitive_words:
        filtered_content = filtered_content.replace(word, '*' * len(word))
    
    return filtered_content

# 检查内容是否包含敏感词
def contains_sensitive_words(content):
    """检查内容是否包含敏感词"""
    sensitive_words = ['敏感词1', '敏感词2', '广告', '联系方式', '政治', '辱骂']
    
    for word in sensitive_words:
        if word in content:
            return True
    
    return False

# 格式化手机号（脱敏显示）
def format_phone(phone):
    """将手机号格式化为138****1234格式"""
    if len(phone) == 11:
        return phone[:3] + '****' + phone[-4:]
    return phone
