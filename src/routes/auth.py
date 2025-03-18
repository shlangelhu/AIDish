from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
from src.models.models import db, User, UserSpirit
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口
    
    请求体:
    {
        "username": "zhangsan",  # 登录用的用户名
        "name": "张三",          # 显示的姓名
        "password": "123456",
        "gender": "男",
        "height": 170,
        "weight": 60,
        "age": 25,
        "education": "本科"
    }
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'name', 'password', 'gender', 'height', 'weight', 'age', 'education']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"缺少必填字段: {field}"}), 400
    
    # 验证性别
    if data['gender'] not in ['男', '女']:
        return jsonify({"message": "性别必须是'男'或'女'"}), 400
    
    # 验证数值范围
    if not (0 < data['height'] <= 300):
        return jsonify({"message": "身高数值不合理"}), 400
    if not (0 < data['weight'] <= 500):
        return jsonify({"message": "体重数值不合理"}), 400
    if not (0 < data['age'] <= 150):
        return jsonify({"message": "年龄数值不合理"}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "用户名已存在"}), 400
    
    try:
        # 创建新用户
        new_user = User(
            username=data['username'],
            name=data['name'],
            password=generate_password_hash(data['password']),
            gender=data['gender'],
            height=data['height'],
            weight=data['weight'],
            age=data['age'],
            education=data['education']
        )
        db.session.add(new_user)
        db.session.flush()  # 获取new_user.id
        
        # 创建用户的营养精灵
        # 根据用户性别设置不同的初始属性
        if data['gender'] == "男":
            height = 100
            weight = 20
            iq = 40
            strength = 40
            spirit_name = f"{data['name']}的小勇士"
        else:
            height = 95
            weight = 18
            iq = 45
            strength = 35
            spirit_name = f"{data['name']}的小仙女"
        
        # 创建精灵
        new_spirit = UserSpirit(
            user_id=new_user.id,
            user_name=new_user.name,
            spirit_name=spirit_name,
            spirit_level=1,
            spirit_exp=0,
            height=height,
            weight=weight,
            iq=iq,
            strength=strength
        )
        db.session.add(new_spirit)
        
        # 提交事务
        db.session.commit()
        
        # 创建访问令牌
        access_token = create_access_token(
            identity=new_user.id,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            "message": "注册成功",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "name": new_user.name,
                "gender": new_user.gender,
                "height": new_user.height,
                "weight": new_user.weight,
                "age": new_user.age,
                "education": new_user.education
            },
            "spirit": {
                "name": new_spirit.spirit_name,
                "level": new_spirit.spirit_level,
                "exp": new_spirit.spirit_exp,
                "attributes": {
                    "height": new_spirit.height,
                    "weight": new_spirit.weight,
                    "iq": new_spirit.iq,
                    "strength": new_spirit.strength
                }
            },
            "access_token": access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"注册失败：{str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口
    
    请求体:
    {
        "username": "用户名",
        "password": "密码"
    }
    
    返回:
    {
        "token": "JWT令牌",
        "message": "登录成功"
    }
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    print('username:', username)
    print('password:', password)
    
    user = User.query.filter_by(username=username).first()
    print('user:', user)
    print('user.password:', user.password)
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(minutes=30)
        )
        return jsonify({
            "token": access_token,
            "message": "登录成功",
            "user": {
                "username": user.username,
                "name": user.name,
                "gender": user.gender,
                "height": user.height,
                "weight": user.weight,
                "age": user.age,
                "education": user.education
            }
        }), 200
    
    return jsonify({"message": "用户名或密码错误"}), 401
