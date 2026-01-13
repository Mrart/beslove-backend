from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import re
import base64
import json
from app.config import Config
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
            logger.info(f'开始解密微信手机号，encrypted_data长度: {len(encrypted_data)}, iv长度: {len(iv)}, session_key长度: {len(session_key)}')
            
            # 参数有效性检查
            if not encrypted_data or not iv or not session_key:
                logger.error('解密参数为空: encrypted_data=%s, iv=%s, session_key=%s', 
                           encrypted_data is not None, iv is not None, session_key is not None)
                return False, '参数不能为空'
            
            # 解密前的数据格式转换
            try:
                session_key_bytes = base64.b64decode(session_key)
                iv_bytes = base64.b64decode(iv)
                encrypted_data_bytes = base64.b64decode(encrypted_data)
                logger.info('Base64解码成功，session_key_bytes长度: %d, iv_bytes长度: %d, encrypted_data_bytes长度: %d',
                           len(session_key_bytes), len(iv_bytes), len(encrypted_data_bytes))
            except Exception as e:
                logger.error('Base64解码失败: %s', str(e))
                return False, f'Base64解码失败: {str(e)}'
            
            # AES解密
            try:
                cipher = AES.new(session_key_bytes, AES.MODE_CBC, iv_bytes)
                decrypted_data = cipher.decrypt(encrypted_data_bytes)
                logger.info('AES解密成功，解密数据长度: %d', len(decrypted_data))
            except Exception as e:
                logger.error('AES解密失败: %s', str(e))
                return False, f'AES解密失败: {str(e)}'
            
            # 移除填充
            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
                logger.info('移除填充成功，移除后数据长度: %d', len(decrypted_data))
            except Exception as e:
                logger.error('移除填充失败: %s', str(e))
                return False, f'移除填充失败: {str(e)}'
            
            # 转换为字符串
            try:
                decrypted_data_str = decrypted_data.decode('utf-8')
                logger.info('解密数据转换为字符串成功，前50个字符: %s', decrypted_data_str[:50] + '...' if len(decrypted_data_str) > 50 else decrypted_data_str)
            except Exception as e:
                logger.error('解密数据转换为字符串失败: %s', str(e))
                return False, f'解密数据转换为字符串失败: {str(e)}'
            
            # 解析JSON数据
            try:
                phone_info = json.loads(decrypted_data_str)
                logger.info('解析JSON成功，数据包含phoneNumber: %s', 'phoneNumber' in phone_info)
            except Exception as e:
                logger.error('解析JSON失败: %s', str(e))
                logger.error('解密后的数据内容: %s', decrypted_data_str)
                return False, f'解析JSON失败: {str(e)}'
            
            # 获取手机号
            phone_number = phone_info.get('phoneNumber')
            if not phone_number:
                logger.error('JSON中没有找到phoneNumber字段，数据: %s', phone_info)
                return False, 'JSON中没有找到phoneNumber字段'
            
            logger.info('微信手机号解密成功: %s', phone_number[:3] + '****' + phone_number[-4:])
            return True, phone_number
            
        except Exception as e:
            logger.exception('微信手机号解密过程中发生意外错误')
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
