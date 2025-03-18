import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.app import create_app
from src.models.models import User, UserSpirit, db

def init_spirit_data():
    """初始化用户营养精灵数据"""
    app = create_app()
    
    with app.app_context():
        # 获取所有用户
        users = User.query.all()
        
        # 为每个用户创建精灵
        for user in users:
            # 检查用户是否已有精灵
            existing_spirit = UserSpirit.query.filter_by(user_id=user.id).first()
            if existing_spirit:
                continue
            
            # 根据用户性别设置不同的初始属性
            if user.gender == "男":
                height = 100
                weight = 20
                iq = 40
                strength = 40
                spirit_name = f"{user.name}的小勇士"
            else:
                height = 95
                weight = 18
                iq = 45
                strength = 35
                spirit_name = f"{user.name}的小仙女"
            
            # 创建精灵
            spirit = UserSpirit(
                user_id=user.id,
                user_name=user.name,
                spirit_name=spirit_name,
                spirit_level=1,
                spirit_exp=0,
                height=height,
                weight=weight,
                iq=iq,
                strength=strength
            )
            
            db.session.add(spirit)
        
        try:
            db.session.commit()
            print("营养精灵数据初始化成功！")
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败：{str(e)}")

if __name__ == '__main__':
    init_spirit_data()
