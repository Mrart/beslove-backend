#!/bin/bash

# 测试API的curl命令集合

echo "=== BesLove后端API测试命令 ==="
echo ""
echo "1. 获取祝福模板 (GET)"
echo "curl -X GET http://localhost:5000/api/blessing/templates"
echo ""
echo "2. 微信登录 (POST)"
echo "curl -X POST http://localhost:5000/api/wx/login \
  -H 'Content-Type: application/json' \
  -d '{"code":"test_code","encryptedData":"test_encrypted_data","iv":"test_iv"}'"
echo ""
echo "3. 发送祝福 (POST)"
echo "curl -X POST http://localhost:5000/api/blessing/send \
  -H 'Content-Type: application/json' \
  -d '{"sender_openid":"test_openid","receiver_phone":"13800138000","content":"今天特别想你"}'"
echo ""
echo "使用方法：
1. 启动服务后，复制对应的curl命令到终端执行
2. 如果服务在远程服务器上运行，将localhost替换为服务器IP或域名
3. 对于需要认证的接口，请先获取有效的参数"
