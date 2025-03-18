from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.models import UserSpirit, User, db
from datetime import datetime

spirit_bp = Blueprint('spirit', __name__)

@spirit_bp.route('/info', methods=['GET'])
@jwt_required()
def get_spirit_info():
    """获取用户营养精灵信息
    
    返回:
    - 用户的营养精灵信息，包括等级、经验值、属性等
    - 如果用户还没有精灵，返回404
    """
    current_user_id = get_jwt_identity()
    
    # 查询用户的精灵信息
    spirit = UserSpirit.query.filter_by(user_id=current_user_id).first()
    
    if not spirit:
        return jsonify({
            "message": "未找到营养精灵信息，请先创建精灵"
        }), 404
    
    # 计算下一级所需经验值
    next_level_exp = spirit.spirit_level * 100
    
    # 计算当前等级的经验值百分比
    exp_percentage = (spirit.spirit_exp / next_level_exp) * 100
    
    return jsonify({
        "spirit": {
            "name": spirit.spirit_name,
            "level": spirit.spirit_level,
            "exp": spirit.spirit_exp,
            "next_level_exp": next_level_exp,
            "exp_percentage": f"{exp_percentage:.1f}%",
            "attributes": {
                "height": spirit.height,
                "weight": spirit.weight,
                "iq": spirit.iq,
                "strength": spirit.strength
            },
            #"status": get_spirit_status(spirit),
            "created_at": spirit.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": spirit.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200

@spirit_bp.route('/name', methods=['POST'])
@jwt_required()
def update_spirit_name():
    """修改营养精灵名称
    
    请求体:
    {
        "name": "新的精灵名称"
    }
    
    返回:
    - 更新后的精灵信息
    - 如果用户还没有精灵，返回404
    - 如果名称为空或超过长度限制，返回400
    """
    current_user_id = get_jwt_identity()
    
    # 获取请求数据
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    # 验证名称
    if not new_name:
        return jsonify({
            "message": "精灵名称不能为空"
        }), 400
    
    if len(new_name) > 50:
        return jsonify({
            "message": "精灵名称不能超过50个字符"
        }), 400
    
    # 查询用户的精灵信息
    spirit = UserSpirit.query.filter_by(user_id=current_user_id).first()
    
    if not spirit:
        return jsonify({
            "message": "未找到营养精灵信息，请先创建精灵"
        }), 404
    
    # 更新名称
    spirit.spirit_name = new_name
    spirit.updated_at = datetime.now()
    
    try:
        db.session.commit()
        return jsonify({
            "message": "精灵名称更新成功",
            "spirit": {
                "name": spirit.spirit_name,
                "level": spirit.spirit_level,
                "exp": spirit.spirit_exp,
                "attributes": {
                    "height": spirit.height,
                    "weight": spirit.weight,
                    "iq": spirit.iq,
                    "strength": spirit.strength
                },
                "updated_at": spirit.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "更新失败，请稍后重试"
        }), 500

def get_spirit_status(spirit):
    """获取精灵状态评价"""
    status = {
        "physical": {
            "bmi": calculate_bmi(spirit.height, spirit.weight),
            "strength_level": get_strength_level(spirit.strength)
        },
        "mental": {
            "iq_level": get_iq_level(spirit.iq)
        }
    }
    return status

def calculate_bmi(height, weight):
    """计算BMI指数"""
    height_m = height / 100  # 转换为米
    bmi = weight / (height_m * height_m)
    
    if bmi < 18.5:
        status = "偏瘦"
    elif bmi < 24:
        status = "正常"
    elif bmi < 28:
        status = "偏胖"
    else:
        status = "肥胖"
    
    return {
        "value": round(bmi, 1),
        "status": status
    }

def get_strength_level(strength):
    """获取力量等级"""
    if strength < 30:
        return {"level": "弱小", "description": "需要多补充蛋白质和钙质"}
    elif strength < 60:
        return {"level": "普通", "description": "可以适当增加营养摄入"}
    elif strength < 90:
        return {"level": "强壮", "description": "继续保持良好的饮食习惯"}
    else:
        return {"level": "超强", "description": "营养摄入非常均衡"}

def get_iq_level(iq):
    """获取智力等级"""
    if iq < 30:
        return {"level": "迟钝", "description": "需要补充维生素B族和DHA"}
    elif iq < 60:
        return {"level": "普通", "description": "可以多吃一些补脑食物"}
    elif iq < 90:
        return {"level": "聪明", "description": "智力发育良好"}
    else:
        return {"level": "天才", "description": "营养摄入帮助了大脑发育"}
