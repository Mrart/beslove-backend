import uuid
import config
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

class AliyunSMS:
    """阿里云短信发送类"""
    
    def __init__(self):
        # 初始化阿里云客户端
        self.client = AcsClient(
            config.Config.ALIYUN_ACCESS_KEY_ID,
            config.Config.ALIYUN_ACCESS_KEY_SECRET,
            'cn-hangzhou'
        )
        
        self.sign_name = config.Config.ALIYUN_SMS_SIGN_NAME
        self.template_code = config.Config.ALIYUN_SMS_TEMPLATE_CODE
    
    def send_sms(self, phone_number, content):
        """发送短信"""
        try:
            # 构建短信内容
            sms_content = config.Config.SMS_TEMPLATE.format(content=content)
            
            # 创建请求
            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            # 设置请求参数
            request.add_query_param('PhoneNumbers', phone_number)
            request.add_query_param('SignName', self.sign_name)
            request.add_query_param('TemplateCode', self.template_code)
            request.add_query_param('TemplateParam', f'{{"content":"{content}"}}')
            request.add_query_param('OutId', str(uuid.uuid4()))
            
            # 发送请求
            response = self.client.do_action_with_exception(request)
            
            # 解析响应
            response_str = response.decode('utf-8')
            import json
            response_data = json.loads(response_str)
            
            if response_data.get('Code') == 'OK':
                return True, response_data.get('Message', '发送成功')
            else:
                return False, response_data.get('Message', '发送失败')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, str(e)


# 初始化短信发送实例
sms_client = AliyunSMS()
