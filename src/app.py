from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from src.models.models import db
from src.routes.auth import auth_bp
from src.routes.nutrition import nutrition_bp
from src.routes.spirit import spirit_bp

def create_app():
    app = Flask(__name__)
    
    # 配置
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'nutrition.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(db_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # 在生产环境中应使用环境变量
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
    
    # 初始化扩展
    db.init_app(app)
    jwt = JWTManager(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(nutrition_bp, url_prefix='/api/nutrition')
    app.register_blueprint(spirit_bp, url_prefix='/api/spirit')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
