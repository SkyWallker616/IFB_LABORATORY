import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from main import app
from src.models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    # Criação do admin diretamente aqui
    admin_existente = Admin.query.filter_by(username='admin').first()
    if not admin_existente:
        admin = Admin(username='admin', senha=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin criado com sucesso!")
    else:
        print("Admin já existe.")
    print("Tabelas criadas com sucesso!")
