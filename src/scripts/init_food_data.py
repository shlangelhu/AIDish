import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.app import create_app
from src.models.models import db, Food

def init_food_data():
    app = create_app()
    with app.app_context():
        # 确保表已创建
        db.create_all()
        
        # 初始化食物数据
        foods_data = [
            {
                "name": "排骨",
                "weight": 100,
                "calories": 264,
                "fat": 20.4,
                "protein": 18.3,
                "calcium": 8,
                "iron": 0.8,
                "zinc": 3.36,
                "vitamin_a": None,
                "vitamin_b": None,
                "vitamin_c": None
            },
            {
                "name": "三文鱼",
                "weight": 100,
                "calories": 130,
                "fat": 7.4,
                "protein": 21,
                "calcium": 286,
                "iron": 0.34,
                "zinc": None,
                "vitamin_a": 0.058,
                "vitamin_b": 0.16,
                "vitamin_c": None
            },
            {
                "name": "花菜",
                "weight": 100,
                "calories": 24,
                "fat": 0.2,
                "protein": 2.1,
                "calcium": 23,
                "iron": 1.1,
                "zinc": 0.38,
                "vitamin_a": 0.005,
                "vitamin_b": None,
                "vitamin_c": 61
            },
            {
                "name": "香菇",
                "weight": 100,
                "calories": 278,
                "fat": 1.8,
                "protein": 20,
                "calcium": 124,
                "iron": 25.3,
                "zinc": 3.36,
                "vitamin_a": 0.004,
                "vitamin_b": 1.2,
                "vitamin_c": None
            },
            {
                "name": "意大利面",
                "weight": 100,
                "calories": 350,
                "fat": 2,
                "protein": 12,
                "calcium": 8,
                "iron": 1.1,
                "zinc": None,
                "vitamin_a": 0.004,
                "vitamin_b": 0.6,
                "vitamin_c": None
            },
            {
                "name": "牛奶",
                "weight": 200,
                "calories": 130,
                "fat": 6.4,
                "protein": 6.6,
                "calcium": 236,
                "iron": None,
                "zinc": 0.4,
                "vitamin_a": 0.12,
                "vitamin_b": 0.22,
                "vitamin_c": None
            },
            {
                "name": "鸡蛋",
                "weight": 50,
                "calories": 77,
                "fat": 5.5,
                "protein": 6.5,
                "calcium": 28,
                "iron": 2.7,
                "zinc": 1.0,
                "vitamin_a": 0.234,
                "vitamin_b": 0.3,
                "vitamin_c": None
            },
            {
                "name": "菠菜",
                "weight": 100,
                "calories": 23,
                "fat": 0.4,
                "protein": 2.9,
                "calcium": 23,
                "iron": 2.7,
                "zinc": 0.85,
                "vitamin_a": 0.487,
                "vitamin_b": None,
                "vitamin_c": 39
            }
        ]
        
        # 清空现有数据
        Food.query.delete()
        
        # 插入新数据
        for food_data in foods_data:
            food = Food(**food_data)
            db.session.add(food)
        
        db.session.commit()
        print("食物数据初始化完成！")

if __name__ == "__main__":
    init_food_data()
