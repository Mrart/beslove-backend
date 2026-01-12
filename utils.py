from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import re
import base64
import json
from config import Config

class CryptoUtil:
    """加密解密工具类"""
    
    def __init__(self):
        self.key = Config.AES_KEY.encode('utf-8')
        self.iv = Config.AES_IV.encode('utf-8')
    
    def encrypt(self, text):
        """AES加密"""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted_data = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_text):
        """AES解密"""
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted_data = base64.b64decode(encrypted_text)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_data.decode('utf-8')
    
    def decrypt_wx_phone(self, encrypted_data, iv, session_key):
        """微信手机号解密"""
        try:
            # 使用session_key作为AES密钥
            session_key_bytes = base64.b64decode(session_key)
            iv_bytes = base64.b64decode(iv)
            encrypted_data_bytes = base64.b64decode(encrypted_data)
            
            cipher = AES.new(session_key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_data = unpad(cipher.decrypt(encrypted_data_bytes), AES.block_size)
            decrypted_data_str = decrypted_data.decode('utf-8')
            
            # 解析JSON数据
            phone_info = json.loads(decrypted_data_str)
            return True, phone_info.get('phoneNumber')
        except Exception as e:
            return False, str(e)


class SensitiveWordFilter:
    """敏感词过滤器"""
    
    def __init__(self):
        # 基础敏感词列表
        self.sensitive_words = [
            # 政治敏感词
            '敏感词1', '敏感词2',
            # 广告联系方式
            '微信', 'wx', 'QQ', 'qq', '电话', '手机号',
            # 辱骂词汇
            '傻逼', 'fuck', 'shit',
            # 其他敏感内容
            '赌博', '色情', '毒品'
        ]
        self.pattern = re.compile('|'.join(re.escape(word) for word in self.sensitive_words), re.IGNORECASE)
    
    def contains_sensitive_word(self, text):
        """检查文本是否包含敏感词"""
        return bool(self.pattern.search(text))
    
    def filter_sensitive_words(self, text):
        """过滤敏感词，用*替换"""
        return self.pattern.sub('*' * 4, text)


# 验证工具函数
def validate_phone(phone):
    """验证中国大陆手机号"""
    pattern = re.compile(r'^1[3-9]\d{9}$')
    return bool(pattern.match(phone))


def validate_blessing_content(content):
    """验证祝福内容"""
    if not content or len(content.strip()) == 0:
        return False
    if len(content) > 80:
        return False
    return True


# 初始化工具实例
crypto_util = CryptoUtil()
sensitive_filter = SensitiveWordFilter()
