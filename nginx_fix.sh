#!/bin/bash

# Nginx配置文件缺失解决方案
echo "=== Nginx配置文件缺失解决方案 ==="

# 步骤1：检查Nginx是否安装
echo "\n1. 检查Nginx是否安装："
rpm -q nginx
if [ $? -ne 0 ]; then
    echo "Nginx未安装，正在安装..."
    dnf install nginx -y
else
    echo "Nginx已安装"
fi

# 步骤2：检查Nginx配置文件是否存在
echo "\n2. 检查Nginx配置文件："
if [ ! -f "/etc/nginx/nginx.conf" ]; then
    echo "Nginx配置文件缺失，正在创建..."
    
    # 创建基本的Nginx配置文件
    cat > /etc/nginx/nginx.conf << EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    include /etc/nginx/conf.d/*.conf;
}
EOF
    
    echo "Nginx配置文件已创建"
else
    echo "Nginx配置文件已存在"
fi

# 步骤3：测试Nginx配置
echo "\n3. 测试Nginx配置："
nginx -t

# 步骤4：启动Nginx服务
echo "\n4. 启动Nginx服务："
systemctl start nginx
systemctl enable nginx

# 步骤5：检查Nginx状态
echo "\n5. 检查Nginx状态："
systemctl status nginx --no-pager

echo "\n=== 修复完成 ==="
