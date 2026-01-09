#!/bin/bash

# BesLove服务启动失败分析脚本
echo "=== BesLove服务启动失败分析 ==="

# 1. 检查gunicorn配置文件
echo "\n1. 检查gunicorn配置文件："
if [ -f "/opt/beslove/gunicorn_config.py" ]; then
    cat /opt/beslove/gunicorn_config.py
else
    echo "gunicorn_config.py 文件不存在！"
fi

# 2. 检查应用程序目录结构
echo "\n2. 检查应用程序目录结构："
ls -la /opt/beslove/

# 3. 检查主应用文件
echo "\n3. 检查主应用文件："
if [ -f "/opt/beslove/app.py" ]; then
    head -n 20 /opt/beslove/app.py
else
    echo "app.py 文件不存在！"
fi

# 4. 直接运行gunicorn命令查看详细错误
echo "\n4. 直接运行gunicorn命令查看详细错误："
/opt/beslove/venv/bin/gunicorn -c /opt/beslove/gunicorn_config.py app:app

# 5. 检查Python依赖
echo "\n5. 检查Python依赖："
/opt/beslove/venv/bin/pip list

# 6. 检查应用程序日志文件
echo "\n6. 检查应用程序日志文件："
find /opt/beslove -name "*.log" -type f 2>/dev/null
if [ $? -eq 0 ]; then
    find /opt/beslove -name "*.log" -type f 2>/dev/null | xargs cat 2>/dev/null
else
    echo "未找到日志文件"
fi
