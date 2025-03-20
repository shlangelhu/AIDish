from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.models import db, Food, StudentMeal, User, UserSpirit, PreselectedMeal
from datetime import datetime, timedelta

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
def record_meal():
    """记录用户的饮食情况
    
    请求体格式:
    {
        "username": "用户名",
        "date": "2025-03-18",  # 可选，默认为当天
        "meal_type": "1",      # 可选，1: 早餐, 2: 午餐, 3: 晚餐，不传则根据当前时间判断
        "foods": [
            {
                "food_name": "米饭",  # 食物名称
                "amount": 1     # 可选，默认为1
            },
            {
                "food_name": "红烧排骨",
                "amount": 0.5
            }
        ]
    }
    
    返回:
    - 成功: 返回记录的饮食信息和精灵成长信息
    - 失败: 返回错误信息
    """
    # 获取请求数据
    data = request.get_json()
    
    username = data.get('username')
    if not username:
        return jsonify({"message": "用户名不能为空"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    
    # 验证请求数据
    if not data.get('foods') or not isinstance(data.get('foods'), list) or len(data.get('foods')) == 0:
        return jsonify({"message": "必须提供至少一种食物"}), 400
    
    # 处理日期参数
    meal_date = data.get('date')
    if meal_date:
        try:
            meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "日期格式错误，应为YYYY-MM-DD"}), 400
    else:
        meal_date = datetime.now().date()
    
    # 处理餐点类型
    meal_type = data.get('meal_type')
    if not meal_type:
        meal_type = get_meal_type_by_time()
    
    # 检查是否已经记录过相同的食物
    existing_meals = StudentMeal.query.filter_by(
        user_id=user.id,
        date=meal_date,
        meal_type=meal_type
    ).all()
    
    # 获取已记录的食物ID列表
    recorded_food_ids = {meal.food_id for meal in existing_meals}
    
    try:
        recorded_foods = []
        skipped_foods = []
        
        # 处理每个食物
        for food_data in data['foods']:
            food_name = food_data.get('food_name')
            if not food_name:
                continue
                
            # 根据食物名称查找食物
            food = Food.query.filter_by(name=food_name).first()
            if not food:
                return jsonify({"message": f"未找到食物：{food_name}"}), 404
            
            # 如果食物已经记录过，则跳过
            if food.id in recorded_food_ids:
                skipped_foods.append(food_name)
                continue
                
            amount = food_data.get('amount', 1)
            
            # 创建记录
            meal = StudentMeal(
                user_id=user.id,
                food_id=food.id,
                meal_type=meal_type,
                date=meal_date,
                amount=amount
            )
            
            db.session.add(meal)
            recorded_foods.append({
                'food_name': food.name,
                'amount': amount,
                'nutrition': {
                    'calories': food.calories * amount if food.calories is not None else None,
                    'protein': food.protein * amount if food.protein is not None else None,
                    'fat': food.fat * amount if food.fat is not None else None,
                    'calcium': food.calcium * amount if food.calcium is not None else None,
                    'iron': food.iron * amount if food.iron is not None else None,
                    'zinc': food.zinc * amount if food.zinc is not None else None,
                    'magnesium': food.magnesium * amount if food.magnesium is not None else None,
                    'vitamin_a': food.vitamin_a * amount if food.vitamin_a is not None else None,
                    'vitamin_b1': food.vitamin_b1 * amount if food.vitamin_b1 is not None else None,
                    'vitamin_b2': food.vitamin_b2 * amount if food.vitamin_b2 is not None else None,
                    'vitamin_c': food.vitamin_c * amount if food.vitamin_c is not None else None,
                    'vitamin_d': food.vitamin_d * amount if food.vitamin_d is not None else None,
                    'vitamin_e': food.vitamin_e * amount if food.vitamin_e is not None else None
                }
            })
        
        if not recorded_foods:
            return jsonify({"message": "所有食物都已经记录过了", "skipped_foods": skipped_foods}), 400
        
        # 计算该餐的总营养值
        total_nutrition = calculate_total_nutrition(recorded_foods)
        
        # 更新精灵属性
        spirit_update = update_spirit_attributes(user.id, total_nutrition)
        
        # 提交所有更改
        db.session.commit()
        
        response_data = {
            "message": "饮食记录添加成功",
            "meal": {
                "date": meal_date.strftime('%Y-%m-%d'),
                "meal_type": meal_type,
                "foods": recorded_foods,
                "total_nutrition": total_nutrition
            },
            "spirit": spirit_update
        }
        
        if skipped_foods:
            response_data["skipped_foods"] = skipped_foods
            response_data["message"] = "部分食物已记录过，已自动跳过"
        
        return jsonify(response_data), 201
        
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
    if total_nutrition.get('calories', 0) > 0:
        nutrition_balance += 1
    if total_nutrition.get('protein', 0) > 0:
        nutrition_balance += 1
    if total_nutrition.get('fat', 0) > 0:
        nutrition_balance += 1
    if total_nutrition.get('calcium', 0) > 0:
        nutrition_balance += 1
    
    # 根据营养均衡程度给予额外经验（最多+5经验）
    exp_gain += min(nutrition_balance, 5)
    
    # 更新精灵经验值
    spirit.spirit_exp += exp_gain
    
    # 检查是否升级
    while spirit.spirit_exp >= spirit.spirit_level * 100:
        spirit.spirit_exp -= spirit.spirit_level * 100
        spirit.spirit_level += 1
    
    # 更新精灵属性
    # 热量影响体重（每100卡路里增加1点）
    weight_gain = total_nutrition.get('calories', 0) / 100
    spirit.weight = min(100, spirit.weight + int(weight_gain))
    
    # 蛋白质影响力量（每10g增加1点）
    strength_gain = total_nutrition.get('protein', 0) / 10
    spirit.strength = min(100, spirit.strength + int(strength_gain))
    
    # 维生素影响智力（每30mg维生素增加1点）
    vitamin_total = (
        total_nutrition.get('vitamin_b1', 0) + 
        total_nutrition.get('vitamin_b2', 0) + 
        total_nutrition.get('vitamin_c', 0)
    )
    iq_gain = vitamin_total / 30
    spirit.iq = min(100, spirit.iq + int(iq_gain))
    
    # 更新时间
    spirit.updated_at = datetime.now()
    
    return {
        "spirit_name": spirit.spirit_name,
        "level": spirit.spirit_level,
        "exp": spirit.spirit_exp,
        "exp_gain": exp_gain,
        "attributes": {
            "weight": spirit.weight,
            "strength": spirit.strength,
            "iq": spirit.iq
        }
    }

def calculate_total_nutrition(foods):
    """计算多个食物的总营养值
    
    Args:
        foods: 食物列表，每个食物包含 nutrition 字段
    
    Returns:
        包含总营养值的字典
    """
    total = {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'calcium': 0,
        'iron': 0,
        'zinc': 0,
        'magnesium': 0,
        'vitamin_a': 0,
        'vitamin_b1': 0,
        'vitamin_b2': 0,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_e': 0
    }
    
    for food in foods:
        nutrition = food.get('nutrition', {})
        for key in total:
            value = nutrition.get(key)
            if value is not None:
                total[key] += value
    
    return total

@nutrition_bp.route('/meals', methods=['GET'])
@jwt_required()
def get_meals():
    """查询指定日期的饮食记录
    
    参数:
    - date: 查询日期，格式为YYYY-MM-DD，可选，默认为今天
    
    返回:
    - 指定日期的所有三餐记录，每餐包含食物信息、总营养成分和实际摄入营养
    """
    current_user_id = get_jwt_identity()

    print(f'current_user_id: {current_user_id}')
    
    # 处理日期参数
    date_str = request.args.get('date')
    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "日期格式错误，应为YYYY-MM-DD"}), 400
    else:
        query_date = datetime.now().date()

    print(f'date_str: {date_str}')
    
    # 查询当天的所有餐点记录
    meals = StudentMeal.query.filter_by(
        user_id=current_user_id,
        date=query_date
    ).all()

    print(f'meals: {meals}')
    
    # 按餐点类型分组
    meals_by_type = {'1': [], '2': [], '3': []}
    nutrition_by_type = {'1': [], '2': [], '3': []}
    
    for meal in meals:
        meal_type = meal.meal_type
        food = meal.food
        
        # 计算该份食物的营养值
        nutrition = {
            'calories': food.calories * meal.amount if food.calories is not None else None,
            'protein': food.protein * meal.amount if food.protein is not None else None,
            'fat': food.fat * meal.amount if food.fat is not None else None,
            'calcium': food.calcium * meal.amount if food.calcium is not None else None,
            'iron': food.iron * meal.amount if food.iron is not None else None,
            'zinc': food.zinc * meal.amount if food.zinc is not None else None,
            'magnesium': food.magnesium * meal.amount if food.magnesium is not None else None,
            'vitamin_a': food.vitamin_a * meal.amount if food.vitamin_a is not None else None,
            'vitamin_b1': food.vitamin_b1 * meal.amount if food.vitamin_b1 is not None else None,
            'vitamin_b2': food.vitamin_b2 * meal.amount if food.vitamin_b2 is not None else None,
            'vitamin_c': food.vitamin_c * meal.amount if food.vitamin_c is not None else None,
            'vitamin_d': food.vitamin_d * meal.amount if food.vitamin_d is not None else None,
            'vitamin_e': food.vitamin_e * meal.amount if food.vitamin_e is not None else None
        }
        
        meals_by_type[meal_type].append({
            'food_name': food.name,
            'amount': meal.amount,
            'nutrition': nutrition
        })
        nutrition_by_type[meal_type].append({'nutrition': nutrition})
    
    # 计算每餐的总营养值和实际摄入营养
    result = {
        'date': query_date.strftime('%Y-%m-%d'),
        'meals': {}
    }

    print(f'meals_by_type: {meals_by_type}')
    
    def calculate_actual_nutrition(total_nutrition):
        """计算实际摄入的营养值（按80%计算）"""
        actual = {}
        for key, value in total_nutrition.items():
            actual[key] = round(value * 0.8, 2) if value is not None else None
        return actual
    
    for meal_type in ['1', '2', '3']:
        if meals_by_type[meal_type]:
            total_nutrition = calculate_total_nutrition(nutrition_by_type[meal_type])
            actual_nutrition = calculate_actual_nutrition(total_nutrition)
            
            result['meals'][meal_type] = {
                'foods': meals_by_type[meal_type],
                'total_nutrition': total_nutrition,
                'actual_nutrition': actual_nutrition  # 新增实际摄入营养字段
            }
    
    # 计算全天总计
    all_nutrition = []
    for meal_type in ['1', '2', '3']:
        all_nutrition.extend(nutrition_by_type[meal_type])
    
    if all_nutrition:
        total_day_nutrition = calculate_total_nutrition(all_nutrition)
        actual_day_nutrition = calculate_actual_nutrition(total_day_nutrition)
        result['daily_total'] = {
            'total_nutrition': total_day_nutrition,
            'actual_nutrition': actual_day_nutrition  # 新增实际摄入营养字段
        }
    
    print(f'result: {result}')
    
    return jsonify(result), 200

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

@nutrition_bp.route('/foods', methods=['GET'])
@jwt_required()
def get_available_foods():
    """查询可选食物列表
    
    参数:
    - keyword: 搜索关键词（可选，按食物名称模糊搜索）
    - page: 页码（可选，默认1）
    - per_page: 每页数量（可选，默认20，最大50）
    
    返回:
    {
        "total": 总记录数,
        "pages": 总页数,
        "current_page": 当前页码,
        "per_page": 每页数量,
        "foods": [
            {
                "id": 食物ID,
                "name": "食物名称",
                "weight": 标准重量(g),
                "calories": 热量(kcal),
                "protein": 蛋白质(g),
                "fat": 脂肪(g),
                "nutrition": {
                    "calcium": 钙(mg),
                    "iron": 铁(mg),
                    "zinc": 锌(mg),
                    "magnesium": 镁(mg),
                    "vitamin_a": 维生素A(mg),
                    "vitamin_b1": 维生素B1(mg),
                    "vitamin_b2": 维生素B2(mg),
                    "vitamin_c": 维生素C(mg),
                    "vitamin_d": 维生素D(mg),
                    "vitamin_e": 维生素E(mg)
                }
            },
            ...
        ]
    }
    """
    # 获取查询参数
    keyword = request.args.get('keyword', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)  # 限制最大每页数量为50
    
    # 构建查询
    query = Food.query
    
    # 如果有关键词，添加模糊搜索条件
    if keyword:
        query = query.filter(Food.name.like(f'%{keyword}%'))
    
    # 获取总记录数和总页数
    total = query.count()
    pages = (total + per_page - 1) // per_page
    
    # 获取当前页的数据
    foods = query.order_by(Food.name).offset((page - 1) * per_page).limit(per_page).all()
    
    # 构建返回数据
    food_list = []
    for food in foods:
        food_list.append({
            "id": food.id,
            "name": food.name,
            "weight": food.weight,
            "calories": food.calories,
            "protein": food.protein,
            "fat": food.fat,
            "nutrition": {
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
        })
    
    return jsonify({
        "total": total,
        "pages": pages,
        "current_page": page,
        "per_page": per_page,
        "foods": food_list
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

@nutrition_bp.route('/preselect', methods=['POST'])
@jwt_required()
def preselect_meal():
    """预选餐接口
    
    请求体格式:
    {
        "date": "2025-03-21",      # 预选日期
        "meal_type": "1",          # 餐点类型：1早餐、2午餐、3晚餐
        "foods": [                 # 食物列表
            {
                "food_name": "米饭",
                "amount": 1         # 可选，份数，默认1
            },
            {
                "food_name": "红烧排骨",
                "amount": 0.5
            }
        ]
    }
    
    返回:
    - 成功: 返回预选的餐食信息
    - 失败: 返回错误信息
    """
    data = request.get_json()
    
    # 从 JWT 中获取用户 ID
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    
    # 验证日期
    try:
        meal_date = datetime.strptime(data.get('date', ''), '%Y-%m-%d').date()
        if meal_date < datetime.now().date():
            return jsonify({"message": "不能为过去的日期预选餐食"}), 400
    except ValueError:
        return jsonify({"message": "日期格式错误，应为YYYY-MM-DD"}), 400
    
    # 验证餐点类型
    meal_type = data.get('meal_type')
    if not meal_type or meal_type not in ['1', '2', '3']:
        return jsonify({"message": "餐点类型错误，应为1、2或3"}), 400
    
    # 验证食物列表
    foods = data.get('foods', [])
    if not foods or not isinstance(foods, list):
        return jsonify({"message": "必须提供至少一种食物"}), 400
    
    try:
        # 删除该日期该餐点的所有预选记录
        PreselectedMeal.query.filter_by(
            user_id=user_id,
            date=meal_date,
            meal_type=meal_type
        ).delete()
        
        recorded_foods = []
        for food_data in foods:
            food_name = food_data.get('food_name')
            if not food_name:
                continue
            
            # 查找食物
            food = Food.query.filter_by(name=food_name).first()
            if not food:
                return jsonify({"message": f"未找到食物：{food_name}"}), 404
            
            amount = food_data.get('amount', 1)
            
            # 创建预选记录
            preselected = PreselectedMeal(
                user_id=user_id,
                food_id=food.id,
                meal_type=meal_type,
                date=meal_date,
                amount=amount
            )
            
            db.session.add(preselected)
            recorded_foods.append({
                'food_name': food.name,
                'amount': amount
            })
        
        db.session.commit()
        
        return jsonify({
            "message": "预选餐食添加成功",
            "meal": {
                "date": meal_date.strftime('%Y-%m-%d'),
                "meal_type": meal_type,
                "foods": recorded_foods
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"预选失败：{str(e)}"}), 500


@nutrition_bp.route('/preselect', methods=['GET'])
@jwt_required()
def get_preselected_meals():
    """获取预选餐列表
    
    参数:
    - date: 查询日期，格式为YYYY-MM-DD，可选，默认为今天
    - meal_type: 餐点类型，1早餐、2午餐、3晚餐，可选
    
    返回:
    - 成功: 返回预选的餐食列表
    - 失败: 返回错误信息
    """
    user_id = get_jwt_identity()
    
    # 处理日期参数
    date_str = request.args.get('date')
    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "日期格式错误，应为YYYY-MM-DD"}), 400
    else:
        query_date = datetime.now().date()

    print(f'query_date: {query_date}')
    
    # 构建查询
    query = PreselectedMeal.query.filter_by(
        user_id=user_id,
        date=query_date
    )
    
    # 处理餐点类型参数
    meal_type = request.args.get('meal_type')
    if meal_type:
        if meal_type not in ['1', '2', '3']:
            return jsonify({"message": "餐点类型错误，应为1、2或3"}), 400
        query = query.filter_by(meal_type=meal_type)
    
    # 获取预选记录
    preselected_meals = query.all()
    
    # 按餐点类型分组
    meals_by_type = {}
    for meal in preselected_meals:
        if meal.meal_type not in meals_by_type:
            meals_by_type[meal.meal_type] = []
        meals_by_type[meal.meal_type].append(meal.to_dict())
    
    return jsonify({
        "date": query_date.strftime('%Y-%m-%d'),
        "meals": meals_by_type
    }), 200
