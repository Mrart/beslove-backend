#!/bin/bash

# 生成SSL证书脚本
# 支持自签名证书和Let's Encrypt证书

set -e

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SSL证书生成脚本 ===${NC}"

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请以root权限运行此脚本${NC}"
    exit 1
fi

# 检查OpenSSL是否已安装
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        echo -e "${RED}错误: OpenSSL未安装${NC}"
        echo -e "${YELLOW}请安装OpenSSL:${NC}"
        echo -e "  CentOS/RHEL: yum install openssl -y"
        echo -e "  Ubuntu/Debian: apt-get install openssl -y"
        exit 1
    fi
}

# 检查Certbot是否已安装
check_certbot() {
    if ! command -v certbot &> /dev/null; then
        echo -e "${YELLOW}提示: Certbot未安装，需要先安装Certbot来获取Let's Encrypt证书${NC}"
        read -p "是否安装Certbot? (y/n): " INSTALL_CERTBOT
        if [ "$INSTALL_CERTBOT" = "y" ] || [ "$INSTALL_CERTBOT" = "Y" ]; then
            install_certbot
        else
            echo -e "${RED}错误: 无法获取Let's Encrypt证书，Certbot未安装${NC}"
            exit 1
        fi
    fi
}

# 安装Certbot
install_certbot() {
    echo -e "${BLUE}正在安装Certbot...${NC}"
    
    # 检测操作系统
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        yum install epel-release -y
        yum install certbot -y
    elif [ -f /etc/debian_version ]; then
        # Ubuntu/Debian
        apt-get update
        apt-get install certbot -y
    else
        echo -e "${RED}错误: 不支持的操作系统${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Certbot安装完成${NC}"
}

# 生成自签名证书
generate_self_signed() {
    echo -e "${BLUE}=== 生成自签名证书 ===${NC}"
    
    # 获取证书信息
    read -p "请输入域名 (例如: www.example.com): " DOMAIN
    read -p "请输入组织名称 (例如: Example Inc): " ORGANIZATION
    read -p "请输入组织单位 (例如: IT Department): " ORG_UNIT
    read -p "请输入城市 (例如: Beijing): " CITY
    read -p "请输入省份 (例如: Beijing): " PROVINCE
    read -p "请输入国家代码 (例如: CN): " COUNTRY
    
    # 证书保存目录
    DEFAULT_CERT_DIR="/etc/ssl/certs"
    DEFAULT_KEY_DIR="/etc/ssl/private"
    
    read -p "请输入证书保存目录 [默认: $DEFAULT_CERT_DIR]: " CERT_DIR
    CERT_DIR=${CERT_DIR:-$DEFAULT_CERT_DIR}
    
    read -p "请输入私钥保存目录 [默认: $DEFAULT_KEY_DIR]: " KEY_DIR
    KEY_DIR=${KEY_DIR:-$DEFAULT_KEY_DIR}
    
    # 创建目录（如果不存在）
    mkdir -p "$CERT_DIR"
    mkdir -p "$KEY_DIR"
    
    # 证书文件路径
    CERT_FILE="$CERT_DIR/${DOMAIN}.crt"
    KEY_FILE="$KEY_DIR/${DOMAIN}.key"
    CSR_FILE="/tmp/${DOMAIN}.csr"
    
    echo -e "${YELLOW}正在生成私钥...${NC}"
    openssl genrsa -out "$KEY_FILE" 2048
    chmod 600 "$KEY_FILE"
    
    echo -e "${YELLOW}正在生成证书签名请求(CSR)...${NC}"
    openssl req -new -key "$KEY_FILE" -out "$CSR_FILE" << EOF
$COUNTRY
$PROVINCE
$CITY
$ORGANIZATION
$ORG_UNIT
$DOMAIN



EOF
    
    echo -e "${YELLOW}正在生成自签名证书...${NC}"
    openssl x509 -req -days 365 -in "$CSR_FILE" -signkey "$KEY_FILE" -out "$CERT_FILE"
    
    # 清理临时文件
    rm -f "$CSR_FILE"
    
    echo -e "${GREEN}自签名证书生成完成！${NC}"
    echo -e "${YELLOW}证书信息:${NC}"
    echo -e "  证书文件: $CERT_FILE"
    echo -e "  私钥文件: $KEY_FILE"
    echo -e "  有效期: 365天"
    echo -e "  域名: $DOMAIN"
    echo -e "  组织: $ORGANIZATION"
    
    echo -e "${YELLOW}注意事项:${NC}"
    echo -e "  1. 自签名证书不受浏览器信任，仅用于测试和开发环境"
    echo -e "  2. 生产环境建议使用Let's Encrypt或其他受信任的证书颁发机构"
    echo -e "  3. 私钥文件权限已设置为600，请确保只有root用户可以访问"
}

# 获取Let's Encrypt证书
generate_lets_encrypt() {
    echo -e "${BLUE}=== 获取Let's Encrypt证书 ===${NC}"
    
    read -p "请输入域名 (例如: www.example.com): " DOMAIN
    read -p "请输入邮箱地址 (用于接收证书到期提醒): " EMAIL
    
    echo -e "${YELLOW}注意: 获取Let's Encrypt证书需要域名已解析到当前服务器，并且80端口可以访问${NC}"
    read -p "确认域名已正确解析且80端口可访问? (y/n): " CONFIRM
    
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${RED}错误: 请先确保域名解析正确且80端口可访问${NC}"
        exit 1
    fi
    
    # 检查80端口是否被占用
    if lsof -i :80 &> /dev/null; then
        echo -e "${YELLOW}警告: 80端口已被占用${NC}"
        read -p "是否暂时停止占用80端口的服务? (y/n): " STOP_SERVICE
        if [ "$STOP_SERVICE" = "y" ] || [ "$STOP_SERVICE" = "Y" ]; then
            # 尝试停止常见的占用80端口的服务
            if command -v systemctl &> /dev/null; then
                systemctl stop nginx 2>/dev/null || true
                systemctl stop httpd 2>/dev/null || true
                systemctl stop apache2 2>/dev/null || true
            else
                service nginx stop 2>/dev/null || true
                service httpd stop 2>/dev/null || true
                service apache2 stop 2>/dev/null || true
            fi
        else
            echo -e "${RED}错误: 无法获取Let's Encrypt证书，80端口被占用${NC}"
            exit 1
        fi
    fi
    
    echo -e "${YELLOW}正在获取Let's Encrypt证书...${NC}"
    
    # 使用webroot或standalone模式
    CERTBOT_MODE="--standalone"
    
    certbot certonly $CERTBOT_MODE --non-interactive --agree-tos --email "$EMAIL" -d "$DOMAIN"
    
    # 恢复服务
    if [ "$STOP_SERVICE" = "y" ] || [ "$STOP_SERVICE" = "Y" ]; then
        if command -v systemctl &> /dev/null; then
            systemctl start nginx 2>/dev/null || true
            systemctl start httpd 2>/dev/null || true
            systemctl start apache2 2>/dev/null || true
        else
            service nginx start 2>/dev/null || true
            service httpd start 2>/dev/null || true
            service apache2 start 2>/dev/null || true
        fi
    fi
    
    # 证书文件路径
    CERT_FILE="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
    KEY_FILE="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
    
    echo -e "${GREEN}Let's Encrypt证书获取完成！${NC}"
    echo -e "${YELLOW}证书信息:${NC}"
    echo -e "  证书文件: $CERT_FILE"
    echo -e "  私钥文件: $KEY_FILE"
    echo -e "  有效期: 90天"
    echo -e "  域名: $DOMAIN"
    echo -e "  邮箱: $EMAIL"
    
    echo -e "${YELLOW}注意事项:${NC}"
    echo -e "  1. Let's Encrypt证书有效期为90天，需要定期续期"
    echo -e "  2. 建议设置自动续期任务: crontab -e"
    echo -e "     添加一行: 0 0 1 * * certbot renew --quiet"
    echo -e "  3. 证书文件保存在/etc/letsencrypt/live/${DOMAIN}/目录下"
}

# 主程序
main() {
    # 检查OpenSSL
    check_openssl
    
    # 显示菜单
    echo -e "${YELLOW}请选择证书类型:${NC}"
    echo -e "1. 生成自签名证书 (用于测试和开发环境)"
    echo -e "2. 获取Let's Encrypt证书 (用于生产环境，免费且受信任)"
    read -p "请输入选项 (1-2): " OPTION
    
    case $OPTION in
        1)
            generate_self_signed
            ;;
        2)
            check_certbot
            generate_lets_encrypt
            ;;
        *)
            echo -e "${RED}错误: 无效的选项${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}\n=== SSL证书生成脚本执行完成 ===${NC}"
}

# 执行主程序
main
