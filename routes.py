from flask import request, jsonify
from app import app, db
from models import User, BlessingMessage
from utils import crypto_util, sensitive_filter, validate_phone, validate_blessing_content
from datetime import datetime, timedelta
import requests
import config
from sms import sms_client

@app.route('/api/wx/login', methods=['POST'])
def wx_login():
    """微信授权登录接口"""
    try:
        data = request.get_json()
        code = data.get('code')
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        
        if not code or not encrypted_data or not iv:
            return jsonify({'code': 400, 'message': '参数错误'})
        
        # 1. 调用微信API获取session_key和openid
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.Config.WX_APP_ID}&secret={config.Config.WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        wx_response = requests.get(wx_url)
        wx_result = wx_response.json()
        
        if 'errcode' in wx_result:
            return jsonify({'code': 400, 'message': '微信登录失败'})
        
        openid = wx_result.get('openid')
        session_key = wx_result.get('session_key')
        
        # 2. 解密手机号
        # 注意：这里需要使用微信提供的解密算法，实际项目中需要实现完整的解密逻辑
        # 简化处理，假设encrypted_data中包含手机号
        phone_number = '13800138000'  # 实际应该从解密结果中获取
        
        # 3. 保存或更新用户信息
        user = User.query.filter_by(openid=openid).first()
        if not user:
            # 创建新用户
            encrypted_phone = crypto_util.encrypt(phone_number)
            user = User(
                openid=openid,
                phone_number=encrypted_phone
            )
            db.session.add(user)
            db.session.commit()
        
        # 4. 返回登录结果
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'openid': openid,
                'phone': phone_number  # 实际项目中不应返回完整手机号
            }
        })
        
    except Exception as e:
        app.logger.error(f'微信登录失败: {str(e)}')
        return jsonify({'code': 500, 'message': '服务器内部错误'})


@app.route('/api/blessing/send', methods=['POST'])
def send_blessing():
    """发送祝福接口"""
    try:
        data = request.get_json()
        sender_openid = data.get('sender_openid')
        receiver_phone = data.get('receiver_phone')
        content = data.get('content')
        
        if not sender_openid or not receiver_phone or not content:
            return jsonify({'code': 400, 'message': '参数错误'})
        
        # 1. 获取发送者信息
        sender = User.query.filter_by(openid=sender_openid).first()
        if not sender:
            return jsonify({'code': 401, 'message': '用户未登录'})
        
        sender_phone = crypto_util.decrypt(sender.phone_number)
        
        # 2. 验证手机号
        if not validate_phone(receiver_phone):
            return jsonify({'code': 400, 'message': '手机号格式不正确'})
        
        # 3. 禁止发送给自己
        if receiver_phone == sender_phone:
            return jsonify({'code': 400, 'message': '不能发送给自己'})
        
        # 4. 验证祝福内容
        if not validate_blessing_content(content):
            return jsonify({'code': 400, 'message': '祝福内容不能为空且不能超过80个字符'})
        
        # 5. 敏感词检查
        if sensitive_filter.contains_sensitive_word(content):
            return jsonify({'code': 400, 'message': '祝福内容包含敏感词'})
        
        # 6. 风控检查
        # 6.1 发送者24小时发送限制
        sender_limit = config.Config.SENDER_DAILY_LIMIT
        sender_count = BlessingMessage.query.filter_by(
            sender_openid=sender_openid
        ).filter(
            BlessingMessage.sent_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        if sender_count >= sender_limit:
            return jsonify({'code': 400, 'message': '您今天发送的祝福已达上限'})
        
        # 6.2 接收者24小时接收限制
        receiver_limit = config.Config.RECEIVER_DAILY_LIMIT
        # 加密接收者手机号进行查询
        encrypted_receiver_phone = crypto_util.encrypt(receiver_phone)
        receiver_count = BlessingMessage.query.filter_by(
            receiver_phone=encrypted_receiver_phone
        ).filter(
            BlessingMessage.sent_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        if receiver_count >= receiver_limit:
            return jsonify({'code': 400, 'message': '该接收者今天接收的祝福已达上限'})
        
        # 7. 记录祝福消息
        encrypted_receiver_phone = crypto_util.encrypt(receiver_phone)
        blessing = BlessingMessage(
            sender_openid=sender_openid,
            receiver_phone=encrypted_receiver_phone,
            content=content,
            status='pending'
        )
        db.session.add(blessing)
        db.session.commit()
        
        # 8. 发送短信
        try:
            # 调用阿里云短信API发送短信
            success, message = sms_client.send_sms(receiver_phone, content)
            
            if success:
                blessing.status = 'sent'
                db.session.commit()
                
                return jsonify({
                    'code': 200,
                    'message': '祝福发送成功',
                    'data': {
                        'receiver_phone': receiver_phone[:3] + '****' + receiver_phone[-4:],
                        'message': '愿TA一眼认出是你'
                    }
                })
            else:
                blessing.status = 'failed'
                db.session.commit()
                app.logger.error(f'短信发送失败: {message}')
                return jsonify({'code': 500, 'message': '短信发送失败，请稍后重试'})
                
        except Exception as e:
            app.logger.error(f'短信发送异常: {str(e)}')
            blessing.status = 'failed'
            db.session.commit()
            return jsonify({'code': 500, 'message': '短信发送失败，请稍后重试'})
        
    except Exception as e:
        app.logger.error(f'发送祝福失败: {str(e)}')
        return jsonify({'code': 500, 'message': '服务器内部错误'})


@app.route('/api/blessing/templates', methods=['GET'])
def get_blessing_templates():
    """获取祝福模板接口"""
    templates = [
        '今天特别想你',
        '对不起，我错了',
        '生日快乐，我的光',
        '谢谢你一直在我身边'
    ]
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': {'templates': templates}
    })
