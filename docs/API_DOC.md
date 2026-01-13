# BesLove后端 API 文档

## 1. 项目概述

BesLove是一个祝福短信发送平台，用户可以通过微信登录，向指定手机号发送匿名祝福短信。

## 2. API 基本信息

- **基础URL**: `https://www.beslove.cn/api`
- **请求格式**: JSON
- **响应格式**: JSON
- **认证方式**: 微信授权认证
- **错误处理**: 统一使用`code`和`message`字段返回错误信息

## 3. API 端点列表

### 3.1 测试接口

**接口路径**: `/api/test`
**请求方法**: GET
**功能描述**: 测试接口，返回Hello World

#### 请求参数

无

#### 请求示例

```
curl -X GET https://www.beslove.cn/api/test
```

#### 响应示例

```json
{
  "message": "Hello, World!"
}
```

### 3.2 获取微信用户openid接口

**接口路径**: `/api/wx/get_openid`
**请求方法**: GET
**功能描述**: 通过微信登录临时凭证获取用户openid和session_key

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| code | string | 是 | 微信登录临时凭证 |

#### 请求示例

```
curl -X GET https://www.beslove.cn/api/wx/get_openid?code=01123456
```

#### 响应示例

**成功响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "openid": "o1234567890",
    "session_key": "abc123xyz"
  }
}
```

**失败响应**:
```json
{
  "code": 400,
  "message": "获取openid失败",
  "wx_error": {
    "errcode": 40029,
    "errmsg": "invalid code"
  }
}
```

### 3.3 微信登录接口

**接口路径**: `/api/wx/login`
**请求方法**: POST
**功能描述**: 用户通过微信授权登录，获取openid和相关用户信息

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| code | string | 是 | 微信登录临时凭证 |
| encryptedData | string | 是 | 加密的用户数据 |
| iv | string | 是 | 加密算法的初始向量 |

#### 请求示例

```json
{
  "code": "01123456",
  "encryptedData": "ABC123...",
  "iv": "XYZ789..."
}
```

#### 响应示例

**成功响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "openid": "o1234567890",
    "phone": "138****8000"
  }
}
```

**失败响应**:
```json
{
  "code": 400,
  "message": "手机号解密失败",
  "error": "解密错误信息"
}
```

### 3.4 获取祝福模板接口

**接口路径**: `/api/blessing/templates`
**请求方法**: GET
**功能描述**: 获取系统预设的祝福模板列表

#### 请求参数

无

#### 请求示例

```
curl -X GET https://www.beslove.cn/api/blessing/templates
```

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
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
}
```

### 3.5 发送祝福接口

**接口路径**: `/api/blessing/send`
**请求方法**: POST
**功能描述**: 向指定手机号发送祝福短信

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| sender_openid | string | 是 | 发送者的openid |
| receiver_phone | string | 是 | 接收者手机号 |
| content | string | 是 | 祝福内容 |

#### 请求示例

```json
{
  "sender_openid": "o1234567890",
  "receiver_phone": "13800138000",
  "content": "今天特别想你"
}
```

#### 响应示例

**成功响应**:
```json
{
  "code": 200,
  "message": "发送成功",
  "data": {
    "sender_openid": "o1234567890",
    "receiver_phone": "13800138000",
    "content": "今天特别想你"
  }
}
```

**失败响应**:
```json
{
  "code": 400,
  "message": "参数错误"
}
```

### 3.6 获取用户手机号接口

**接口路径**: `/api/user/phone`
**请求方法**: GET
**功能描述**: 获取当前用户的手机号（脱敏处理）

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| openid | string | 是 | 用户唯一标识 |

#### 请求示例

```
curl -X GET https://www.beslove.cn/api/user/phone?openid=o1234567890
```

#### 响应示例

**成功响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "phone": "138****8000"
  }
}
```

**失败响应**:
```json
{
  "code": 404,
  "message": "用户不存在"
}
```

## 4. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 参数错误 |
| 404 | 用户不存在 |
| 500 | 服务器内部错误 |

## 5. 数据模型

### 5.1 用户模型 (User)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| openid | string | 用户唯一标识，微信openid |
| phone_number | string | 加密存储的手机号 |
| created_at | datetime | 用户创建时间 |

### 5.2 祝福消息模型 (BlessingMessage)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | integer | 消息ID，自增主键 |
| sender_openid | string | 发送者openid |
| receiver_phone | string | 加密存储的接收者手机号 |
| content | string | 祝福内容 |
| sent_at | datetime | 发送时间 |
| status | string | 发送状态：pending(待发送)、sent(已发送)、failed(发送失败) |

## 6. 注意事项

1. 所有API请求和响应都使用JSON格式
2. 用户必须先通过微信登录获取openid才能发送祝福
3. 祝福内容会经过敏感词过滤
4. 系统有发送频率限制，防止恶意发送
5. 不能给自己发送祝福
6. 手机号格式必须正确

## 7. 安全说明

1. 所有敏感信息（如手机号）都经过加密存储
2. API请求不直接暴露完整手机号（仅显示部分）
3. 微信登录使用安全的加密算法解密用户数据
4. 系统日志不记录敏感信息

## 8. 部署说明

请参考项目根目录下的`deploy_aliyun.md`文件进行部署。

## 9. 日志管理

### 9.1 Flask应用日志

Flask应用日志记录了应用程序的运行情况、错误信息和用户请求等内容。

**日志文件位置：**
```
/opt/beslove/app/logs/beslove.log
```

**查看日志方法：**
```bash
# 查看最新日志
cat /opt/beslove/app/logs/beslove.log

# 实时监控日志
tail -f /opt/beslove/app/logs/beslove.log

# 查看日志的最后100行
tail -n 100 /opt/beslove/app/logs/beslove.log
```

**日志级别：**
- DEBUG：详细调试信息
- INFO：一般信息
- WARNING：警告信息
- ERROR：错误信息
- CRITICAL：严重错误信息

### 9.2 Systemd服务日志

Systemd服务日志记录了应用程序的启动、停止和运行状态。

**查看方法：**
```bash
# 查看beslove服务的日志
journalctl -u beslove.service

# 实时监控服务日志
journalctl -u beslove.service -f

# 查看最近的50条日志
journalctl -u beslove.service -n 50

# 查看特定时间范围内的日志
journalctl -u beslove.service --since "2024-01-01" --until "2024-01-02"
```

### 9.3 Nginx日志

Nginx日志记录了HTTP请求、响应和错误信息。

**日志文件位置：**
```
# 访问日志
/usr/local/nginx/logs/access.log

# 错误日志
/usr/local/nginx/logs/error.log
```

**查看方法：**
```bash
# 查看Nginx访问日志
tail -f /usr/local/nginx/logs/access.log

# 查看Nginx错误日志
tail -f /usr/local/nginx/logs/error.log
```

### 9.4 日志分析

通过分析日志，您可以：
1. 了解应用程序的运行状态和性能
2. 定位和解决错误问题
3. 监控用户请求和行为
4. 识别潜在的安全问题

建议定期查看和分析日志，确保应用程序的正常运行。