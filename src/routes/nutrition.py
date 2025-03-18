from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from src.models.models import db, Food, StudentMeal, User, UserSpirit

nutrition_bp = Blueprint('nutrition', __name__)

def get_meal_type_by_time(current_time=None):
    """根据时间判断用餐类型
    
    时间段划分：
    - 早餐：5:00-10:00
    - 午餐：10:00-15:00
    - 晚餐：15:00-23:00
    - 其他时间段默认为最近的下一顿
    
    Args:
        current_time: datetime对象，默认为当前时间
    
    Returns:
        str: 用餐类型 '1'早餐, '2'午餐, '3'晚餐
    """
    if current_time is None:
        current_time = datetime.now()
    
    hour = current_time.hour
    
    if 5 <= hour < 10:
        return '1'  # 早餐
    elif 10 <= hour < 15:
        return '2'  # 午餐
    elif 15 <= hour < 23:
        return '3'  # 晚餐
    else:  # 23:00-5:00
        return '1'  # 第二天的早餐

@nutrition_bp.route('/meals', methods=['POST'])
@jwt_required()
def record_meal():
    """记录用户的饮食情况
    
    请求体格式:
    {
        "date": "2025-03-18",  # 可选，默认为当天
        "meal_type": "1",      # 可选，1: 早餐, 2: 午餐, 3: 晚餐，不传则根据当前时间判断
        "foods": [
            {
                "food_id": 1,
                "amount": 1     # 可选，默认为1
            },
            {
                "food_id": 2,
                "amount": 0.5
            }
        ]
    }
    
    返回:
    - 成功: 返回记录的饮食信息和精灵成长信息
    - 失败: 返回错误信息
    """
    current_user_id = get_jwt_identity()
    
    # 获取请求数据
    data = request.get_json()
        
    if not data.get('foods') or not isinstance(data.get('foods'), list) or len(data.get('foods')) == 0:
        return jsonify({"message": "必须提供至少一种食物"}), 400
    
    # 获取用餐类型，如果没有提供则根据当前时间判断
    meal_type = str(data.get('meal_type', ''))
    if not meal_type:
        current_time = datetime.now()
        meal_type = get_meal_type_by_time(current_time)
    elif meal_type not in ['1', '2', '3']:
        return jsonify({"message": "用餐类型必须是：1(早餐)、2(午餐)或3(晚餐)"}), 400
    
    # 获取日期，默认为当天
    try:
        if 'date' in data:
            meal_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        else:
            meal_date = datetime.now().date()
    except ValueError:
        return jsonify({"message": "日期格式错误，请使用YYYY-MM-DD格式"}), 400
    
    # 验证每个食物ID是否存在
    food_ids = [food['food_id'] for food in data['foods']]
    foods = Food.query.filter(Food.id.in_(food_ids)).all()
    if len(foods) != len(food_ids):
        return jsonify({"message": "部分食物ID不存在"}), 400
    
    # 检查是否已经记录过该餐
    existing_meals = StudentMeal.query.filter_by(
        user_id=current_user_id,
        date=meal_date,
        meal_type=meal_type
    ).all()
    
    if existing_meals:
        # 如果已存在记录，先删除旧记录
        for meal in existing_meals:
            db.session.delete(meal)
    
    # 创建新的饮食记录
    new_meals = []
    recorded_foods = []
    
    try:
        for food_data in data['foods']:
            food_id = food_data['food_id']
            amount = food_data.get('amount', 1)  # 默认份数为1
            
            # 验证份数是否合理
            if amount <= 0:
                return jsonify({"message": f"食物ID {food_id} 的份数必须大于0"}), 400
            
            # 创建记录
            meal = StudentMeal(
                user_id=current_user_id,
                food_id=food_id,
                meal_type=meal_type,
                date=meal_date,
                amount=amount
            )
            db.session.add(meal)
            new_meals.append(meal)
            
            # 记录食物信息用于返回
            food = next(f for f in foods if f.id == food_id)
            recorded_foods.append({
                "food_id": food_id,
                "food_name": food.name,
                "amount": amount,
                "nutrition": {
                    "calories": food.calories * amount,
                    "protein": food.protein * amount,
                    "fat": food.fat * amount,
                    "calcium": food.calcium * amount if food.calcium else None,
                    "iron": food.iron * amount if food.iron else None,
                    "zinc": food.zinc * amount if food.zinc else None,
                    "magnesium": food.magnesium * amount if food.magnesium else None,
                    "vitamin_a": food.vitamin_a * amount if food.vitamin_a else None,
                    "vitamin_b1": food.vitamin_b1 * amount if food.vitamin_b1 else None,
                    "vitamin_b2": food.vitamin_b2 * amount if food.vitamin_b2 else None,
                    "vitamin_c": food.vitamin_c * amount if food.vitamin_c else None,
                    "vitamin_d": food.vitamin_d * amount if food.vitamin_d else None,
                    "vitamin_e": food.vitamin_e * amount if food.vitamin_e else None
                }
            })
        
        # 计算该餐的总营养值
        total_nutrition = calculate_total_nutrition(recorded_foods)
        
        # 更新精灵属性
        spirit_update = update_spirit_attributes(current_user_id, total_nutrition)
        
        # 提交所有更改
        db.session.commit()
        
        return jsonify({
            "message": "饮食记录添加成功",
            "meal": {
                "date": meal_date.strftime('%Y-%m-%d'),
                "meal_type": meal_type,
                "foods": recorded_foods,
                "total_nutrition": total_nutrition
            },
            "spirit": spirit_update
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"记录失败：{str(e)}"}), 500

def update_spirit_attributes(user_id, total_nutrition):
    """更新精灵属性
    
    根据用户的饮食记录更新精灵的经验值和属性
    
    Args:
        user_id: 用户ID
        total_nutrition: 该餐的总营养值
    
    Returns:
        更新后的精灵信息
    """
    spirit = UserSpirit.query.filter_by(user_id=user_id).first()
    if not spirit:
        return None
    
    # 基础经验值增长（每记录一餐+5经验）
    exp_gain = 5
    
    # 根据营养均衡程度增加额外经验
    nutrition_balance = 0
    if total_nutrition['calories'] > 0:
        nutrition_balance += 1
    if total_nutrition['protein'] > 0:
        nutrition_balance += 1
    if total_nutrition['fat'] > 0:
        nutrition_balance += 1
    if total_nutrition['calcium'] > 0:
        nutrition_balance += 1
        
    # 营养均衡度越高，获得的经验越多（每种营养+2经验）
    exp_gain += nutrition_balance * 2
    
    # 更新经验值
    spirit.spirit_exp += exp_gain
    
    # 检查是否升级（每级所需经验值为：当前等级×200）
    next_level_exp = spirit.spirit_level * 200
    while spirit.spirit_exp >= next_level_exp:
        spirit.spirit_exp -= next_level_exp
        spirit.spirit_level += 1
        next_level_exp = spirit.spirit_level * 200
    
    # 根据摄入的营养更新属性
    # 热量影响体重（每2000卡路里增加0.1体重）
    if total_nutrition['calories'] > 0:
        weight_gain = min(total_nutrition['calories'] / 2000 * 0.1, 0.1)
        spirit.weight = min(spirit.weight + weight_gain, 100)
    
    # 蛋白质影响力量（每30g蛋白质增加0.1力量）
    if total_nutrition['protein'] > 0:
        strength_gain = min(total_nutrition['protein'] / 30 * 0.1, 0.1)
        spirit.strength = min(spirit.strength + strength_gain, 100)
    
    # 钙质和维生素D影响身高（每天最多增加0.05身高）
    if total_nutrition['calcium'] > 0 or total_nutrition.get('vitamin_d', 0) > 0:
        height_gain = 0.05
        spirit.height = min(spirit.height + height_gain, 200)
    
    # 维生素影响智力（每种维生素增加0.05智力）
    vitamins_count = sum(1 for k in ['vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_c', 'vitamin_d', 'vitamin_e'] 
                        if total_nutrition.get(k, 0) > 0)
    if vitamins_count > 0:
        iq_gain = vitamins_count * 0.05
        spirit.iq = min(spirit.iq + iq_gain, 100)
    
    spirit.updated_at = datetime.now()
    
    return {
        "name": spirit.spirit_name,
        "level": spirit.spirit_level,
        "exp": spirit.spirit_exp,
        "next_level_exp": next_level_exp,
        "exp_gained": exp_gain,
        "attributes": {
            "height": round(spirit.height, 2),
            "weight": round(spirit.weight, 2),
            "iq": round(spirit.iq, 2),
            "strength": round(spirit.strength, 2)
        }
    }

def calculate_total_nutrition(foods):
    """计算多个食物的总营养值"""
    total = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "calcium": 0,
        "iron": 0,
        "zinc": 0,
        "magnesium": 0,
        "vitamin_a": 0,
        "vitamin_b1": 0,
        "vitamin_b2": 0,
        "vitamin_c": 0,
        "vitamin_d": 0,
        "vitamin_e": 0
    }
    
    for food in foods:
        nutrition = food['nutrition']
        for key in total:
            if nutrition[key] is not None:
                total[key] += nutrition[key]
    
    return total

@nutrition_bp.route('/meals', methods=['GET'])
@jwt_required()
def get_meals():
    """查询指定日期的饮食记录
    
    参数:
    - date: 查询日期，格式为YYYY-MM-DD，可选，默认为今天
    
    返回:
    - 指定日期的所有三餐记录，每餐包含食物信息和总营养成分
    """
    current_user_id = get_jwt_identity()
    
    # 获取查询参数
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        # 转换日期字符串为datetime对象
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "日期格式错误，请使用YYYY-MM-DD格式"}), 400
    
    # 查询指定日期的所有用餐记录
    meals = StudentMeal.query.filter(
        StudentMeal.user_id == current_user_id,
        StudentMeal.date == query_date
    ).order_by(StudentMeal.meal_type).all()
    
    if not meals:
        return jsonify({
            "message": "未找到记录",
            "date": date_str
        }), 404
    
    # 按餐次分组整理数据
    meals_by_type = {
        "1": {"foods": [], "total_nutrition": initialize_nutrition_dict()},
        "2": {"foods": [], "total_nutrition": initialize_nutrition_dict()},
        "3": {"foods": [], "total_nutrition": initialize_nutrition_dict()}
    }
    
    # 总营养摄入
    total_nutrition = initialize_nutrition_dict()
    
    # 统计每餐的食物和营养成分
    for meal in meals:
        meal_info = {
            "food_id": meal.food_id,
            "food_name": meal.food.name,
            "nutrition": get_food_nutrition(meal.food)
        }
        
        # 添加食物到对应餐次
        meals_by_type[meal.meal_type]["foods"].append(meal_info)
        
        # 累计该餐次的营养成分
        meal_type_nutrition = meals_by_type[meal.meal_type]["total_nutrition"]
        for nutrient in meal_type_nutrition:
            meal_type_nutrition[nutrient] += getattr(meal.food, nutrient) or 0
            total_nutrition[nutrient] += getattr(meal.food, nutrient) or 0
    
    # 计算每种营养素占推荐值的百分比
    user = User.query.get(current_user_id)
    nutrition_analysis = {}
    for nutrient, value in total_nutrition.items():
        nutrition_analysis[nutrient] = analyze_nutrition(
            value,
            user.gender,
            user.age,
            nutrient
        )
    
    return jsonify({
        "date": date_str,
        "meals": {
            "1": {
                "foods": meals_by_type["1"]["foods"],
                "total_nutrition": meals_by_type["1"]["total_nutrition"]
            },
            "2": {
                "foods": meals_by_type["2"]["foods"],
                "total_nutrition": meals_by_type["2"]["total_nutrition"]
            },
            "3": {
                "foods": meals_by_type["3"]["foods"],
                "total_nutrition": meals_by_type["3"]["total_nutrition"]
            }
        },
        "total_nutrition": total_nutrition,
        "nutrition_analysis": nutrition_analysis
    }), 200

def initialize_nutrition_dict():
    """初始化营养字典"""
    return {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "calcium": 0,
        "iron": 0,
        "zinc": 0,
        "magnesium": 0,
        "vitamin_a": 0,
        "vitamin_b1": 0,
        "vitamin_b2": 0,
        "vitamin_c": 0,
        "vitamin_d": 0,
        "vitamin_e": 0
    }

def get_food_nutrition(food):
    """获取食物的营养信息"""
    return {
        "calories": food.calories,
        "protein": food.protein,
        "fat": food.fat,
        "calcium": food.calcium,
        "iron": food.iron,
        "zinc": food.zinc,
        "magnesium": food.magnesium,
        "vitamin_a": food.vitamin_a,
        "vitamin_b1": food.vitamin_b1,
        "vitamin_b2": food.vitamin_b2,
        "vitamin_c": food.vitamin_c,
        "vitamin_d": food.vitamin_d,
        "vitamin_e": food.vitamin_e
    }

@nutrition_bp.route('/foods', methods=['GET'])
@jwt_required()
def get_foods():
    """获取所有可用的食物列表"""
    foods = Food.query.all()
    return jsonify({
        "foods": [{
            "id": food.id,
            "name": food.name,
            "calories": food.calories,
            "protein": food.protein,
            "fat": food.fat,
            "calcium": food.calcium,
            "iron": food.iron,
            "zinc": food.zinc,
            "vitamin_a": food.vitamin_a,
            "vitamin_b1": food.vitamin_b1,
            "vitamin_c": food.vitamin_c
        } for food in foods]
    }), 200

@nutrition_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """获取用户的营养摄入统计和分析
    
    参数:
    - start_date: 开始日期，格式为YYYY-MM-DD，可选，默认为7天前
    - end_date: 结束日期，格式为YYYY-MM-DD，可选，默认为今天
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 获取日期参数，如果未提供则使用最近7天
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    today = datetime.now().date()
    
    try:
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = today
            
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # 默认查询最近7天
            start = end - timedelta(days=6)  # 6天前到今天，共7天
            
    except ValueError:
        return jsonify({"message": "日期格式错误，请使用YYYY-MM-DD格式"}), 400
    
    # 确保开始日期不晚于结束日期
    if start > end:
        return jsonify({"message": "开始日期不能晚于结束日期"}), 400
    
    # 查询指定日期范围内的所有用餐记录
    meals = StudentMeal.query.filter(
        StudentMeal.user_id == current_user_id,
        StudentMeal.date >= start,
        StudentMeal.date <= end
    ).all()
    
    if not meals:
        return jsonify({
            "message": "未找到记录",
            "date_range": {
                "start": start.strftime('%Y-%m-%d'),
                "end": end.strftime('%Y-%m-%d')
            }
        }), 404
    
    # 按日期分组统计
    daily_stats = {}
    for meal in meals:
        date_str = meal.date.strftime('%Y-%m-%d')
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                "meals_count": 0,
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "calcium": 0,
                "iron": 0,
                "zinc": 0,
                "magnesium": 0,
                "vitamin_a": 0,
                "vitamin_b1": 0,
                "vitamin_b2": 0,
                "vitamin_c": 0,
                "vitamin_d": 0,
                "vitamin_e": 0,
                "meals": []
            }
        
        stats = daily_stats[date_str]
        stats["meals_count"] += 1
        stats["calories"] += meal.food.calories
        stats["protein"] += meal.food.protein
        stats["fat"] += meal.food.fat
        stats["calcium"] += meal.food.calcium or 0
        stats["iron"] += meal.food.iron or 0
        stats["zinc"] += meal.food.zinc or 0
        stats["magnesium"] += meal.food.magnesium or 0
        stats["vitamin_a"] += meal.food.vitamin_a or 0
        stats["vitamin_b1"] += meal.food.vitamin_b1 or 0
        stats["vitamin_b2"] += meal.food.vitamin_b2 or 0
        stats["vitamin_c"] += meal.food.vitamin_c or 0
        stats["vitamin_d"] += meal.food.vitamin_d or 0
        stats["vitamin_e"] += meal.food.vitamin_e or 0
        stats["meals"].append({
            "meal_type": meal.meal_type,
            "food_name": meal.food.name,
            "calories": meal.food.calories
        })
    
    # 计算总体统计
    days_count = (end - start).days + 1
    total_stats = {
        "total_calories": sum(day["calories"] for day in daily_stats.values()),
        "total_protein": sum(day["protein"] for day in daily_stats.values()),
        "total_fat": sum(day["fat"] for day in daily_stats.values()),
        "total_calcium": sum(day["calcium"] for day in daily_stats.values()),
        "total_iron": sum(day["iron"] for day in daily_stats.values()),
        "total_zinc": sum(day["zinc"] for day in daily_stats.values()),
        "total_vitamin_a": sum(day["vitamin_a"] for day in daily_stats.values()),
        "total_vitamin_b1": sum(day["vitamin_b1"] for day in daily_stats.values()),
        "total_vitamin_b2": sum(day["vitamin_b2"] for day in daily_stats.values()),
        "total_vitamin_c": sum(day["vitamin_c"] for day in daily_stats.values()),
        "total_magnesium": sum(day["magnesium"] for day in daily_stats.values()),
        "total_vitamin_d": sum(day["vitamin_d"] for day in daily_stats.values()),
        "total_vitamin_e": sum(day["vitamin_e"] for day in daily_stats.values()),
        "days_count": days_count,
        "days_with_records": len(daily_stats),
        "meal_compliance_rate": f"{(len(daily_stats) / days_count * 100):.1f}%"
    }
    
    # 计算日均摄入
    daily_avgs = {
        "calories": total_stats["total_calories"] / days_count,
        "protein": total_stats["total_protein"] / days_count,
        "fat": total_stats["total_fat"] / days_count,
        "calcium": total_stats["total_calcium"] / days_count,
        "iron": total_stats["total_iron"] / days_count,
        "zinc": total_stats["total_zinc"] / days_count,
        "magnesium": total_stats["total_magnesium"] / days_count,
        "vitamin_a": total_stats["total_vitamin_a"] / days_count,
        "vitamin_b1": total_stats["total_vitamin_b1"] / days_count,
        "vitamin_b2": total_stats["total_vitamin_b2"] / days_count,
        "vitamin_c": total_stats["total_vitamin_c"] / days_count,
        "vitamin_d": total_stats["total_vitamin_d"] / days_count,
        "vitamin_e": total_stats["total_vitamin_e"] / days_count,
    }
    
    # 营养摄入分析
    nutrition_analysis = {}
    for nutrient, daily_avg in daily_avgs.items():
        nutrition_analysis[nutrient] = analyze_nutrition(
            daily_avg,
            user.gender,
            user.age,
            nutrient
        )
    
    return jsonify({
        "user": {
            "name": user.name,
            "gender": user.gender,
            "age": user.age,
            "height": user.height,
            "weight": user.weight
        },
        "date_range": {
            "start": start.strftime('%Y-%m-%d'),
            "end": end.strftime('%Y-%m-%d')
        },
        # "daily_statistics": daily_stats,
        "total_statistics": total_stats,
        "daily_averages": daily_avgs,
        "nutrition_analysis": nutrition_analysis
    }), 200

def get_nutrition_standard(nutrient_type, gender, age):
    """获取营养素的标准参考值"""
    standards = {
        "calories": {
            "男": {"<=18": 2700, ">18": 2400},
            "女": {"<=18": 2400, ">18": 2100}
        },
        "protein": {
            "男": {"<=18": 75, ">18": 65},
            "女": {"<=18": 65, ">18": 55}
        },
        "fat": {
            "男": {"<=18": 75, ">18": 70},
            "女": {"<=18": 65, ">18": 60}
        },
        "calcium": {
            "男": {"<=18": 1000, ">18": 800},
            "女": {"<=18": 1000, ">18": 800}
        },
        "iron": {
            "男": {"<=18": 12, ">18": 12},
            "女": {"<=18": 15, ">18": 15}
        },
        "zinc": {
            "男": {"<=18": 15, ">18": 15},
            "女": {"<=18": 12, ">18": 12}
        },
        "magnesium": {
            "男": {"<=18": 100, ">18": 100},
            "女": {"<=18": 100, ">18": 100}
        },
        "vitamin_a": {
            "男": {"<=18": 800, ">18": 800},
            "女": {"<=18": 700, ">18": 700}
        },
        "vitamin_b1": {
            "男": {"<=18": 1.4, ">18": 1.4},
            "女": {"<=18": 1.2, ">18": 1.2}
        },
        "vitamin_b2": {
            "男": {"<=18": 1.4, ">18": 1.4},
            "女": {"<=18": 1.2, ">18": 1.2}
        },
        "vitamin_c": {
            "男": {"<=18": 100, ">18": 100},
            "女": {"<=18": 100, ">18": 100}
        },
        "vitamin_d": {
            "男": {"<=18": 100, ">18": 100},
            "女": {"<=18": 100, ">18": 100}
        },
        "vitamin_e": {
            "男": {"<=18": 100, ">18": 100},
            "女": {"<=18": 100, ">18": 100}
        }
    }
    
    age_key = "<=18" if age <= 18 else ">18"
    return standards[nutrient_type][gender][age_key]

def get_nutrition_grade(percentage):
    """根据营养素摄入比例获取等级评定"""
    if percentage < 60:
        return {
            "grade": "严重不足",
            "level": 1,
            "description": "摄入量远低于推荐值，需要立即改善",
            "color": "red"
        }
    elif percentage < 80:
        return {
            "grade": "不足",
            "level": 2,
            "description": "摄入量低于推荐值，建议适当增加",
            "color": "orange"
        }
    elif percentage < 95:
        return {
            "grade": "略低",
            "level": 3,
            "description": "摄入量接近推荐值，可以适当增加",
            "color": "yellow"
        }
    elif percentage <= 105:
        return {
            "grade": "适中",
            "level": 4,
            "description": "摄入量符合推荐值，继续保持",
            "color": "green"
        }
    elif percentage <= 120:
        return {
            "grade": "充足",
            "level": 3,
            "description": "摄入量略高于推荐值，可以适当减少",
            "color": "blue"
        }
    elif percentage <= 140:
        return {
            "grade": "过量",
            "level": 2,
            "description": "摄入量明显高于推荐值，建议减少",
            "color": "orange"
        }
    else:
        return {
            "grade": "严重过量",
            "level": 1,
            "description": "摄入量远高于推荐值，需要立即控制",
            "color": "red"
        }

def analyze_nutrition(daily_avg, gender, age, nutrient_type):
    """分析营养摄入情况"""
    # 获取标准参考值
    standard = get_nutrition_standard(nutrient_type, gender, age)
    
    # 计算摄入比例
    percentage = (daily_avg / standard) * 100
    
    # 获取营养等级评定
    grade_info = get_nutrition_grade(percentage)
    
    # 生成建议
    if grade_info["level"] < 3:
        suggestion = f"建议增加{nutrient_type}的摄入，可以多吃以下食物："
        if nutrient_type == "protein":
            suggestion += "瘦肉、鱼、蛋、奶制品、豆制品等"
        elif nutrient_type == "calcium":
            suggestion += "牛奶、酸奶、小鱼干、豆制品等"
        elif nutrient_type == "iron":
            suggestion += "动物肝脏、瘦肉、菠菜等深色蔬菜"
        elif nutrient_type == "zinc":
            suggestion += "牡蛎、瘦肉、坚果等"
        elif nutrient_type == "magnesium":
            suggestion += "绿叶蔬菜、坚果、鱼类等"
        elif nutrient_type == "vitamin_a":
            suggestion += "胡萝卜、南瓜、菠菜、动物肝脏等"
        elif nutrient_type == "vitamin_b1":
            suggestion += "全谷物、瘦肉、蛋类、豆类等"
        elif nutrient_type == "vitamin_b2":
            suggestion += "牛奶、鸡蛋、绿叶蔬菜等"
        elif nutrient_type == "vitamin_c":
            suggestion += "柑橘类水果、青椒、西兰花等"
        elif nutrient_type == "vitamin_d":
            suggestion += "鱼类、蛋黄、奶制品等"
        elif nutrient_type == "vitamin_e":
            suggestion += "坚果、种子、绿叶蔬菜等"
        elif nutrient_type == "calories":
            suggestion += "全麦面包、燕麦、糙米、红薯、玉米等"
        elif nutrient_type == "fat":
            suggestion += "坚果、橄榄油、牛油果、三文鱼、芝麻等"
    elif grade_info["level"] > 3:
        suggestion = f"建议减少{nutrient_type}的摄入，可以："
        if nutrient_type == "calories":
            suggestion += "控制食量，增加运动量"
        elif nutrient_type == "fat":
            suggestion += "少吃油炸食品，选择蒸煮烤的烹饪方式"
        else:
            suggestion += "注意饮食均衡，不要过分偏食"
    else:
        suggestion = "目前摄入适中，请继续保持均衡的饮食习惯"
    
    return {
        "nutrient": nutrient_type,
        "current": round(daily_avg, 2),
        "standard": standard,
        "percentage": f"{percentage:.1f}%",
        "grade": grade_info["grade"],
        "level": grade_info["level"],
        "color": grade_info["color"],
        "description": grade_info["description"],
        "suggestion": suggestion
    }

def get_nutrition_analysis(daily_avgs, user):
    """分析用户的营养状况并提供建议
    
    Args:
        daily_avgs: 每日平均营养摄入量
        user: 用户对象，用于获取性别等信息
    
    Returns:
        包含营养分析和建议的字典
    """
    analysis = {
        "status": "良好",
        "deficiencies": [],
        "suggestions": []
    }
    
    # 根据性别确定每日推荐摄入量
    if user.gender == "男":
        recommended = {
            "calories": 2250,  # 千卡
            "protein": 65,     # 克
            "fat": 60,         # 克
            "calcium": 800,    # 毫克
            "iron": 12,        # 毫克
            "zinc": 12.5,      # 毫克
            "vitamin_a": 800,  # 微克
            "vitamin_b1": 1.4, # 毫克
            "vitamin_b2": 1.4, # 毫克
            "vitamin_c": 100,  # 毫克
            "vitamin_d": 10,   # 微克
            "vitamin_e": 14    # 毫克
        }
    else:
        recommended = {
            "calories": 1800,
            "protein": 55,
            "fat": 50,
            "calcium": 800,
            "iron": 20,
            "zinc": 7.5,
            "vitamin_a": 700,
            "vitamin_b1": 1.2,
            "vitamin_b2": 1.2,
            "vitamin_c": 100,
            "vitamin_d": 10,
            "vitamin_e": 14
        }
    
    # 定义营养素对应的食物推荐
    nutrient_foods = {
        "calories": ["全麦面包", "燕麦", "糙米", "红薯", "玉米"],
        "protein": ["鸡胸肉", "鱼", "鸡蛋", "豆腐", "牛奶"],
        "fat": ["坚果", "橄榄油", "牛油果", "三文鱼", "芝麻"],
        "calcium": ["牛奶", "酸奶", "豆腐", "虾皮", "芝麻"],
        "iron": ["菠菜", "瘦牛肉", "黑木耳", "红枣", "紫菜"],
        "zinc": ["牡蛎", "瘦牛肉", "南瓜子", "芝麻", "花生"],
        "vitamin_a": ["胡萝卜", "菠菜", "南瓜", "芒果", "红薯"],
        "vitamin_b1": ["糙米", "瘦猪肉", "花生", "豆类", "全麦面包"],
        "vitamin_b2": ["牛奶", "鸡蛋", "瘦肉", "香菇", "豆类"],
        "vitamin_c": ["猕猴桃", "柑橘", "青椒", "西兰花", "草莓"],
        "vitamin_d": ["鱼类", "蛋黄", "牛奶", "香菇", "海鲜"],
        "vitamin_e": ["坚果", "植物油", "豆类", "绿叶蔬菜", "全谷物"]
    }
    
    deficiencies = []
    suggestions = {}
    
    # 检查每种营养素的摄入情况
    for nutrient, recommended_value in recommended.items():
        if nutrient in daily_avgs:
            actual = daily_avgs[nutrient] or 0  # 处理None值
            ratio = (actual / recommended_value) * 100
            
            # 如果摄入量低于推荐量的70%，视为不足
            if ratio < 70:
                deficiencies.append({
                    "nutrient": nutrient,
                    "current": round(actual, 2),
                    "recommended": recommended_value,
                    "percentage": round(ratio, 1)
                })
                
                # 添加食物建议
                if nutrient in nutrient_foods:
                    suggestions[nutrient] = nutrient_foods[nutrient]
    
    # 更新分析状态
    if len(deficiencies) > 3:
        analysis["status"] = "需要注意"
    elif len(deficiencies) > 0:
        analysis["status"] = "一般"
    
    # 整理建议
    suggestion_text = []
    for nutrient, foods in suggestions.items():
        nutrient_names = {
            "calories": "热量",
            "protein": "蛋白质",
            "fat": "脂肪",
            "calcium": "钙",
            "iron": "铁",
            "zinc": "锌",
            "vitamin_a": "维生素A",
            "vitamin_b1": "维生素B1",
            "vitamin_b2": "维生素B2",
            "vitamin_c": "维生素C",
            "vitamin_d": "维生素D",
            "vitamin_e": "维生素E"
        }
        
        suggestion_text.append({
            "nutrient": nutrient_names.get(nutrient, nutrient),
            "foods": foods,
            "description": f"建议多吃：{', '.join(foods[:3])}等食物"
        })
    
    analysis["deficiencies"] = deficiencies
    analysis["suggestions"] = suggestion_text
    
    return analysis
