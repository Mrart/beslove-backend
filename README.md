# BesLove 小程序后端

轻量级情感短信传递工具后端服务，基于 Flask + SQLite 实现。

## 项目特点

- 使用 Flask 框架构建 RESTful API
- SQLite 数据库存储用户和祝福消息
- AES-256 加密存储手机号，确保隐私安全
- 集成阿里云短信服务发送祝福短信
- 完善的风控机制，防止短信滥用
- 敏感词过滤功能，确保内容安全

## 技术栈

- Python 3.8+
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- Flask-CORS 4.0.0
- pycryptodome 3.18.0
- requests 2.31.0
- python-dotenv 1.0.0

## 安装指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd beslove-backend
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 文件并修改为 `.env`，填写必要的配置信息：

```bash
cp .env.example .env
```

配置项说明：

- `SECRET_KEY`: Flask 应用密钥
- `WX_APP_ID`: 微信小程序 AppID
- `WX_APP_SECRET`: 微信小程序 AppSecret
- `ALIYUN_ACCESS_KEY_ID`: 阿里云 Access Key ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云 Access Key Secret
- `ALIYUN_SMS_TEMPLATE_CODE`: 阿里云短信模板代码
- `AES_KEY`: AES-256 加密密钥（32位）
- `AES_IV`: AES-256 加密向量（16位）

### 5. 启动服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

## 数据库结构

### User 表

| 字段名 | 类型 | 描述 |
|--------|------|------|
| openid | String(100) | 微信用户唯一标识，主键 |
| phone_number | String(200) | 加密后的用户手机号 |
| created_at | DateTime | 用户创建时间 |

### BlessingMessage 表

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 祝福消息ID，主键，自增 |
| sender_openid | String(100) | 发送者openid，外键 |
| receiver_phone | String(200) | 加密后的接收者手机号 |
| content | String(100) | 祝福内容 |
| sent_at | DateTime | 发送时间 |
| status | String(20) | 发送状态（pending/sent/failed） |

## API 接口文档

### 1. 微信授权登录

**接口地址**: `/api/wx/login`

**请求方法**: POST

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| code | String | 是 | 微信登录临时凭证 |
| encryptedData | String | 是 | 加密的用户数据 |
| iv | String | 是 | 加密算法的初始向量 |

**响应示例**:

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "openid": "o1FkQ5LxZ7Y8W9E0R1T2Y3U4I5O6P7",
    "phone": "138****0000"
  }
}
```

### 2. 获取祝福模板

**接口地址**: `/api/blessing/templates`

**请求方法**: GET

**响应示例**:

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

### 3. 发送祝福

**接口地址**: `/api/blessing/send`

**请求方法**: POST

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| sender_openid | String | 是 | 发送者openid |
| receiver_phone | String | 是 | 接收者手机号 |
| content | String | 是 | 祝福内容（最多80个字符） |

**响应示例**:

```json
{
  "code": 200,
  "message": "祝福发送成功",
  "data": {
    "receiver_phone": "138****1234",
    "message": "愿TA一眼认出是你"
  }
}
```

**错误响应示例**:

```json
{
  "code": 400,
  "message": "手机号格式不正确"
}
```

## 风控规则

1. **发送者限制**: 同一用户（openid）24小时最多发送3条祝福
2. **接收者限制**: 同一手机号24小时最多接收2条祝福
3. **内容限制**: 祝福内容最多80个字符，禁止包含敏感词
4. **自发送限制**: 禁止向自己的手机号发送祝福

## 部署说明

### 阿里云服务器部署

#### 服务器信息
- **系统版本**: CentOS 8
- **内核版本**: 4.18.0-193.28.1.el8_2.x86_64

#### 部署步骤

1. **登录服务器**:

```bash
ssh root@your-server-ip
```

2. **更新系统**:

```bash
dnf update -y
dnf upgrade -y
```

3. **安装必要软件**:

```bash
# 安装 Python 3.8
dnf install python38 python38-devel python38-pip -y

# 安装 Git
dnf install git -y

# 安装 Nginx
dnf install nginx -y

# 安装其他依赖
dnf install gcc gcc-c++ make -y
```

4. **克隆项目代码**:

```bash
# 创建项目目录
mkdir -p /opt/beslove
cd /opt/beslove

# 克隆项目代码
git clone <your-repository-url> .
```

5. **创建虚拟环境**:

```bash
# 创建虚拟环境
python3.8 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

6. **安装项目依赖**:

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

7. **配置环境变量**:

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，填写必要的配置信息
vi .env
```

8. **初始化数据库**:

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
python -c "from app import app, db; with app.app_context(): db.create_all()"
```

9. **安装并配置 Gunicorn**:

```bash
# 安装 Gunicorn
pip install gunicorn

# 创建 Gunicorn 配置文件
cat > /opt/beslove/gunicorn_config.py << EOF
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 30
accesslog = "/var/log/beslove/access.log"
errorlog = "/var/log/beslove/error.log"
loglevel = "info"
EOF

# 创建日志目录
mkdir -p /var/log/beslove
chmod 755 /var/log/beslove
```

10. **配置 Systemd 服务**:

```bash
# 创建 Systemd 服务文件
cat > /etc/systemd/system/beslove.service << EOF
[Unit]
Description=BesLove Flask Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/beslove
Environment="PATH=/opt/beslove/venv/bin"
ExecStart=/opt/beslove/venv/bin/gunicorn -c /opt/beslove/gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl start beslove
systemctl enable beslove

# 检查服务状态
systemctl status beslove
```

11. **配置 Nginx**:

```bash
# 创建 Nginx 配置文件
cat > /etc/nginx/conf.d/beslove.conf << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 测试 Nginx 配置
nginx -t

# 启动 Nginx
systemctl start nginx
systemctl enable nginx
```

12. **配置防火墙**:

```bash
# 开放 80 端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp  # 如果使用 HTTPS
firewall-cmd --reload
```

13. **配置 HTTPS**（推荐）:

```bash
# 安装 Certbot
dnf install certbot python3-certbot-nginx -y

# 申请证书
certbot --nginx -d your-domain.com
```

### 日常维护

#### 查看日志

```bash
# 查看应用日志
tail -f /var/log/beslove/error.log
tail -f /var/log/beslove/access.log

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

#### 重启服务

```bash
# 重启应用服务
systemctl restart beslove

# 重启 Nginx
systemctl restart nginx
```

#### 更新应用

```bash
cd /opt/beslove

git pull

# 更新依赖（如果有变化）
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
deactivate
systemctl restart beslove
```

## 注意事项

1. 请确保微信小程序已经获取了用户手机号的权限
2. 请确保阿里云短信服务已经开通，并且短信签名和模板已经审核通过
3. 生产环境中请使用更安全的密钥管理方式，不要将密钥直接存储在代码中
4. 定期备份数据库文件，防止数据丢失
5. 根据实际业务需求调整风控规则

## 未来扩展

- 支持语音祝福（转文字+语音链接短信）
- 实现定时发送功能
- 添加接收方扫码查看动态电子卡片
- 增加情感场景分类功能
- 优化敏感词过滤算法

## 许可证

MIT
