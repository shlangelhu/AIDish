from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(80))
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<User {self.username}>'

class Food(db.Model):
    """食物表"""
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Float)  # 热量(kcal)
    protein = db.Column(db.Float)  # 蛋白质(g)
    fat = db.Column(db.Float)  # 脂肪(g)
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    meals = db.relationship('StudentMeal', backref='food', lazy=True)

    def __repr__(self):
        return f'<Food {self.name}>'

class StudentMeal(db.Model):
    """学生用餐记录表"""
    __tablename__ = 'student_meals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # 1: 早餐, 2: 午餐, 3: 晚餐
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<StudentMeal {self.user_id}-{self.food_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'food_id': self.food_id,
            'meal_type': self.meal_type,
            'date': self.date.strftime('%Y-%m-%d'),
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
