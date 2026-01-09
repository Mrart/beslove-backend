#!/bin/bash

# 检查Nginx安装情况
echo "=== 检查Nginx安装情况 ==="
if command -v nginx &> /dev/null; then
    echo "Nginx已安装: $(which nginx)"
    echo "Nginx版本: $(nginx -v 2>&1)"
    echo "Nginx编译参数: $(nginx -V 2>&1)"
else
    echo "Nginx未安装"
fi

# 检查Nginx配置文件
echo "\n=== 检查Nginx配置文件 ==="
config_paths=("/www/server/nginx/conf/nginx.conf" "/etc/nginx/nginx.conf" "/usr/local/nginx/conf/nginx.conf")
for path in "${config_paths[@]}"; do
    if [ -f "$path" ]; then
        echo "找到配置文件: $path"
        echo "配置文件内容(前30行):"
        head -n 30 "$path"
        echo "\n配置文件中的include指令:"
        grep -i include "$path"
        echo ""  # 空行分隔
    fi
done

# 检查Nginx目录结构
echo "\n=== 检查Nginx目录结构 ==="
nginx_dirs=("/www/server/nginx" "/etc/nginx" "/usr/local/nginx")
for dir in "${nginx_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "目录存在: $dir"
        ls -la "$dir"
        echo ""  # 空行分隔
    fi
done

# 检查Nginx进程
echo "\n=== 检查Nginx进程 ==="
ps aux | grep nginx | grep -v grep

# 检查systemd服务
echo "\n=== 检查Nginx systemd服务 ==="
systemctl list-unit-files | grep nginx
systemctl status nginx 2>&1 | head -n 20
