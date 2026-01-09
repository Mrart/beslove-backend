#!/bin/bash

# Configure Nginx service to use custom configuration path
# This script creates a systemd service file that ensures Nginx uses
# configuration files from /etc/nginx/ directory

echo "=== Nginx Service Configuration Script ==="
echo "开始时间: $(date)"
echo ""

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请以root用户运行此脚本"
    exit 1
fi

# 检查Nginx是否已安装
if ! command -v nginx &> /dev/null; then
    echo "错误: Nginx未安装，请先安装Nginx"
    exit 1
fi

# 定义变量
NGINX_SERVICE_FILE="/etc/systemd/system/nginx.service"
NGINX_CONFIG_PATH="/etc/nginx/nginx.conf"
NGINX_BIN_PATH=$(which nginx)

echo "检测到Nginx二进制文件路径: $NGINX_BIN_PATH"
echo "目标配置文件路径: $NGINX_CONFIG_PATH"
echo ""

# 备份现有服务文件（如果存在）
if [ -f "$NGINX_SERVICE_FILE" ]; then
    cp "$NGINX_SERVICE_FILE" "$NGINX_SERVICE_FILE.$(date +%Y%m%d%H%M%S).bak"
    echo "已备份现有Nginx服务文件到: $NGINX_SERVICE_FILE.$(date +%Y%m%d%H%M%S).bak"
    echo ""
fi

# 创建新的Nginx服务文件
echo "创建新的Nginx服务文件..."
cat > "$NGINX_SERVICE_FILE" << 'EOF'
[Unit]
Description=The NGINX HTTP and reverse proxy server
After=syslog.target network.target remote-fs.target nss-lookup.target

[Service]
Type=forking
PIDFile=/run/nginx.pid
# 指定配置文件路径
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

echo "已创建Nginx服务文件: $NGINX_SERVICE_FILE"
echo ""

# 赋予服务文件正确的权限
chmod 644 "$NGINX_SERVICE_FILE"
echo "已设置服务文件权限为644"
echo ""

# 重新加载systemd配置
echo "重新加载systemd配置..."
systemctl daemon-reload

echo ""

# 启用Nginx服务（可选）
echo "是否要启用Nginx服务以便开机自启动？(y/n)"
read -r ENABLE_SERVICE
if [ "$ENABLE_SERVICE" = "y" ] || [ "$ENABLE_SERVICE" = "Y" ]; then
    systemctl enable nginx
    echo "已启用Nginx服务开机自启动"
fi

echo ""

# 测试Nginx配置
echo "测试Nginx配置..."
nginx -t -c "$NGINX_CONFIG_PATH"

if [ $? -eq 0 ]; then
    echo "Nginx配置有效，可以启动服务了！"
    echo ""
    echo "使用以下命令启动Nginx:"
    echo "  systemctl start nginx"
    echo ""
    echo "使用以下命令验证Nginx是否使用了正确的配置:"
    echo "  nginx -T | head -n 5"
    echo ""
else
    echo "错误: Nginx配置无效，请检查配置文件: $NGINX_CONFIG_PATH"
    exit 1
fi

echo ""
echo "=== Nginx服务配置完成 ==="
echo "完成时间: $(date)"
