from app.app import app, db
from app.models import User

def add_nickname_field():
    with app.app_context():
        # 检查users表是否已经有nick_name字段
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(users);")).fetchall()
            columns = [row[1] for row in result]
            
            if 'nick_name' not in columns:
                # 添加nick_name字段，允许为空
                conn.execute(db.text("ALTER TABLE users ADD COLUMN nick_name TEXT;"))
                print("已成功添加nick_name字段到users表")
            else:
                print("users表已经包含nick_name字段")

if __name__ == "__main__":
    add_nickname_field()
