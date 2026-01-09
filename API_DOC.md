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

### 3.1 微信登录接口

**接口路径**: `/wx/login`
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

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "openid": "o1234567890",
    "phone": "13800138000"
  }
}
```

### 3.2 发送祝福接口

**接口路径**: `/blessing/send`
**请求方法**: POST
**功能描述**: 向指定手机号发送祝福短信

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| sender_openid | string | 是 | 发送者的openid |
| receiver_phone | string | 是 | 接收者手机号 |
| content | string | 是 | 祝福内容，最多80个字符 |

#### 请求示例

```json
{
  "sender_openid": "o1234567890",
  "receiver_phone": "13800138000",
  "content": "今天特别想你"
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "祝福发送成功",
  "data": {
    "receiver_phone": "138****8000",
    "message": "愿TA一眼认出是你"
  }
}
```

### 3.3 获取祝福模板接口

**接口路径**: `/blessing/templates`
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
  "data": {
    "templates": [
      "今天特别想你",
      "对不起，我错了",
      "生日快乐，我的光",
      "谢谢你一直在我身边"
    ]
  }
}
```

## 4. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 参数错误 |
| 401 | 用户未登录 |
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
| content | string | 祝福内容，最多80个字符 |
| sent_at | datetime | 发送时间 |
| status | string | 发送状态：pending(待发送)、sent(已发送)、failed(发送失败) |

## 6. 注意事项

1. 所有API请求和响应都使用JSON格式
2. 用户必须先通过微信登录获取openid才能发送祝福
3. 祝福内容有长度限制（最多80个字符）
4. 祝福内容会经过敏感词过滤
5. 系统有发送频率限制，防止恶意发送
6. 不能给自己发送祝福
7. 手机号格式必须正确

## 7. 安全说明

1. 所有敏感信息（如手机号）都经过加密存储
2. API请求不直接暴露完整手机号（仅显示部分）
3. 微信登录使用安全的加密算法解密用户数据
4. 系统日志不记录敏感信息

## 8. 部署说明

请参考项目根目录下的`deploy_aliyun.md`文件进行部署。
