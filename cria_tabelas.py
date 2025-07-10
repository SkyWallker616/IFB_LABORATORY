
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.models import db
from main import app

with app.app_context():
    db.create_all()
    print("Tabelas criadas com sucesso!")
