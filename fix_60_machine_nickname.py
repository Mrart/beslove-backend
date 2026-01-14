#!/usr/bin/env python3
"""
修复60机器上users表缺少nick_name字段的问题
"""

from app.app import app, db
from app.models import User
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_nickname_column():
    try:
        with app.app_context():
            logger.info("开始修复60机器上的nick_name字段问题")
            
            # 检查数据库连接
            if not db.engine:
                logger.error("无法连接到数据库")
                return False
            
            # 检查users表是否存在
            with db.engine.connect() as conn:
                # 检查表是否存在
                table_exists = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")).fetchone()
                if not table_exists:
                    logger.error("users表不存在，无法修复")
                    return False
                
                # 检查nick_name字段是否存在
                columns = conn.execute(db.text("PRAGMA table_info(users);")).fetchall()
                column_names = [row[1] for row in columns]
                
                if 'nick_name' in column_names:
                    logger.info("nick_name字段已经存在，无需修复")
                    return True
                
                # 添加nick_name字段
                logger.info("正在添加nick_name字段到users表")
                conn.execute(db.text("ALTER TABLE users ADD COLUMN nick_name TEXT;")).fetchall()
                logger.info("nick_name字段添加成功")
                
                # 验证修复结果
                updated_columns = conn.execute(db.text("PRAGMA table_info(users);")).fetchall()
                updated_column_names = [row[1] for row in updated_columns]
                if 'nick_name' in updated_column_names:
                    logger.info("修复验证成功：nick_name字段已存在于users表中")
                    return True
                else:
                    logger.error("修复验证失败：nick_name字段仍不存在")
                    return False
    
    except Exception as e:
        logger.error(f"修复过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("启动修复脚本")
    success = fix_nickname_column()
    
    if success:
        logger.info("修复成功完成")
        sys.exit(0)
    else:
        logger.error("修复失败")
        sys.exit(1)
