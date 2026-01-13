# 日志查看指南

## 1. 日志概述

BesLove应用的日志系统由多个组件组成，包括应用程序日志、Gunicorn服务器日志、Nginx访问日志和系统服务日志。这些日志分布在不同的位置，记录了应用运行的各个方面信息。

## 2. 应用程序日志

### 2.1 日志位置

应用程序日志存储在以下位置：

```
/opt/beslove/app/logs/beslove.log
```

### 2.2 日志格式

日志采用以下格式记录：

```
2024-01-13 16:00:00,000 - app - INFO - app.py:42 - 应用启动成功
```

格式说明：
- `2024-01-13 16:00:00,000`: 日志时间戳
- `app`: 日志器名称
- `INFO`: 日志级别
- `app.py:42`: 日志来源文件和行号
- `应用启动成功`: 日志消息内容

### 2.3 日志级别

应用使用以下日志级别（从低到高）：
- `DEBUG`: 调试信息，用于开发和问题诊断
- `INFO`: 一般信息，记录正常的应用操作
- `WARNING`: 警告信息，记录潜在的问题
- `ERROR`: 错误信息，记录应用错误
- `CRITICAL`: 严重错误信息，记录导致应用崩溃的严重问题

### 2.4 查看方法

查看最新日志：
```bash
cat /opt/beslove/app/logs/beslove.log
```

实时监控日志：
```bash
tail -f /opt/beslove/app/logs/beslove.log
```

查看最后N行日志：
```bash
tail -n 100 /opt/beslove/app/logs/beslove.log
```

搜索特定关键字：
```bash
grep "ERROR" /opt/beslove/app/logs/beslove.log
grep "微信登录" /opt/beslove/app/logs/beslove.log
grep -i "error" /opt/beslove/app/logs/beslove.log  # 忽略大小写
```

## 3. Gunicorn服务器日志

### 3.1 日志位置

Gunicorn服务器日志包括访问日志和错误日志：

- 访问日志：`/var/log/beslove/access.log`
- 错误日志：`/var/log/beslove/error.log`

### 3.2 查看方法

查看Gunicorn错误日志：
```bash
tail -f /var/log/beslove/error.log
```

查看Gunicorn访问日志：
```bash
tail -f /var/log/beslove/access.log
```

## 4. Nginx日志

### 4.1 日志位置

Nginx日志包括访问日志和错误日志：

- 访问日志：`/usr/local/nginx/logs/access.log`
- 错误日志：`/usr/local/nginx/logs/error.log`

### 4.2 查看方法

查看Nginx错误日志：
```bash
tail -f /usr/local/nginx/logs/error.log
```

查看Nginx访问日志：
```bash
tail -f /usr/local/nginx/logs/access.log
```

## 5. Systemd服务日志

应用通过Systemd服务管理，相关日志可以通过journalctl查看。

### 5.1 查看方法

查看应用服务日志：
```bash
journalctl -u beslove.service
```

实时监控服务日志：
```bash
journalctl -u beslove.service -f
```

查看最近的N条日志：
```bash
journalctl -u beslove.service -n 100
```

查看特定时间范围内的日志：
```bash
journalctl -u beslove.service --since "2024-01-13 16:00:00" --until "2024-01-13 17:00:00"
```

## 6. 日志分析工具

### 6.1 使用less查看大日志文件

对于较大的日志文件，可以使用less命令进行交互式查看：

```bash
less /opt/beslove/app/logs/beslove.log
```

在less中可以使用以下快捷键：
- `j`/`k`: 上下滚动
- `/`: 搜索
- `n`/`N`: 下一个/上一个搜索结果
- `q`: 退出

### 6.2 使用grep过滤日志

搜索所有错误日志：
```bash
grep -i "error" /opt/beslove/app/logs/beslove.log | less
```

搜索特定时间段的日志：
```bash
grep "2024-01-13 16:0[0-9]:" /opt/beslove/app/logs/beslove.log | less
```

### 6.3 使用awk分析日志

统计不同日志级别的数量：
```bash
awk '{print $4}' /opt/beslove/app/logs/beslove.log | sort | uniq -c
```

## 7. 日志轮转

应用日志配置了自动轮转机制，当日志文件达到10MB时会自动创建新文件，并保留最近5个日志文件。这样可以避免日志文件过大导致的问题。

## 8. 常见问题排查

### 8.1 应用无法启动

查看应用日志：
```bash
tail -n 100 /opt/beslove/app/logs/beslove.log
```

查看Systemd服务日志：
```bash
journalctl -u beslove.service -n 100
```

### 8.2 微信登录失败

查看微信登录相关日志：
```bash
grep -i "微信登录" /opt/beslove/app/logs/beslove.log
```

### 8.3 短信发送失败

查看短信发送相关日志：
```bash
grep -i "短信" /opt/beslove/app/logs/beslove.log
```

### 8.4 Nginx连接问题

查看Nginx错误日志：
```bash
tail -n 100 /usr/local/nginx/logs/error.log
```

查看Nginx访问日志：
```bash
tail -n 100 /usr/local/nginx/logs/access.log | grep "404\|500"
```

## 9. 日志配置修改

### 9.1 修改应用日志级别

编辑`/opt/beslove/app/app.py`文件，找到以下代码并修改日志级别：

```python
app.logger.setLevel(logging.INFO)
```

将`INFO`改为其他日志级别（如`DEBUG`、`WARNING`、`ERROR`等）。

### 9.2 修改Gunicorn日志级别

编辑`/opt/beslove/app/gunicorn_config.py`文件，找到以下代码并修改日志级别：

```python
loglevel = "info"
```

将`info`改为其他日志级别（如`debug`、`warning`、`error`等）。

### 9.3 重启服务使配置生效

修改配置后，需要重启应用服务：

```bash
systemctl restart beslove
```