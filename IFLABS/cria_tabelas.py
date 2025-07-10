from src.models import db
from main import app

with app.app_context():
    db.create_all()
    print("Tabelas criadas com sucesso!")
