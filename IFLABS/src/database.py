from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Defina db aqui

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        from src.models import Admin
        from werkzeug.security import generate_password_hash
        # Cria admin apenas se não existir
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', senha=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()