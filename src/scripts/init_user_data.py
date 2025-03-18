import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.app import create_app
from src.models.models import db, User
from werkzeug.security import generate_password_hash

def init_user_data():
    app = create_app()
    with app.app_context():
        # 确保表已创建
        db.create_all()
        
        # 初始化用户数据
        users_data = [
            {
                "username": "xiaohong",
                "password": generate_password_hash("123456"),
                "name": "小红",
                "gender": "女",
                "height": 158.0,
                "weight": 55.0,
                "age": 14,
                "education": "初中",
                'created_at': datetime.now()
            },
            {
                "username": "xiaoming",
                "password": generate_password_hash("123456"),
                "name": "小明",
                "gender": "男",
                "height": 166.0,
                "weight": 52.0,
                "age": 15,
                "education": "初中",
                'created_at': datetime.now()
            },
            {
                "username": "xiaozhang",
                "password": generate_password_hash("123456"),
                "name": "小张",
                "gender": "男",
                "height": 160.0,
                "weight": 53.0,
                "age": 15,
                "education": "初中",
                'created_at': datetime.now()
            }
        ]
        
        # 清空现有用户数据
        User.query.delete()
        
        # 插入新用户数据
        for user_data in users_data:
            user = User(**user_data)
            db.session.add(user)
        
        db.session.commit()
        print("用户数据初始化完成！")

if __name__ == "__main__":
    init_user_data()
