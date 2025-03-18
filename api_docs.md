# 学生每周营养摄入系统 API 文档

## 基础信息

- 基础URL: `http://localhost:5000/api`
- 所有请求和响应的数据格式均为 `application/json`
- 除登录接口外，所有接口都需要在请求头中携带token：
  ```
  Authorization: Bearer <your_token>
  ```

## 接口列表

### 1. 用户登录

#### 请求信息
- 接口: `/auth/login`
- 方法: `POST`
- 请求体:
```json
{
    "username": "用户名",
    "password": "密码"
}
```

#### 响应信息
- 成功响应 (200):
```json
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "message": "登录成功"
}
```
- 失败响应 (401):
```json
{
    "message": "用户名或密码错误"
}
```

### 2. 录入饮食记录

#### 请求信息
- 接口: `/nutrition/meals`
- 方法: `POST`
- 请求头: 需要token
- 请求体:
```json
{
    "items": [
        {
            "food_name": "红烧肉",
            "weight": 200,
            "calories": 440,
            "protein": 22,
            "fat": 38,
            "carbohydrate": 6
        },
        {
            "food_name": "青菜",
            "weight": 150,
            "calories": 45,
            "protein": 3,
            "fat": 0.5,
            "carbohydrate": 8
        },
        {
            "food_name": "米饭",
            "weight": 200,
            "calories": 260,
            "protein": 4.8,
            "fat": 0.4,
            "carbohydrate": 58
        }
    ]
}
```

#### 响应信息
- 成功响应 (201):
```json
{
    "message": "记录成功"
}
```
- 失败响应 (400):
```json
{
    "message": "请提供1-3个菜品"
}
```

### 3. 查询每日饮食记录

#### 请求信息
- 接口: `/nutrition/meals/<date>`
- 方法: `GET`
- 请求头: 需要token
- URL参数: 
  - date: 日期，格式为YYYY-MM-DD，例如：`/nutrition/meals/2025-03-14`

#### 响应信息
- 成功响应 (200):
```json
{
    "items": [
        {
            "food_name": "红烧肉",
            "weight": 200,
            "calories": 440,
            "protein": 22,
            "fat": 38,
            "carbohydrate": 6
        },
        {
            "food_name": "青菜",
            "weight": 150,
            "calories": 45,
            "protein": 3,
            "fat": 0.5,
            "carbohydrate": 8
        },
        {
            "food_name": "米饭",
            "weight": 200,
            "calories": 260,
            "protein": 4.8,
            "fat": 0.4,
            "carbohydrate": 58
        }
    ]
}
```
- 失败响应 (404):
```json
{
    "message": "未找到该日期的记录"
}
```
- 失败响应 (400):
```json
{
    "message": "日期格式错误，请使用YYYY-MM-DD格式"
}
```

### 4. 营养摄入统计分析

#### 请求信息
- 接口: `/nutrition/statistics`
- 方法: `GET`
- 请求头: 需要token
- 查询参数:
  - start_date: 开始日期，格式为YYYY-MM-DD
  - end_date: 结束日期，格式为YYYY-MM-DD
  - 示例: `/nutrition/statistics?start_date=2025-03-01&end_date=2025-03-14`

#### 响应信息
- 成功响应 (200):
```json
{
    "total_calories": 5230,
    "total_protein": 186.4,
    "total_fat": 243.6,
    "total_carbohydrate": 504,
    "days_count": 14,
    "daily_avg_calories": 373.57,
    "daily_avg_protein": 13.31,
    "daily_avg_fat": 17.40,
    "daily_avg_carbohydrate": 36.00
}
```
- 失败响应 (400):
```json
{
    "message": "日期格式错误，请使用YYYY-MM-DD格式"
}
```
- 失败响应 (404):
```json
{
    "message": "所选时间段内没有记录"
}
```

## 错误码说明

- 200: 请求成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 未授权（token无效或过期）
- 404: 资源未找到
- 500: 服务器内部错误

## 注意事项

1. token有效期为30分钟，过期需要重新登录
2. 每次记录饮食最多可录入3个菜品
3. 所有重量单位为克(g)
4. 所有营养成分单位：
   - 热量：千卡(kcal)
   - 蛋白质：克(g)
   - 脂肪：克(g)
   - 碳水化合物：克(g)
5. 统计分析接口的日期范围不要太大，建议不超过31天
