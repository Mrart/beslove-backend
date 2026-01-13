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
| code | string | 是 | 微信登录临时凭证code |

#### 请求示例

```
curl -X GET "https://www.beslove.cn/api/wx/get_openid?code=0010130000000000000000000000000"
```

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "openid": "oBzHC4tnDMxWcVmiFSbaXTEAWY-g",
    "session_key": "6BurxYZzztRmS2xzx4hjrg=="
  }
}
```

#### 错误响应示例

```json
{
  "code": 400,
  "message": "缺少code参数"
}
```

### 3.3 微信登录接口

**接口路径**: `/api/wx/login`
**请求方法**: POST
**功能描述**: 微信授权登录，获取用户手机号并创建/更新用户信息

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| code | string | 是 | 微信登录临时凭证code |
| encryptedData | string | 是 | 微信加密的用户数据 |
| iv | string | 是 | 加密算法的初始向量 |

#### 请求示例

```json
{
  "code": "0010130000000000000000000000000",
  "encryptedData": "xxxxxxxxx",
  "iv": "yyyyyyyyy"
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "openid": "oBzHC4tnDMxWcVmiFSbaXTEAWY-g",
    "phone": "138****1234"
  }
}
```

#### 错误响应示例

```json
{
  "code": 400,
  "message": "参数错误"
}
```

### 3.4 获取祝福模板接口

**接口路径**: `/api/blessing/templates`
**请求方法**: GET
**功能描述**: 获取祝福短信模板列表

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
      {
        "id": 1,
        "content": "愿你被这个世界温柔以待",
        "category": "温暖"
      },
      {
        "id": 2,
        "content": "愿你有一个灿烂的前程",
        "category": "祝福"
      }
    ]
  }
}
```

### 3.5 发送祝福短信接口

**接口路径**: `/api/blessing/send`
**请求方法**: POST
**功能描述**: 向指定手机号发送祝福短信

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| sender_openid | string | 是 | 发送者微信openid |
| receiver_phone | string | 是 | 接收者手机号 |
| content | string | 是 | 祝福内容，最长80个字符 |

#### 请求示例

```json
{
  "sender_openid": "oBzHC4tnDMxWcVmiFSbaXTEAWY-g",
  "receiver_phone": "13800138000",
  "content": "愿你被这个世界温柔以待"
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "祝福发送成功",
  "data": {
    "message_id": 1
  }
}
```

#### 错误响应示例

```json
{
  "code": 400,
  "message": "祝福内容超过80个字符"
}
```

### 3.6 获取用户手机号接口

**接口路径**: `/api/user/phone`
**请求方法**: GET
**功能描述**: 获取当前用户的手机号（脱敏处理）

#### 请求参数

| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| openid | string | 是 | 用户微信openid |

#### 请求示例

```
curl -X GET "https://www.beslove.cn/api/user/phone?openid=oBzHC4tnDMxWcVmiFSbaXTEAWY-g"
```

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "phone": "138****1234"
  }
}
```

#### 错误响应示例

```json
{
  "code": 400,
  "message": "用户不存在"
}
```

## 4. 错误码说明

| 错误码 | 错误描述 |
|--------|----------|
| 200 | 请求成功 |
| 400 | 请求参数错误或业务逻辑错误 |
| 401 | 未授权或授权失败 |
| 500 | 服务器内部错误 |

## 5. 数据模型

### 5.1 用户(User)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| openid | string | 用户微信openid，主键 |
| phone_number | string | 加密存储的用户手机号 |
| created_at | datetime | 用户创建时间 |

### 5.2 祝福短信(BlessingMessage)

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | integer | 短信ID，主键 |
| sender_openid | string | 发送者openid，外键 |
| receiver_phone | string | 加密存储的接收者手机号 |
| content | string | 祝福内容 |
| sent_at | datetime | 发送时间 |
| status | string | 发送状态(pending/sent/failed) |

## 6. 部署说明

请参考项目根目录下的`deploy_aliyun.md`文件进行部署。