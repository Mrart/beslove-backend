#!/bin/bash

# BesLove 后端更新脚本
# 该脚本会检查并停止已有的进程，然后执行更新流程
echo "=== BesLove 后端更新脚本 ==="
echo "开始更新时间: $(date)"
echo ""

# 定义变量
PROJECT_DIR="/opt/beslove"
VENV_DIR="$PROJECT_DIR/venv"

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

echo ""

# 步骤2: 更新项目代码
echo "2. 更新项目代码..."
cd $PROJECT_DIR

# 拉取最新代码
git pull

if [ $? -ne 0 ]; then
    echo "错误: git pull 失败，请检查网络连接和仓库权限"
    exit 1
fi

echo ""

# 步骤3: 更新依赖
echo "3. 更新项目依赖..."

# 激活虚拟环境
source $VENV_DIR/bin/activate

# 升级 pip
$VENV_DIR/bin/pip install --upgrade pip

# 更新项目依赖
$VENV_DIR/bin/pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败，请检查requirements.txt文件"
    exit 1
fi

# 确保Gunicorn已安装
    $VENV_DIR/bin/pip install gunicorn

    # 退出虚拟环境
    deactivate

    echo ""

    # 步骤4: 检查并初始化数据库（如果需要）
    echo "4. 检查并初始化数据库..."

    if [ -f "$PROJECT_DIR/app/init_db.py" ]; then
        echo "发现数据库初始化脚本，执行初始化..."
        source $VENV_DIR/bin/activate
        python -m app.init_db
        deactivate
    else
        echo "未找到数据库初始化脚本，跳过此步骤"
    fi

echo ""

# 步骤5: 检查配置文件
echo "5. 检查配置文件..."

# 检查并创建日志目录
mkdir -p $PROJECT_DIR/app/logs
chmod -R 755 $PROJECT_DIR/app/logs

# 检查.env文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "警告: .env文件不存在，可能需要手动创建"
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo "发现.env.example文件，建议复制为.env并配置"
        cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
    fi
fi

echo ""

# 步骤6: 更新Nginx配置和SSL证书
echo "6. 更新Nginx配置和SSL证书..."

# 定义Nginx配置路径
NGINX_MAIN_CONF="/usr/local/nginx/conf/nginx.conf"

# 检查Nginx是否已安装
if command -v nginx &> /dev/null; then
    echo "Nginx已安装，配置路径: $NGINX_MAIN_CONF"
    
    # 备份当前的主配置文件
    cp $NGINX_MAIN_CONF "$NGINX_MAIN_CONF.$(date +%Y%m%d%H%M%S).bak"
    echo "已备份当前Nginx主配置文件到: $NGINX_MAIN_CONF.$(date +%Y%m%d%H%M%S).bak"
    
    # 使用acme.sh管理SSL证书（已替换certbot）
    echo "使用acme.sh管理SSL证书..."
    
    # 检查acme.sh是否已安装
    if [ ! -f "/root/.acme.sh/acme.sh" ]; then
        echo "安装acme.sh..."
        wget -O acme.sh https://raw.githubusercontent.com/acmesh-official/acme.sh/master/acme.sh
        chmod +x acme.sh
        ./acme.sh --install --email admin@beslove.cn
        rm -f acme.sh
    fi
    
    # 检查SSL证书是否存在
    if [ ! -f "/root/.acme.sh/www.beslove.cn_ecc/fullchain.cer" ]; then
        echo "获取SSL证书..."
        # 停止Nginx以允许acme.sh验证
        kill -TERM $(pgrep -f "nginx") 2>/dev/null
        sleep 2
        
        # 使用acme.sh获取证书
        /root/.acme.sh/acme.sh --issue -d www.beslove.cn --standalone
        
        if [ $? -ne 0 ]; then
            echo "警告: SSL证书获取失败，请手动检查"
        else
            echo "SSL证书获取成功"
        fi
    else
        echo "SSL证书已存在，检查是否需要续期..."
        /root/.acme.sh/acme.sh --renew -d www.beslove.cn --force
        if [ $? -eq 0 ]; then
            echo "SSL证书已更新或无需续期"
        else
            echo "警告: SSL证书续期失败，请手动检查"
        fi
    fi
    
    # 创建一个完整的Nginx配置模板
    cat > /tmp/nginx_template.conf << 'EOF'
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
#error_log  logs/error.log  info;

#pid        logs/nginx.pid;


events {
    multi_accept on;
    use epoll;
    worker_connections 1024;
}


http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=beslove_cache:10m max_size=100m inactive=60m use_temp_path=off;
    reset_timedout_connection on;
    keepalive_requests 100;
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # Default server block
    server {
        listen       80;
        server_name  localhost;

        location / {
            root   html;
            index  index.html index.htm;
        }

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }

    # BesLove backend server block (HTTP to HTTPS redirect)
    server {
        listen 80;
        server_name www.beslove.cn;
        location ~ /.well-known {
            root /opt/beslove/app/static;
            allow all;
        }

        # Redirect HTTP to HTTPS
        return 301 https://$host$request_uri;
    }

    # BesLove backend server block (HTTPS)
    server {
        listen 443 ssl http2;
        server_name www.beslove.cn;

        # SSL certificate configuration
        ssl_certificate /root/.acme.sh/www.beslove.cn_ecc/fullchain.cer;
        ssl_certificate_key /root/.acme.sh/www.beslove.cn_ecc/www.beslove.cn.key;
        ssl_session_cache shared:SSL:1m;
        ssl_session_timeout 5m;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        location ~ /.well-known {
            root /opt/beslove/app/static;
            allow all;
        }

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    
    # 使用完整模板替换配置文件
    mv /tmp/nginx_template.conf $NGINX_MAIN_CONF
    
    echo "已更新Nginx主配置文件"
    
    # 启动Nginx（如果之前停止了）
    if ! pgrep -f "nginx" > /dev/null; then
        echo "启动Nginx服务..."
        /usr/local/nginx/sbin/nginx
    fi
    
    # 测试Nginx配置
    echo "测试Nginx配置..."
    /usr/local/nginx/sbin/nginx -t
    
    if [ $? -eq 0 ]; then
        echo "Nginx配置有效，重启服务..."
        kill -HUP $(pgrep -f "nginx") 2>/dev/null
        echo "Nginx服务已重新加载"
    else
        echo "警告: Nginx配置无效，请手动检查"
    fi
else
    echo "Nginx未安装，跳过配置步骤"
fi

echo ""

# 步骤7: 启动服务
echo "7. 启动服务..."

# 更新systemd服务配置文件
echo "更新systemd服务配置文件..."
cat > /etc/systemd/system/beslove.service << 'EOF'
[Unit]
Description=BesLove Flask Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/beslove
Environment="PATH=/opt/beslove/venv/bin"
ExecStart=/opt/beslove/venv/bin/gunicorn -c /opt/beslove/app/gunicorn_config.py app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd配置
systemctl daemon-reload

# 启动应用服务
systemctl start beslove

if [ $? -ne 0 ]; then
    echo "错误: 应用服务启动失败，请检查日志: journalctl -u beslove.service -n 50"
    exit 1
fi

echo ""

# 步骤8: 检查服务状态
echo "8. 检查服务状态..."

# 检查应用服务状态
echo "应用服务状态:"
systemctl status beslove -l | head -n 20

echo ""

# 检查端口
echo "端口状态:"
netstat -tlnp | grep 5000

echo ""

# 检查Nginx状态（如果正在使用）
if pgrep -f "nginx" > /dev/null; then
    echo "Nginx状态:"
    ps aux | grep nginx | head -n 10
fi

echo ""

echo "=== 更新完成 ==="
echo "完成时间: $(date)"
echo ""
echo "更新内容:"
echo "1. 代码已更新到最新版本"
echo "2. 项目依赖已更新"
echo "3. Nginx配置和SSL证书已更新"
echo "4. 应用服务已启动"