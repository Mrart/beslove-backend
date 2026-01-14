from app.app import app, db
from app.models import User, BlessingMessage

def init_database():
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库初始化成功，所有表已创建")
        
        # 检查users表结构
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(users);")).fetchall()
            print("\nUsers表结构:")
            for row in result:
                print(f"列名: {row[1]}, 类型: {row[2]}, 是否可为空: {row[3]}, 默认值: {row[4]}")

if __name__ == "__main__":
    init_database()
