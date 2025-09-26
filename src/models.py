from flask_login import UserMixin
from src.database import db  # Use o db do database.py, não crie um novo aqui


class Projeto(db.Model):
    __tablename__ = 'projeto'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='aberto')
    descricao = db.Column(db.String(2000), nullable=False)
    requisitos = db.Column(db.String(1000), nullable=True)
    tipo_vaga = db.Column(db.String(50), nullable=True)
    area_conhecimento = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.String(20), db.ForeignKey('professor.matricula'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.now())
    # Relacionamento para acessar membros
    membros = db.relationship('MembroProjeto', backref='projeto', lazy=True)

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)

    def get_id(self):
        return str(self.id)

class Professor(UserMixin, db.Model):
    __tablename__ = 'professor'
    matricula = db.Column(db.String(20), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    sobre = db.Column(db.Text, nullable=True)
    foto_perfil = db.Column(db.String(255), nullable=True)  # Caminho da foto
    aprovado = db.Column(db.Boolean, default=False)  # Novo campo para aprovação
    # outros campos...
    projetos = db.relationship('Projeto', backref='autor', lazy=True)

    def get_id(self):
        return self.matricula

class Aluno(UserMixin, db.Model):
    __tablename__ = 'aluno'
    matricula = db.Column(db.String(20), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    sobre = db.Column(db.Text, nullable=True)
    foto_perfil = db.Column(db.String(255), nullable=True)  # Caminho da foto
    aprovado = db.Column(db.Boolean, default=False)  # Novo campo para aprovação
    # outros campos...
    membros_projeto = db.relationship('MembroProjeto', backref='aluno', lazy=True)

    def get_id(self):
        return self.matricula

class MembroProjeto(db.Model):
    __tablename__ = 'membro_projeto'
    id = db.Column(db.Integer, primary_key=True)
    id_projeto = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    matricula = db.Column(db.String(20), db.ForeignKey('aluno.matricula'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, aceito, recusado

class MensagemProjeto(db.Model):
    __tablename__ = 'mensagem_projeto'
    id = db.Column(db.Integer, primary_key=True)
    id_projeto = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    remetente_matricula = db.Column(db.String(20), nullable=False)
    destinatario_matricula = db.Column(db.String(20), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=db.func.now())
    lida = db.Column(db.Boolean, default=False)

class ComentarioProjeto(db.Model):
    __tablename__ = 'comentario_projeto'
    id = db.Column(db.Integer, primary_key=True)
    id_projeto = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    autor_matricula = db.Column(db.String(20), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=db.func.now())
    resposta_id = db.Column(db.Integer, db.ForeignKey('comentario_projeto.id'), nullable=True)
    respostas = db.relationship('ComentarioProjeto', backref=db.backref('comentario_pai', remote_side=[id]), lazy=True)