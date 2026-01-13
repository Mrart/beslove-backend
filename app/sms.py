import uuid
import logging
from app.config import Config
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

# 获取日志记录器
logger = logging.getLogger(__name__)

class AliyunSMS:
    """阿里云短信发送类"""
    
    def __init__(self):
        # 初始化阿里云客户端
        self.client = AcsClient(
            Config.ALIYUN_ACCESS_KEY_ID,
            Config.ALIYUN_ACCESS_KEY_SECRET,
            'cn-hangzhou'
        )
        
        self.sign_name = Config.ALIYUN_SMS_SIGN_NAME
        self.template_code = Config.ALIYUN_SMS_TEMPLATE_CODE
    
    def send_sms(self, phone_number, content):
        """发送短信"""
        try:
            logger.info(f"开始发送短信，手机号: {phone_number}, 内容: {content}")
            
            # 验证参数
            if not phone_number or not content:
                logger.error("发送短信失败：手机号或内容为空")
                return False, "手机号或内容不能为空"
            
            # 构建短信内容
            sms_content = Config.SMS_TEMPLATE.format(content=content)
            logger.debug(f"构建的短信内容: {sms_content}")
            
            # 创建请求
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            # 设置请求参数
            out_id = str(uuid.uuid4())
            request.add_query_param('PhoneNumbers', phone_number)
            request.add_query_param('SignName', self.sign_name)
            request.add_query_param('TemplateCode', self.template_code)
            request.add_query_param('TemplateParam', f'{{"content":"{content}"}}')
            request.add_query_param('OutId', out_id)
            
            logger.debug(f"请求参数：手机号={phone_number}, 签名={self.sign_name}, 模板={self.template_code}")
            logger.debug(f"模板参数：{{\"content\":\"{content}\"}}, OutId={out_id}")
            
            # 发送请求
            logger.info("发送短信请求到阿里云")
            response = self.client.do_action_with_exception(request)
            
            # 解析响应
            response_str = response.decode('utf-8')
            logger.debug(f"阿里云响应原始数据: {response_str}")
            
            import json
            response_data = json.loads(response_str)
            logger.info(f"阿里云响应解析后: {response_data}")
            
            code = response_data.get('Code')
            message = response_data.get('Message', '未知消息')
            request_id = response_data.get('RequestId')
            
            logger.info(f"短信发送结果：Code={code}, Message={message}, RequestId={request_id}")
            
            if code == 'OK':
                logger.info(f"短信发送成功，手机号: {phone_number}, RequestId: {request_id}")
                return True, message
            else:
                logger.error(f"短信发送失败，手机号: {phone_number}, Code: {code}, Message: {message}, RequestId: {request_id}")
                return False, f"{message} (Code: {code})"
                
        except Exception as e:
            import traceback
            logger.error(f"发送短信异常，手机号: {phone_number}, 异常信息: {str(e)}")
            logger.error("异常堆栈:")
            traceback.print_exc()
            return False, f"发送异常: {str(e)}"


# 初始化短信发送实例
sms_client = AliyunSMS()
