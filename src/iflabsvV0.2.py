from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()

class Projeto(db.Model):
    __tablename__ = 'projeto'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(2000), nullable=False)


class Professor(UserMixin, db.Model):
    __tablename__ = 'professor'
    matricula = db.Column(db.String(20), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    # outros campos...

    def get_id(self):
        return self.matricula

class Aluno(UserMixin, db.Model):
    __tablename__ = 'aluno'
    matricula = db.Column(db.String(20), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    # outros campos...

    def get_id(self):
        return self.matricula

class MembroProjeto(db.Model):
    __tablename__ = 'membro_projeto'
    id = db.Column(db.Integer, primary_key=True)
    id_projeto = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    matricula = db.Column(db.String(20), nullable=False)  # Pode ser aluno ou professor