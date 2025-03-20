from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
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

@auth_bp.route('/check_username', methods=['GET'])
def check_username():
    """检查用户名是否已经注册
    
    参数:
    - username: 要检查的用户名（通过查询参数传递）
    
    返回:
    {
        "exists": true/false,      # 用户名是否已存在
        "message": "提示信息"
    }
    """
    username = request.args.get('username')
    if not username:
        return jsonify({
            "exists": False,
            "message": "请提供要检查的用户名"
        }), 400
    
    # 检查用户名格式
    if len(username) < 3 or len(username) > 20:
        return jsonify({
            "exists": False,
            "message": "用户名长度必须在3-20个字符之间"
        }), 400
    
    # 检查用户名是否已存在
    user = User.query.filter_by(username=username).first()
    
    return jsonify({
        "exists": user is not None,
        "message": "用户名已存在" if user else "用户名可用"
    }), 200

@auth_bp.route('/profile', methods=['POST'])
@jwt_required()
def update_profile():
    """更新用户信息（需要JWT鉴权）
    
    请求体格式:
    {
        "name": "张三",          # 可选，显示的姓名
        "gender": "男",          # 可选，性别
        "height": 170,          # 可选，身高
        "weight": 60,           # 可选，体重
        "age": 25,              # 可选，年龄
        "education": "本科"      # 可选，学历
    }
    
    返回:
    - 成功: 返回更新后的用户信息
    - 失败: 返回错误信息
    """
    data = request.get_json()
    
    # 从 JWT 中获取用户名
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    
    # 验证可选字段的格式
    if 'gender' in data and data['gender'] not in ['男', '女']:
        return jsonify({"message": "性别必须是'男'或'女'"}), 400
        
    if 'height' in data and (not isinstance(data['height'], (int, float)) or data['height'] <= 0):
        return jsonify({"message": "身高必须是大于0的数字"}), 400
        
    if 'weight' in data and (not isinstance(data['weight'], (int, float)) or data['weight'] <= 0):
        return jsonify({"message": "体重必须是大于0的数字"}), 400
        
    if 'age' in data and (not isinstance(data['age'], int) or data['age'] <= 0):
        return jsonify({"message": "年龄必须是大于0的整数"}), 400
    
    try:
        # 更新用户信息
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'height' in data:
            user.height = data['height']
        if 'weight' in data:
            user.weight = data['weight']
        if 'age' in data:
            user.age = data['age']
        if 'education' in data:
            user.education = data['education']
        
        db.session.commit()
        
        return jsonify({
            "message": "用户信息更新成功",
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"更新失败：{str(e)}"}), 500
