#!/bin/bash

# Nginx安装失败解决方案（排除规则问题）
echo "=== Nginx安装失败解决方案 ==="

# 步骤1：检查仓库配置中的排除规则
echo "\n1. 检查仓库配置中的排除规则："
grep -r "exclude" /etc/yum.repos.d/

# 步骤2：使用官方Nginx仓库安装
echo "\n2. 使用官方Nginx仓库安装："

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

# 步骤3：测试Nginx配置和启动服务
echo "\n3. 测试Nginx配置："
nginx -t

echo "\n4. 启动Nginx服务："
systemctl start nginx
systemctl enable nginx

echo "\n5. 检查Nginx状态："
systemctl status nginx --no-pager

echo "\n=== 安装完成 ==="
