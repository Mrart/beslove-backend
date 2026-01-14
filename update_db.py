from app.app import app, db
from app.models import BlessingMessage

def update_database():
    with app.app_context():
        # 检查blessing_messages表是否已经有is_deleted字段
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(blessing_messages);")).fetchall()
            columns = [row[1] for row in result]
            
            if 'is_deleted' not in columns:
                # 添加is_deleted字段，默认值为False
                conn.execute(db.text("ALTER TABLE blessing_messages ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0;"))
                print("已成功添加is_deleted字段到blessing_messages表")
            else:
                print("blessing_messages表已经包含is_deleted字段")

if __name__ == "__main__":
    update_database()
