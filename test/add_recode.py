from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.models import db, StudentMeal, User, Food
from src.app import create_app

def add_test_records():
    """添加测试数据到 student_meals 表"""
    app = create_app()
    
    with app.app_context():
        # 获取所有用户
        users = User.query.all()
        if not users:
            print("错误：数据库中没有用户数据")
            return

        # 获取指定的食物
        food_names = ['排骨', '三文鱼', '花菜', '香菇', '意大利面']
        foods = Food.query.filter(Food.name.in_(food_names)).all()
        
        if len(foods) != len(food_names):
            print("错误：未找到所有指定的食物")
            found_names = [food.name for food in foods]
            print(f"已找到的食物: {found_names}")
            return

        # 设置日期范围
        start_date = datetime(2025, 3, 1).date()
        end_date = datetime(2025, 3, 28).date()
        meal_types = ['1', '2', '3']
        
        # 为每个用户添加记录
        total_records = 0
        for user in users:
            current_date = start_date
            while current_date <= end_date:
                for meal_type in meal_types:
                    # 为每餐添加5种食物
                    for food in foods:
                        new_meal = StudentMeal(
                            user_id=user.id,
                            food_id=food.id,
                            meal_type=meal_type,
                            date=current_date,
                            amount=1.0,
                            created_at=datetime.now()
                        )
                        db.session.add(new_meal)
                        total_records += 1
                
                # 每100条记录提交一次，避免内存占用过大
                if total_records % 100 == 0:
                    try:
                        db.session.commit()
                        print(f"已添加 {total_records} 条记录...")
                    except Exception as e:
                        db.session.rollback()
                        print(f"添加记录时发生错误：{str(e)}")
                        return
                
                current_date += timedelta(days=1)
        
        # 提交剩余的记录
        try:
            db.session.commit()
            print(f"成功完成！共添加了 {total_records} 条用餐记录！")
        except Exception as e:
            db.session.rollback()
            print(f"添加记录时发生错误：{str(e)}")

if __name__ == '__main__':
    add_test_records()