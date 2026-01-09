# Certbot安装问题解决方案

## 步骤1：检查仓库配置文件
ls -la /etc/yum.repos.d/

## 步骤2：修复CentOS 8仓库配置
# 备份当前仓库配置
mkdir -p /etc/yum.repos.d/backup
mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/backup/

# 下载新的CentOS 8仓库配置
curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-8.repo
curl -o /etc/yum.repos.d/epel.repo https://mirrors.aliyun.com/repo/epel-8.repo

## 步骤3：清理并更新仓库缓存
dnf clean all
dnf makecache

## 步骤4：安装Certbot（方法一：使用仓库）
dnf install epel-release -y
dnf config-manager --set-enabled powertools
dnf install certbot python3-certbot-nginx -y

## 如果方法一失败，尝试方法二：使用pip
# python3 -m pip install --upgrade pip
# python3 -m pip install certbot certbot-nginx
# ln -s /usr/local/bin/certbot /usr/bin/certbot
