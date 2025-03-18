import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.app import create_app
from src.models.models import db, User, Food, StudentMeal

def init_meal_data():
    app = create_app()
    with app.app_context():
        # 确保表已创建
        db.create_all()
        
        # 获取小红的用户信息
        user = User.query.filter_by(name='小红').first()
        if not user:
            print("未找到用户'小红'")
            return
        
        # 获取食物信息
        foods = {
            '排骨': Food.query.filter_by(name='排骨').first(),
            '三文鱼': Food.query.filter_by(name='三文鱼').first(),
            '花菜': Food.query.filter_by(name='花菜').first()
        }
        
        if not all(foods.values()):
            print("未找到所需的食物数据")
            return
        
        # 创建用餐记录
        meals_data = [
            {
                'user_id': user.id,
                'food_id': foods['排骨'].id,
                'meal_type': '1',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['三文鱼'].id,
                'meal_type': '1',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['花菜'].id,
                'meal_type': '1',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['排骨'].id,
                'meal_type': '2',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['三文鱼'].id,
                'meal_type': '2',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['花菜'].id,
                'meal_type': '2',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['排骨'].id,
                'meal_type': '3',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['三文鱼'].id,
                'meal_type': '3',
                'date': datetime(2025, 3, 15).date()
            },
            {
                'user_id': user.id,
                'food_id': foods['花菜'].id,
                'meal_type': '3',
                'date': datetime(2025, 3, 15).date()
            }
        ]
        
        # 清空现有用餐数据
        StudentMeal.query.delete()
        
        # 插入新的用餐数据
        for meal_data in meals_data:
            meal = StudentMeal(**meal_data)
            db.session.add(meal)
        
        try:
            db.session.commit()
            print("用餐数据初始化完成！")
            
            # 验证数据
            meals = StudentMeal.query.all()
            print("\n已添加的用餐记录：")
            for meal in meals:
                print(f"用户：{meal.user.name}, 食物：{meal.food.name}, 类型：{meal.meal_type}, 日期：{meal.date}")
                
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败：{str(e)}")

if __name__ == "__main__":
    init_meal_data()
