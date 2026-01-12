from flask import request, jsonify, make_response
import json
from app import app, db
from models import User, BlessingMessage
from utils import crypto_util, sensitive_filter, validate_phone, validate_blessing_content
from datetime import datetime, timedelta
import requests
import config
from sms import sms_client

@app.route('/api/wx/get_openid', methods=['POST'])
def wx_get_openid():
    """获取微信用户openid接口"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 调用微信API获取openid
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.Config.WX_APP_ID}&secret={config.Config.WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        wx_response = requests.get(wx_url)
        wx_result = wx_response.json()
        
        if 'errcode' in wx_result:
            response_data = {
                'code': 400, 
                'message': '获取openid失败',
                'wx_error': {
                    'errcode': wx_result.get('errcode'),
                    'errmsg': wx_result.get('errmsg')
                }
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 返回openid
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': {
                'openid': wx_result.get('openid')
            }
        }
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        app.logger.error(f'获取openid失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response


@app.route('/api/wx/login', methods=['POST'])
def wx_login():
    """微信授权登录接口"""
    try:
        data = request.get_json()
        code = data.get('code')
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        
        if not code or not encrypted_data or not iv:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 1. 调用微信API获取session_key和openid
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.Config.WX_APP_ID}&secret={config.Config.WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        wx_response = requests.get(wx_url)
        wx_result = wx_response.json()
        
        if 'errcode' in wx_result:
            response_data = {
                'code': 400, 
                'message': '微信登录失败',
                'wx_error': {
                    'errcode': wx_result.get('errcode'),
                    'errmsg': wx_result.get('errmsg')
                }
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        openid = wx_result.get('openid')
        session_key = wx_result.get('session_key')
        
        # 2. 解密手机号
        success, phone_number = crypto_util.decrypt_wx_phone(encrypted_data, iv, wx_result.get('session_key'))
        if not success:
            response_data = {
                'code': 400, 
                'message': '手机号解密失败',
                'error': phone_number
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 3. 验证手机号格式
        if not validate_phone(phone_number):
            response_data = {
                'code': 400, 
                'message': '手机号格式不正确'
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 4. 保存或更新用户信息
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
        
        # 5. 返回登录结果（脱敏手机号）
        desensitized_phone = phone_number[:3] + '****' + phone_number[-4:]
        response_data = {
            'code': 200,
            'message': '登录成功',
            'data': {
                'openid': openid,
                'phone': desensitized_phone  # 返回脱敏后的手机号
            }
        }
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        app.logger.error(f'微信登录失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response


@app.route('/api/blessing/send', methods=['POST'])
def send_blessing():
    """发送祝福接口"""
    try:
        data = request.get_json()
        sender_openid = data.get('sender_openid')
        receiver_phone = data.get('receiver_phone')
        content = data.get('content')
        
        if not sender_openid or not receiver_phone or not content:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 1. 获取发送者信息
        sender = User.query.filter_by(openid=sender_openid).first()
        if not sender:
            response_data = {'code': 401, 'message': '用户未登录'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        sender_phone = crypto_util.decrypt(sender.phone_number)
        
        # 2. 验证手机号
        if not validate_phone(receiver_phone):
            response_data = {'code': 400, 'message': '手机号格式不正确'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 3. 禁止发送给自己
        if receiver_phone == sender_phone:
            response_data = {'code': 400, 'message': '不能发送给自己'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 4. 验证祝福内容
        if not validate_blessing_content(content):
            response_data = {'code': 400, 'message': '祝福内容不能为空且不能超过80个字符'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 5. 敏感词检查
        if sensitive_filter.contains_sensitive_word(content):
            response_data = {'code': 400, 'message': '祝福内容包含敏感词'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 6. 风控检查
        # 6.1 发送者24小时发送限制
        sender_limit = config.Config.SENDER_DAILY_LIMIT
        sender_count = BlessingMessage.query.filter_by(
            sender_openid=sender_openid
        ).filter(
            BlessingMessage.sent_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        if sender_count >= sender_limit:
            response_data = {'code': 400, 'message': '您今天发送的祝福已达上限'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
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
            response_data = {'code': 400, 'message': '该接收者今天接收的祝福已达上限'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
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
                
                response_data = {
                    'code': 200,
                    'message': '祝福发送成功',
                    'data': {
                        'receiver_phone': receiver_phone[:3] + '****' + receiver_phone[-4:],
                        'message': '愿TA一眼认出是你'
                    }
                }
                response = make_response(json.dumps(response_data, ensure_ascii=False))
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response
            else:
                blessing.status = 'failed'
                db.session.commit()
                app.logger.error(f'短信发送失败: {message}')
                response_data = {'code': 500, 'message': '短信发送失败，请稍后重试'}
                response = make_response(json.dumps(response_data, ensure_ascii=False))
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response
                
        except Exception as e:
            app.logger.error(f'短信发送异常: {str(e)}')
            blessing.status = 'failed'
            db.session.commit()
            response_data = {'code': 500, 'message': '短信发送失败，请稍后重试'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
    except Exception as e:
        app.logger.error(f'发送祝福失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response


@app.route('/api/user/phone', methods=['GET'])
def get_user_phone():
    """获取用户手机号接口"""
    try:
        # 获取请求参数
        openid = request.args.get('openid')
        
        if not openid:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 查询用户信息
        user = User.query.filter_by(openid=openid).first()
        if not user:
            response_data = {'code': 404, 'message': '用户不存在'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 解密手机号并脱敏
        phone_number = crypto_util.decrypt(user.phone_number)
        desensitized_phone = phone_number[:3] + '****' + phone_number[-4:]
        
        # 返回结果
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': {
                'phone': desensitized_phone
            }
        }
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        app.logger.error(f'获取用户手机号失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response


@app.route('/api/blessing/templates', methods=['GET'])
def get_blessing_templates():
    """获取祝福模板接口"""
    templates = [
        # 爱情相关
        '今天特别想你',
        '我的心永远属于你',
        '遇见你是我最幸运的事',
        '和你在一起的每一天都是情人节',
        '你是我生命中最美的风景',
        '我永远爱你',
        '你是我的唯一',
        '有你真好',
        '想你了，期待与你相见',
        '距离无法阻挡我对你的思念',
        
        # 道歉相关
        '对不起，我错了',
        '请原谅我的冲动',
        '我不该那样对你',
        '给我一个弥补的机会好吗',
        
        # 生日相关
        '生日快乐，我的光',
        '祝你生日快乐，天天开心',
        '愿你永远年轻美丽',
        '生日祝福：健康快乐，幸福永远',
        
        # 感谢相关
        '谢谢你一直在我身边',
        '感谢你为我做的一切',
        '感恩有你',
        '谢谢你的帮助',
        '你的好意我永远不会忘记',
        
        # 友情相关
        '有你这样的朋友真好',
        '感谢一路有你陪伴',
        '朋友一生一起走',
        '你的支持是我最大的动力',
        '每当想起你，心里就暖暖的',
        
        # 鼓励相关
        '相信自己，你一定可以',
        '困难只是暂时的，坚持就是胜利',
        '你已经做得很好了',
        '明天会更好',
        '继续加油，我支持你'
    ]
    
    # 使用json.dumps控制编码
    response_data = {
        'code': 200,
        'message': '获取成功',
        'data': {'templates': templates}
    }
    
    # 创建响应，设置正确的编码
    response = make_response(json.dumps(response_data, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
