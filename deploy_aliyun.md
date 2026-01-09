# BesLove 后端阿里云部署指南

## 服务器环境信息

根据您提供的信息，服务器系统为：
- Linux 内核：4.18.0-193.28.1.el8_2.x86_64
- 系统版本：CentOS 8

以下是针对 CentOS 8 系统的详细部署步骤。

## 部署前准备

### 1. 登录服务器

使用 SSH 登录您的阿里云服务器：

```bash
ssh root@your-server-ip
```

### 2. 更新系统

首先更新系统到最新版本：

```bash
dnf update -y
dnf upgrade -y
```

### 3. 安装必要的软件

安装 Python 3.8+ 和其他必要依赖：

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

## 项目部署

### 1. 克隆项目代码

```bash
# 创建项目目录
mkdir -p /opt/beslove
cd /opt/beslove

# 克隆项目代码
git clone <your-repository-url> .
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3.8 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，填写必要的配置信息
vi .env
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

### 5. 初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
python -c "from app import app, db; with app.app_context(): db.create_all()"
```

## 配置生产环境

### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

### 2. 配置 Gunicorn

创建 Gunicorn 配置文件：

```bash
vi /opt/beslove/gunicorn_config.py
```

添加以下内容：

```python
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 30
accesslog = "/var/log/beslove/access.log"
errorlog = "/var/log/beslove/error.log"
loglevel = "info"
```

创建日志目录：

```bash
mkdir -p /var/log/beslove
chmod 755 /var/log/beslove
```

### 3. 配置 Systemd 服务

创建 Systemd 服务文件：

```bash
vi /etc/systemd/system/beslove.service
```

添加以下内容：

```ini
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
```

启动服务：

```bash
systemctl daemon-reload
systemctl start beslove
systemctl enable beslove
```

检查服务状态：

```bash
systemctl status beslove
```

### 4. 配置 Nginx

编辑 Nginx 配置文件：

```bash
vi /etc/nginx/conf.d/beslove.conf
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件配置（如果有的话）
    # location /static {
    #     alias /opt/beslove/static;
    #     expires 30d;
    # }
}
```

测试 Nginx 配置：

```bash
nginx -t
```

启动 Nginx：

```bash
systemctl start nginx
systemctl enable nginx
```

### 5. 配置防火墙

```bash
# 开放 80 端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp  # 如果使用 HTTPS
firewall-cmd --reload
```

## HTTPS 配置（可选但推荐）

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 Certbot
dnf install certbot python3-certbot-nginx -y

# 申请证书
certbot --nginx -d your-domain.com
```

按照提示完成证书申请，Certbot 会自动配置 Nginx。

## 测试应用

应用部署完成后，可以通过以下方式测试：

```bash
# 测试 API 接口
curl http://your-domain.com/api/blessing/templates
```

## 监控和维护

### 查看日志

```bash
# 查看应用日志
tail -f /var/log/beslove/error.log
tail -f /var/log/beslove/access.log

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 重启服务

```bash
# 重启应用服务
systemctl restart beslove

# 重启 Nginx
systemctl restart nginx
```

### 更新应用

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

## 常见问题排查

1. **数据库连接问题**：检查数据库路径和权限
2. **端口占用**：使用 `netstat -tlnp` 查看端口占用情况
3. **环境变量**：确保 .env 文件配置正确
4. **权限问题**：检查文件和目录的权限设置
5. **日志分析**：查看应用和 Nginx 日志以定位问题

## 安全建议

1. **定期更新系统和依赖**
2. **使用 HTTPS 加密通信**
3. **限制 SSH 登录**：使用密钥认证，禁用密码登录
4. **配置防火墙规则**：只开放必要的端口
5. **定期备份数据库**

```bash
# 备份数据库示例
cp /opt/beslove/beslove.db /backup/beslove_$(date +%Y%m%d_%H%M%S).db
```

## 联系方式

如果您在部署过程中遇到任何问题，请随时联系技术支持。

---

**部署完成后，您的 BesLove 后端应用将运行在：**
- 主域名：http://your-domain.com
- API 接口：http://your-domain.com/api/

祝您使用愉快！
