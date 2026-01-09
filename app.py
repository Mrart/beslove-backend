from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'beslove.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 配置JSON响应支持中文
app.config['JSON_AS_ASCII'] = False

# 配置CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化数据库
db = SQLAlchemy(app)

# 导入路由
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
