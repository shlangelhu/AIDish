from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # 姓名
    gender = db.Column(db.String(10), nullable=False)  # 性别
    height = db.Column(db.Float, nullable=False)  # 身高(cm)
    weight = db.Column(db.Float, nullable=False)  # 体重(kg)
    age = db.Column(db.Integer, nullable=False)  # 年龄
    education = db.Column(db.String(20), nullable=False)  # 学历
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    meals = db.relationship('StudentMeal', backref='user', lazy=True)

class Meal(db.Model):
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    meal_items = db.relationship('MealItem', backref='meal', lazy=True)

class MealItem(db.Model):
    __tablename__ = 'meal_items'
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # 克
    calories = db.Column(db.Float, nullable=False)  # 千卡
    protein = db.Column(db.Float, nullable=False)  # 克
    fat = db.Column(db.Float, nullable=False)  # 克
    carbohydrate = db.Column(db.Float, nullable=False)  # 克

class Food(db.Model):
    __tablename__ = 'foods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # 标准重量(g)
    calories = db.Column(db.Float, nullable=False)  # 热量(kcal)
    fat = db.Column(db.Float, nullable=False)  # 脂肪(g)
    protein = db.Column(db.Float, nullable=False)  # 蛋白质(g)
    calcium = db.Column(db.Float)  # 钙(mg)
    iron = db.Column(db.Float)  # 铁(mg)
    zinc = db.Column(db.Float)  # 锌(mg)
    magnesium = db.Column(db.Float)  # 镁(mg)
    vitamin_a = db.Column(db.Float)  # 维生素A(mg)
    vitamin_b1 = db.Column(db.Float)  # 维生素B1(mg)
    vitamin_b2 = db.Column(db.Float)  # 维生素B2(mg)
    vitamin_c = db.Column(db.Float)  # 维生素C(mg)
    vitamin_d = db.Column(db.Float)  # 维生素D(mg)
    vitamin_e = db.Column(db.Float)  # 维生素E(mg)
    meals = db.relationship('StudentMeal', backref='food', lazy=True)

class StudentMeal(db.Model):
    __tablename__ = 'student_meals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # 用餐类型：早餐、午餐、晚餐
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    amount = db.Column(db.Float, nullable=False, default=1)  # 份数
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name,
            'food_id': self.food_id,
            'food_name': self.food.name,
            'meal_type': self.meal_type,
            'date': self.date.strftime('%Y-%m-%d'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class PreselectedMeal(db.Model):
    """用户预选餐表"""
    __tablename__ = 'preselected_meals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # 用餐类型：1早餐、2午餐、3晚餐
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False, default=1)  # 份数
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 建立关联
    user = db.relationship('User', backref=db.backref('preselected_meals', lazy=True))
    food = db.relationship('Food', backref=db.backref('preselected_meals', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food.name,
            'meal_type': self.meal_type,
            'date': self.date.strftime('%Y-%m-%d'),
            'amount': self.amount,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class UserSpirit(db.Model):
    """用户营养精灵表"""
    __tablename__ = 'user_spirit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    user_name = db.Column(db.String(50), nullable=False)
    spirit_name = db.Column(db.String(50), nullable=False)
    spirit_level = db.Column(db.Integer, nullable=False, default=1)
    spirit_exp = db.Column(db.Integer, nullable=False, default=0)
    height = db.Column(db.Integer, nullable=False)  # 单位: cm
    weight = db.Column(db.Integer, nullable=False)  # 单位: kg
    iq = db.Column(db.Integer, nullable=False)
    strength = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 建立与User表的关联
    user = db.relationship('User', backref=db.backref('spirit', uselist=False))

    def __repr__(self):
        return f'<UserSpirit {self.spirit_name}>'