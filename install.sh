#!/bin/bash

# BesLove 后端完整安装脚本
# 该脚本会检查并停止已有的进程，然后执行完整的部署流程

echo "=== BesLove 后端安装脚本 ==="
echo "开始安装时间: $(date)"
echo ""

# 定义变量
PROJECT_DIR="/opt/beslove"
VENV_DIR="$PROJECT_DIR/venv"
GUNICORN_CONFIG="$PROJECT_DIR/gunicorn_config.py"
SERVICE_FILE="/etc/systemd/system/beslove.service"
LOG_DIR="/var/log/beslove"

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请以root用户运行此脚本"
    exit 1
fi

# 步骤1: 检查并停止已有的进程
echo "1. 检查并停止已有的进程..."

# 检查gunicorn进程
GUNICORN_PIDS=$(pgrep -f "gunicorn.*beslove" 2>/dev/null)
if [ -n "$GUNICORN_PIDS" ]; then
    echo "发现运行中的gunicorn进程: $GUNICORN_PIDS"
    echo "正在停止这些进程..."
    kill -TERM $GUNICORN_PIDS 2>/dev/null
    # 等待进程终止
    sleep 2
    # 强制终止仍在运行的进程
    GUNICORN_PIDS=$(pgrep -f "gunicorn.*beslove" 2>/dev/null)
    if [ -n "$GUNICORN_PIDS" ]; then
        echo "强制终止仍在运行的进程..."
        kill -KILL $GUNICORN_PIDS 2>/dev/null
    fi
    echo "gunicorn进程已停止"
else
    echo "未发现运行中的gunicorn进程"
fi

# 检查Systemd服务
if systemctl is-active --quiet beslove; then
    echo "发现运行中的beslove服务"
    echo "正在停止服务..."
    systemctl stop beslove 2>/dev/null
    echo "beslove服务已停止"
else
    echo "beslove服务未运行"
fi

# 检查80端口（Nginx）
NGINX_PIDS=$(pgrep -f "nginx" 2>/dev/null)
if [ -n "$NGINX_PIDS" ]; then
    echo "发现运行中的Nginx进程: $NGINX_PIDS"
    echo "正在停止Nginx..."
    systemctl stop nginx 2>/dev/null
    echo "Nginx已停止"
else
    echo "未发现运行中的Nginx进程"
fi

echo ""

# 步骤2: 更新系统
echo "2. 更新系统..."
dnf update -y
dnf upgrade -y
echo ""

# 步骤3: 安装必要的软件
echo "3. 安装必要的软件..."
# 安装 Python 3.8
dnf install python38 python38-devel python38-pip -y

# 安装 Git
dnf install git -y

# 安装 Nginx
dnf install nginx -y

# 安装其他依赖
dnf install gcc gcc-c++ make -y

echo ""

# 步骤4: 克隆项目代码
echo "4. 克隆项目代码..."
# 创建项目目录
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 克隆项目代码（这里需要用户手动替换为实际的仓库URL）
# 如果已经存在.git目录，则执行git pull
if [ -d ".git" ]; then
    echo "项目目录已存在，执行git pull更新代码..."
    git pull
else
    echo "请输入项目Git仓库URL:"
    read REPO_URL
    git clone $REPO_URL .
fi

echo ""

# 步骤5: 创建虚拟环境
echo "5. 创建虚拟环境..."
# 如果虚拟环境已存在，先删除
if [ -d "$VENV_DIR" ]; then
    echo "虚拟环境已存在，删除后重新创建..."
    rm -rf $VENV_DIR
fi

python3.8 -m venv venv
echo ""

# 步骤6: 安装项目依赖
echo "6. 安装项目依赖..."
# 激活虚拟环境
source $VENV_DIR/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装 Gunicorn
pip install gunicorn
echo ""

# 步骤7: 配置 Gunicorn
echo "7. 配置 Gunicorn..."

# 创建 Gunicorn 配置文件
cat > $GUNICORN_CONFIG << 'EOF'
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 30
accesslog = "/var/log/beslove/access.log"
errorlog = "/var/log/beslove/error.log"
loglevel = "info"
EOF

# 创建日志目录
mkdir -p $LOG_DIR
chmod 755 $LOG_DIR
echo ""

# 步骤8: 配置 Systemd 服务
echo "8. 配置 Systemd 服务..."

# 创建 Systemd 服务文件
cat > $SERVICE_FILE << 'EOF'
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

# 重新加载 Systemd
systemctl daemon-reload
echo ""

# 步骤9: 配置 Nginx
echo "9. 配置 Nginx..."

# 创建 Nginx 配置文件
cat > /etc/nginx/conf.d/beslove.conf << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 请替换为您的域名

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
EOF

# 测试 Nginx 配置
nginx -t
echo ""

# 步骤10: 配置防火墙
echo "10. 配置防火墙..."

# 开放 80 端口
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp  # HTTPS端口
firewall-cmd --reload
echo ""

# 步骤11: 启动服务
echo "11. 启动服务..."

# 启动应用服务
systemctl start beslove
systemctl enable beslove

# 启动 Nginx
systemctl start nginx
systemctl enable nginx

echo ""

# 步骤12: 检查服务状态
echo "12. 检查服务状态..."

# 检查应用服务状态
systemctl status beslove -l | head -n 20

echo ""

# 检查 Nginx 状态
systemctl status nginx -l | head -n 20

echo ""

# 检查端口
echo "13. 检查端口状态..."
netstat -tlnp | grep -E "(5000|80|443)"

echo ""

echo "=== 安装完成 ==="
echo "完成时间: $(date)"
echo ""
echo "下一步操作:"
echo "1. 请编辑 /opt/beslove/.env 文件，配置必要的环境变量"
echo "2. 初始化数据库: cd /opt/beslove && source venv/bin/activate && python init_db.py"
echo "3. 配置域名: 编辑 /etc/nginx/conf.d/beslove.conf 中的 server_name"
echo "4. 配置HTTPS: 运行 certbot --nginx -d your-domain.com"
echo ""
echo "详细日志可查看:"
echo "- 应用日志: $LOG_DIR/error.log 和 $LOG_DIR/access.log"
echo "- Nginx日志: /var/log/nginx/error.log 和 /var/log/nginx/access.log"
