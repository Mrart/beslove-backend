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
pip install --upgrade pip

# 更新项目依赖
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败，请检查requirements.txt文件"
    exit 1
fi

# 确保Gunicorn已安装
pip install gunicorn

# 退出虚拟环境
deactivate

echo ""

# 步骤4: 检查并初始化数据库（如果需要）
echo "4. 检查并初始化数据库..."

if [ -f "$PROJECT_DIR/init_db.py" ]; then
    echo "发现数据库初始化脚本，执行初始化..."
    source $VENV_DIR/bin/activate
    python init_db.py
    deactivate
else
    echo "未找到数据库初始化脚本，跳过此步骤"
fi

echo ""

# 步骤5: 检查配置文件
echo "5. 检查配置文件..."

# 检查.env文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "警告: .env文件不存在，可能需要手动创建"
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo "发现.env.example文件，建议复制为.env并配置"
        cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
    fi
fi

echo ""

# 步骤6: 启动服务
echo "6. 启动服务..."

# 启动应用服务
systemctl start beslove

if [ $? -ne 0 ]; then
    echo "错误: 应用服务启动失败，请检查日志: journalctl -u beslove.service -n 50"
    exit 1
fi

echo ""

# 步骤7: 检查服务状态
echo "7. 检查服务状态..."

# 检查应用服务状态
echo "应用服务状态:"
systemctl status beslove -l | head -n 20

echo ""

# 检查端口
echo "端口状态:"
netstat -tlnp | grep 5000

echo ""

# 检查Nginx状态（如果正在使用）
if systemctl is-active --quiet nginx; then
    echo "Nginx状态:"
    systemctl status nginx -l | head -n 10
fi

echo ""

echo "=== 更新完成 ==="
echo "完成时间: $(date)"
echo ""
echo "更新内容:"
echo "1. 代码已更新到最新版本"
echo "2. 项目依赖已更新"
echo "3. 应用服务已重启"
echo ""
echo "检查应用日志: tail -f /var/log/beslove/error.log"
echo "检查访问日志: tail -f /var/log/beslove/access.log"
