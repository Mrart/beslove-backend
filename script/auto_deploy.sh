#!/bin/bash

# BesLove 自动部署脚本
# 该脚本会自动提交本地代码到Git仓库，然后SSH到服务器执行部署

echo "=== BesLove 自动部署脚本 ==="
echo "开始部署时间: $(date)"
echo ""

# 定义变量
REMOTE_SERVER="120.26.152.60"
REMOTE_DIR="/opt/beslove"
REMOTE_USER="root"
GIT_BRANCH="main"

# 本地操作：提交代码到Git仓库
echo "1. 本地操作：提交代码到Git仓库..."

# 检查当前目录是否为Git仓库
if [ ! -d ".git" ]; then
    echo "错误: 当前目录不是Git仓库"
    exit 1
fi

# 检查Git状态
echo "检查Git状态..."
git status

# 添加所有更改到暂存区
echo "添加所有更改到暂存区..."
git add .

# 检查是否有更改需要提交
if git diff --staged --exit-code > /dev/null 2>&1; then
    echo "没有更改需要提交"
else
    # 提交更改
    echo "输入提交信息:"
    read -r commit_message
    
    if [ -z "$commit_message" ]; then
        commit_message="自动提交: $(date +%Y-%m-%d%H:%M:%S)"
    fi
    
    echo "提交更改: $commit_message"
    git commit -m "$commit_message"
    
    # 推送到远程仓库
    echo "推送到远程仓库..."
    git push origin $GIT_BRANCH
    
    if [ $? -ne 0 ]; then
        echo "错误: Git推送失败，请检查网络连接和仓库权限"
        exit 1
    fi
fi

echo ""

# 远程操作：SSH到服务器并部署
echo "2. 远程操作：SSH到服务器并部署..."

# 检查SSH连接
echo "检查与服务器的SSH连接..."
if ! ssh -q $REMOTE_USER@$REMOTE_SERVER "exit"; then
    echo "错误: 无法连接到服务器 $REMOTE_SERVER"
    exit 1
fi

# SSH到服务器并执行部署命令
echo "SSH到服务器并执行部署命令..."
ssh $REMOTE_USER@$REMOTE_SERVER << EOF
    echo "连接到服务器: $REMOTE_SERVER"
    echo "进入项目目录: $REMOTE_DIR"
    cd $REMOTE_DIR
    
    echo "拉取最新代码..."
    git pull origin $GIT_BRANCH
    
    if [ $? -ne 0 ]; then
        echo "错误: Git拉取失败，请检查网络连接和仓库权限"
        exit 1
    fi
    
    echo "运行更新脚本..."
    bash $REMOTE_DIR/update.sh
    
    if [ $? -ne 0 ]; then
        echo "警告: 更新脚本执行失败，请查看服务器日志"
    else
        echo "更新脚本执行成功"
    fi
EOF

echo ""
echo "=== 自动部署完成 ==="
echo "完成时间: $(date)"
