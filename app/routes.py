from flask import request, jsonify, make_response
import json
import requests
from app.app import app, db
from app.config import Config
from app.models import User
from app.utils import CryptoUtil
import logging

# 创建加密工具实例
crypto_util = CryptoUtil()

# 测试接口
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'Hello, World!'})

# 获取openid接口
@app.route('/api/wx/get_openid', methods=['GET'])
def wx_get_openid():
    """获取微信用户openid接口"""
    try:
        code = request.args.get('code')
        
        if not code:
            response_data = {'code': 400, 'message': '缺少code参数'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 调用微信API获取session_key和openid
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={Config.WX_APP_ID}&secret={Config.WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        wx_response = requests.get(wx_url)
        wx_result = wx_response.json()
        
        app.logger.info(f'微信openid获取请求，code: {code}, 微信返回: {wx_result}')
        
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
        
        openid = wx_result.get('openid')
        session_key = wx_result.get('session_key')
        
        # 验证用户是否存在
        # user = User.query.filter_by(openid=openid).first()
        # if not user:
        #     app.logger.info(f'openid获取成功但用户不存在，openid: {openid}')
        
        # 返回openid和session_key
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': {
                'openid': openid,
                'session_key': session_key
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

# 微信登录接口
@app.route('/api/wx/login', methods=['POST'])
def wx_login():
    """微信授权登录接口"""
    try:
        data = request.get_json()
        code = data.get('code')
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        
        app.logger.info(f'微信登录请求，code: {code}, encryptedData: {encrypted_data[:10]}..., iv: {iv}')
        
        if not code or not encrypted_data or not iv:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 1. 调用微信API获取session_key和openid
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={Config.WX_APP_ID}&secret={Config.WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        wx_response = requests.get(wx_url)
        wx_result = wx_response.json()
        
        app.logger.info(f'微信登录，调用微信API返回: {wx_result}')
        
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
        
        app.logger.info(f'微信登录，获取到openid: {openid}, session_key: {session_key[:10]}...')
        
        # 2. 解密手机号
        success, phone_number = crypto_util.decrypt_wx_phone(encrypted_data, iv, wx_result.get('session_key'))
        if not success:
            app.logger.error(f'微信登录，手机号解密失败: {phone_number}')
            response_data = {
                'code': 400, 
                'message': '手机号解密失败',
                'error': phone_number
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        app.logger.info(f'微信登录，解密得到手机号: {phone_number}')
        
        # 3. 验证手机号格式
        if not validate_phone(phone_number):
            app.logger.error(f'微信登录，手机号格式不正确: {phone_number}')
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
            app.logger.info(f'微信登录，创建新用户，openid: {openid}, 手机号: {phone_number}')
            encrypted_phone = crypto_util.encrypt(phone_number)
            user = User(
                openid=openid,
                phone_number=encrypted_phone
            )
            db.session.add(user)
            db.session.commit()
        else:
            app.logger.info(f'微信登录，用户已存在，更新信息，openid: {openid}')
            # 更新手机号
            encrypted_phone = crypto_util.encrypt(phone_number)
            user.phone_number = encrypted_phone
            db.session.commit()
            app.logger.info(f'微信登录，用户信息更新成功，openid: {openid}')
        
        # 5. 返回登录结果（脱敏手机号）
        desensitized_phone = phone_number[:3] + '****' + phone_number[-4:]
        app.logger.info(f'微信登录成功，openid: {openid}, 返回脱敏手机号: {desensitized_phone}')
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

# 微信手机号获取接口
@app.route('/api/wx/phone', methods=['GET'])
def wx_get_phone():
    """获取微信用户手机号接口"""
    try:
        code = request.args.get('code')
        openid = request.args.get('openid')
        
        app.logger.info(f'微信手机号获取请求，code: {code}, openid: {openid}')
        
        if not code or not openid:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 1. 获取微信access_token
        access_token_url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={Config.WX_APP_ID}&secret={Config.WX_APP_SECRET}'
        access_token_response = requests.get(access_token_url)
        access_token_result = access_token_response.json()
        
        app.logger.info(f'获取微信access_token返回: {access_token_result}')
        
        if 'errcode' in access_token_result:
            app.logger.error(f'获取微信access_token失败: {access_token_result}')
            response_data = {
                'code': 400,
                'message': '获取微信access_token失败',
                'wx_error': access_token_result
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        access_token = access_token_result.get('access_token')
        
        # 2. 调用微信phonenumber.getPhoneNumber接口
        phone_url = f'https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}'
        phone_payload = {'code': code}
        phone_response = requests.post(phone_url, json=phone_payload)
        phone_result = phone_response.json()
        
        app.logger.info(f'调用微信getPhoneNumber返回: {phone_result}')
        
        if 'errcode' in phone_result and phone_result['errcode'] != 0:
            app.logger.error(f'调用微信getPhoneNumber失败: {phone_result}')
            response_data = {
                'code': 400,
                'message': '获取手机号失败',
                'wx_error': phone_result
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 3. 获取手机号数据
        phone_info = phone_result.get('phone_info')
        if not phone_info:
            app.logger.error(f'微信返回数据中缺少phone_info: {phone_result}')
            response_data = {'code': 400, 'message': '获取手机号数据失败'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 检查是否有直接的手机号字段（微信API可能直接返回明文）
        phone_number = phone_info.get('phoneNumber')
        if not phone_number:
            # 如果没有直接的手机号，尝试解密
            encrypted_data = phone_info.get('encryptedData')
            iv = phone_info.get('iv')
            session_key = phone_info.get('session_key')
            
            # 4. 解密手机号
            success, phone_number = crypto_util.decrypt_wx_phone(encrypted_data, iv, session_key)
            if not success:
                app.logger.error(f'微信手机号解密失败: {phone_number}')
                response_data = {
                    'code': 400,
                    'message': '手机号解密失败',
                    'error': phone_number
                }
                response = make_response(json.dumps(response_data, ensure_ascii=False))
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response
        
        app.logger.info(f'获取微信手机号成功: {phone_number}')
        
        # 5. 验证手机号格式
        if not validate_phone(phone_number):
            app.logger.error(f'手机号格式不正确: {phone_number}')
            response_data = {
                'code': 400,
                'message': '手机号格式不正确'
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 6. 保存或更新用户信息
        user = User.query.filter_by(openid=openid).first()
        if not user:
            # 创建新用户
            app.logger.info(f'创建新用户，openid: {openid}, 手机号: {phone_number}')
            encrypted_phone = crypto_util.encrypt(phone_number)
            user = User(
                openid=openid,
                phone_number=encrypted_phone
            )
            db.session.add(user)
        else:
            app.logger.info(f'用户已存在，更新手机号，openid: {openid}, 手机号: {phone_number}')
            # 更新手机号
            encrypted_phone = crypto_util.encrypt(phone_number)
            user.phone_number = encrypted_phone
        
        db.session.commit()
        app.logger.info(f'用户手机号更新成功，openid: {openid}')
        
        # 7. 返回完整手机号
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': {
                'phone': phone_number
            }
        }
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        app.logger.error(f'获取微信手机号失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

# 获取祝福模板接口
@app.route('/api/blessing/templates', methods=['GET'])
def get_blessing_templates():
    """获取祝福模板接口"""
    try:
        # 返回祝福模板列表
        templates = [
            {
                "id": 1,
                "type": "love",
                "title": "爱情表白",
                "content": "亲爱的{name}，今天特别想告诉你：与你相遇是我生命中最美好的事情，你的笑容照亮了我的每一天。愿我们的爱情永远甜蜜幸福！"
            },
            {
                "id": 2,
                "type": "apology",
                "title": "道歉信",
                "content": "{name}，我知道我错了，让你伤心难过。请你原谅我的冲动和自私，我会努力改正，给你更多的理解和关心。对不起，我爱你！"
            },
            {
                "id": 3,
                "type": "birthday",
                "title": "生日祝福",
                "content": "亲爱的{name}，祝你生日快乐！愿你的每一天都充满阳光和快乐，所有的梦想都能实现。在这个特别的日子里，我想对你说：有你在真好！"
            },
            {
                "id": 4,
                "type": "thanks",
                "title": "感谢有你",
                "content": "{name}，谢谢你一直以来的陪伴和支持。在我遇到困难的时候，你总是第一个伸出援手；在我开心的时候，你总是和我分享喜悦。有你这样的朋友，我感到无比幸运！"
            },
            {
                "id": 5,
                "type": "friendship",
                "title": "友情祝福",
                "content": "{name}，我们的友谊就像美酒一样，越陈越香。无论距离多远，时间多久，我都会珍惜这份情谊。愿我们的友谊天长地久！"
            },
            {
                "id": 6,
                "type": "encouragement",
                "title": "鼓励支持",
                "content": "{name}，我知道你现在面临挑战，但请相信自己的能力。你是最棒的，一定能够克服困难，实现目标。我会一直支持你！"
            }
        ]
        
        response_data = {
            "code": 200,
            "message": "获取成功",
            "data": templates
        }
        
        # 使用json.dumps和make_response解决中文乱码问题
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        app.logger.error(f'获取祝福模板失败: {str(e)}')
        response_data = {'code': 500, 'message': '服务器内部错误'}
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

# 发送祝福接口
@app.route('/api/blessing/send', methods=['POST'])
def send_blessing():
    """发送祝福接口"""
    try:
        data = request.get_json()
        sender_openid = data.get('sender_openid')
        receiver_phone = data.get('receiver_phone')
        content = data.get('content')
        
        app.logger.info(f'发送祝福请求，发送者openid: {sender_openid}, 接收者手机号: {receiver_phone}')
        
        if not sender_openid or not receiver_phone or not content:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # TODO: 实现发送祝福的逻辑，如存储祝福记录、发送短信等
        
        response_data = {
            'code': 200,
            'message': '发送成功',
            'data': {
                'sender_openid': sender_openid,
                'receiver_phone': receiver_phone,
                'content': content
            }
        }
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
        
        app.logger.info(f'获取用户手机号请求，openid: {openid}')
        
        if not openid:
            response_data = {'code': 400, 'message': '参数错误'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 查询用户信息
        user = User.query.filter_by(openid=openid).first()
        if not user:
            app.logger.warning(f'获取用户手机号失败：用户不存在，openid: {openid}')
            response_data = {'code': 404, 'message': '用户不存在'}
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        
        # 解密手机号并脱敏
        phone_number = crypto_util.decrypt(user.phone_number)
        desensitized_phone = phone_number[:3] + '****' + phone_number[-4:]
        
        app.logger.info(f'获取用户手机号成功，openid: {openid}, 脱敏手机号: {desensitized_phone}')
        
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
