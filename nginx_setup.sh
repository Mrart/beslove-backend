#!/bin/bash

# Nginx综合配置脚本
# 支持手动安装的Nginx (/usr/local/nginx/) 和HTTPS配置
# 合并了原有的nginx_fix.sh, nginx_install_fix.sh和configure_nginx_service.sh的功能

echo "=== Nginx综合配置脚本 ==="
echo "开始时间: $(date)"
echo ""

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请以root用户运行此脚本"
    exit 1
fi

# 定义变量
MANUAL_NGINX_PATH="/usr/local/nginx"
SYSTEM_NGINX_PATH="/etc/nginx"
NGINX_CONF_PATH=""
NGINX_BIN_PATH=""
USE_HTTPS="n"
DOMAIN="www.beslove.cn"
BACKEND_PORT="5000"

# 检查Nginx安装情况
check_nginx_installation() {
    echo "=== 检查Nginx安装情况 ==="
    
    # 检查手动安装的Nginx
    if [ -d "$MANUAL_NGINX_PATH" ] && [ -f "$MANUAL_NGINX_PATH/sbin/nginx" ]; then
        NGINX_BIN_PATH="$MANUAL_NGINX_PATH/sbin/nginx"
        NGINX_CONF_PATH="$MANUAL_NGINX_PATH/conf/nginx.conf"
        echo "检测到手动安装的Nginx: $NGINX_BIN_PATH"
        echo "手动安装的Nginx配置文件: $NGINX_CONF_PATH"
        return 0
    fi
    
    # 检查系统安装的Nginx
    if command -v nginx &> /dev/null; then
        NGINX_BIN_PATH=$(which nginx)
        # 尝试获取系统Nginx的配置文件路径
        if $NGINX_BIN_PATH -t &> /dev/null; then
            NGINX_CONF_PATH=$($NGINX_BIN_PATH -t 2>&1 | grep -oP 'configuration file \K[^ ]+')
        else
            NGINX_CONF_PATH="$SYSTEM_NGINX_PATH/nginx.conf"
        fi
        echo "检测到系统安装的Nginx: $NGINX_BIN_PATH"
        echo "系统安装的Nginx配置文件: $NGINX_CONF_PATH"
        return 0
    fi
    
    echo "未检测到Nginx安装"
    return 1
}

# 安装Nginx（如果未安装）
install_nginx() {
    echo "\n=== 安装Nginx ==="
    
    # 检查仓库配置中的排除规则
    echo "检查仓库配置中的排除规则:"
    grep -r "exclude" /etc/yum.repos.d/ 2>/dev/null
    
    # 使用官方Nginx仓库安装
    echo "\n使用官方Nginx仓库安装:"
    
    # 创建官方Nginx仓库配置
    cat > /etc/yum.repos.d/nginx.repo << 'EOF'
[nginx-stable]
name=nginx stable repo
baseurl=http://nginx.org/packages/centos/$releasever/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://nginx.org/keys/nginx_signing.key
module_hotfixes=true

[nginx-mainline]
name=nginx mainline repo
baseurl=http://nginx.org/packages/mainline/centos/$releasever/$basearch/
gpgcheck=1
enabled=0
gpgkey=https://nginx.org/keys/nginx_signing.key
module_hotfixes=true
EOF
    
    # 安装Nginx
    dnf install nginx -y
    
    # 更新Nginx路径
    NGINX_BIN_PATH=$(which nginx)
    if $NGINX_BIN_PATH -t &> /dev/null; then
        NGINX_CONF_PATH=$($NGINX_BIN_PATH -t 2>&1 | grep -oP 'configuration file \K[^ ]+')
    else
        NGINX_CONF_PATH="$SYSTEM_NGINX_PATH/nginx.conf"
    fi
    
    echo "Nginx安装完成: $NGINX_BIN_PATH"
}

# 配置Nginx HTTPS
configure_https() {
    echo "\n=== 配置HTTPS ==="
    
    # 询问是否使用HTTPS
    echo "是否要配置HTTPS访问？(y/n)"
    read -r USE_HTTPS
    
    if [ "$USE_HTTPS" != "y" ] && [ "$USE_HTTPS" != "Y" ]; then
        echo "跳过HTTPS配置，将使用HTTP"
        return
    fi
    
    # 获取证书路径
    echo "请输入SSL证书文件路径（.pem/.crt）:"
    read -r SSL_CERT_PATH
    
    echo "请输入SSL私钥文件路径（.key）:"
    read -r SSL_KEY_PATH
    
    # 验证证书和私钥文件是否存在
    if [ ! -f "$SSL_CERT_PATH" ]; then
        echo "错误: 证书文件不存在: $SSL_CERT_PATH"
        exit 1
    fi
    
    if [ ! -f "$SSL_KEY_PATH" ]; then
        echo "错误: 私钥文件不存在: $SSL_KEY_PATH"
        exit 1
    fi
    
    # 保存证书路径到全局变量
    SSL_CERT="$SSL_CERT_PATH"
    SSL_KEY="$SSL_KEY_PATH"
    
    echo "HTTPS证书配置完成"
}

# 配置Nginx服务器块
configure_nginx_server() {
    echo "\n=== 配置Nginx服务器块 ==="
    
    # 获取Nginx配置目录
    NGINX_CONF_DIR=$(dirname "$NGINX_CONF_PATH")
    
    # 确定服务器块配置文件路径
    if [ -d "$NGINX_CONF_DIR/conf.d" ]; then
        SERVER_CONF_PATH="$NGINX_CONF_DIR/conf.d/beslove.conf"
    elif [ -d "$NGINX_CONF_DIR/sites-enabled" ]; then
        SERVER_CONF_PATH="$NGINX_CONF_DIR/sites-enabled/beslove.conf"
    else
        SERVER_CONF_PATH="$NGINX_CONF_DIR/beslove.conf"
        # 检查主配置是否包含该文件
        if ! grep -q "beslove.conf" "$NGINX_CONF_PATH"; then
            echo "在主配置文件中添加beslove.conf的include指令"
            echo "include $SERVER_CONF_PATH;" >> "$NGINX_CONF_PATH"
        fi
    fi
    
    echo "服务器块配置文件路径: $SERVER_CONF_PATH"
    
    # 创建HTTP服务器块配置
    HTTP_CONFIG="server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}"
    
    # 创建HTTPS服务器块配置
    HTTPS_CONFIG="server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;

    # SSL优化配置
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # 强密码套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}"
    
    # 创建或更新服务器块配置文件
    if [ "$USE_HTTPS" = "y" ] || [ "$USE_HTTPS" = "Y" ]; then
        # 使用HTTPS配置并添加HTTP到HTTPS的重定向
        cat > "$SERVER_CONF_PATH" << EOF
# HTTP配置 (重定向到HTTPS)
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://$DOMAIN$request_uri;
}

# HTTPS配置
$HTTPS_CONFIG
EOF
    else
        # 使用HTTP配置
        cat > "$SERVER_CONF_PATH" << EOF
$HTTP_CONFIG
EOF
    fi
    
    echo "已创建服务器块配置文件: $SERVER_CONF_PATH"
}

# 配置Nginx systemd服务（仅适用于系统安装的Nginx）
configure_nginx_service() {
    echo "\n=== 配置Nginx systemd服务 ==="
    
    # 仅当使用系统安装的Nginx时配置systemd服务
    if [ "$NGINX_BIN_PATH" != "$MANUAL_NGINX_PATH/sbin/nginx" ]; then
        NGINX_SERVICE_FILE="/etc/systemd/system/nginx.service"
        
        # 备份现有服务文件（如果存在）
        if [ -f "$NGINX_SERVICE_FILE" ]; then
            cp "$NGINX_SERVICE_FILE" "$NGINX_SERVICE_FILE.$(date +%Y%m%d%H%M%S).bak"
            echo "已备份现有Nginx服务文件到: $NGINX_SERVICE_FILE.$(date +%Y%m%d%H%M%S).bak"
        fi
        
        # 创建新的Nginx服务文件
        cat > "$NGINX_SERVICE_FILE" << 'EOF'
[Unit]
Description=The NGINX HTTP and reverse proxy server
After=syslog.target network.target remote-fs.target nss-lookup.target

[Service]
Type=forking
PIDFile=/run/nginx.pid
ExecStartPre=/usr/sbin/nginx -t -c /etc/nginx/nginx.conf
ExecStart=/usr/sbin/nginx -c /etc/nginx/nginx.conf
ExecReload=/usr/sbin/nginx -s reload -c /etc/nginx/nginx.conf
ExecStop=/bin/kill -s QUIT $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
        
        # 更新服务文件中的二进制文件路径
        if [ "$NGINX_BIN_PATH" != "/usr/sbin/nginx" ]; then
            sed -i "s|/usr/sbin/nginx|$NGINX_BIN_PATH|g" "$NGINX_SERVICE_FILE"
            echo "已更新Nginx二进制文件路径为: $NGINX_BIN_PATH"
        fi
        
        # 更新服务文件中的配置文件路径
        if [ "$NGINX_CONF_PATH" != "/etc/nginx/nginx.conf" ]; then
            sed -i "s|/etc/nginx/nginx.conf|$NGINX_CONF_PATH|g" "$NGINX_SERVICE_FILE"
            echo "已更新Nginx配置文件路径为: $NGINX_CONF_PATH"
        fi
        
        # 更新PID文件路径（如果是手动安装的Nginx）
        if [ -f "$MANUAL_NGINX_PATH/logs/nginx.pid" ]; then
            sed -i "s|/run/nginx.pid|$MANUAL_NGINX_PATH/logs/nginx.pid|g" "$NGINX_SERVICE_FILE"
            echo "已更新Nginx PID文件路径为: $MANUAL_NGINX_PATH/logs/nginx.pid"
        fi
        
        echo "已创建Nginx服务文件: $NGINX_SERVICE_FILE"
        
        # 赋予服务文件正确的权限
        chmod 644 "$NGINX_SERVICE_FILE"
        echo "已设置服务文件权限为644"
        
        # 重新加载systemd配置
        echo "重新加载systemd配置..."
        systemctl daemon-reload
        
        # 启用Nginx服务
        echo "启用Nginx服务开机自启动..."
        systemctl enable nginx
        
        echo "Nginx systemd服务配置完成"
    else
        echo "手动安装的Nginx不使用systemd服务，跳过此步骤"
    fi
}

# 测试Nginx配置
test_nginx_config() {
    echo "\n=== 测试Nginx配置 ==="
    
    if $NGINX_BIN_PATH -t -c "$NGINX_CONF_PATH"; then
        echo "Nginx配置有效！"
        return 0
    else
        echo "错误: Nginx配置无效，请检查配置文件"
        return 1
    fi
}

# 启动/重启Nginx
start_nginx() {
    echo "\n=== 启动/重启Nginx ==="
    
    # 检查是否使用systemd服务
    if systemctl is-active nginx &> /dev/null; then
        echo "使用systemd重启Nginx服务..."
        systemctl restart nginx
        
        # 检查服务状态
        echo "\n检查Nginx服务状态:"
        systemctl status nginx --no-pager | head -n 20
    else
        # 手动安装的Nginx，使用直接命令重启
        echo "使用直接命令重启Nginx..."
        # 先停止运行的Nginx进程
        if pgrep -f "nginx" &> /dev/null; then
            echo "停止运行中的Nginx进程..."
            $NGINX_BIN_PATH -s stop
            sleep 2
        fi
        
        # 启动Nginx
        echo "启动Nginx..."
        $NGINX_BIN_PATH -c "$NGINX_CONF_PATH"
        
        # 检查是否启动成功
        if pgrep -f "nginx" &> /dev/null; then
            echo "Nginx启动成功！"
            echo "Nginx进程:"
            pgrep -f "nginx" | xargs ps -fp
        else
            echo "错误: Nginx启动失败"
            return 1
        fi
    fi
    
    return 0
}

# 主流程执行

# 1. 检查Nginx安装情况
if ! check_nginx_installation; then
    # 2. 如果未安装，安装Nginx
    echo "\nNginx未安装，是否要安装？(y/n)"
    read -r INSTALL_NGINX
    if [ "$INSTALL_NGINX" = "y" ] || [ "$INSTALL_NGINX" = "Y" ]; then
        install_nginx
    else
        echo "Nginx未安装，无法继续配置"
        exit 1
    fi
fi

# 3. 配置HTTPS
configure_https

# 4. 配置Nginx服务器块
configure_nginx_server

# 5. 配置Nginx systemd服务
configure_nginx_service

# 6. 测试Nginx配置
if ! test_nginx_config; then
    echo "配置错误，无法继续"
    exit 1
fi

# 7. 启动/重启Nginx
if ! start_nginx; then
    echo "Nginx启动失败"
    exit 1
fi

echo ""
echo "=== Nginx综合配置脚本完成 ==="
echo "完成时间: $(date)"
echo ""
echo "服务器配置信息:"
echo "- 域名: $DOMAIN"
echo "- 后端服务端口: $BACKEND_PORT"
if [ "$USE_HTTPS" = "y" ] || [ "$USE_HTTPS" = "Y" ]; then
    echo "- 访问方式: HTTPS (https://$DOMAIN)"
else
    echo "- 访问方式: HTTP (http://$DOMAIN)"
fi
echo ""
echo "使用以下命令验证配置:"
echo "$NGINX_BIN_PATH -T | grep -A 20 'server_name $DOMAIN'"
echo ""
echo "使用以下命令检查Nginx状态:"
if [ "$NGINX_BIN_PATH" != "$MANUAL_NGINX_PATH/sbin/nginx" ]; then
    echo "systemctl status nginx"
else
    echo "$NGINX_BIN_PATH -t"
fi