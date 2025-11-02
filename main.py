import os
from dotenv import load_dotenv
import jwt
from time import time
from datetime import datetime
from src.models import db, Professor, Aluno, MembroProjeto, Projeto, MensagemProjeto, ComentarioProjeto, Admin  # Adicione este import no topo do arquivo
from werkzeug.security import check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, RadioField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

# ================================
# CRIA O BANCO A PARTIR DO SCHEMA
# ================================
if not os.path.exists('instance/ifb_projetos.db') and os.path.exists('instance/schema.sql'):
    import subprocess
    subprocess.run(['sqlite3', 'instance/ifb_projetos.db', '.read instance/schema.sql'])

# ======================================
# CONFIGURAÇÃO INICIAL
# ======================================

app = Flask(__name__)


app.config[
    'SECRET_KEY'] = 'sua_chave_secreta_super_segura'  # Troque em produção!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ifb_projetos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['POSTS_PER_PAGE'] = 10
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Configurações de email (substitua com seus dados)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'admin@gmail.com'  # Seu email
app.config['MAIL_PASSWORD'] = '123'  # Sua senha ou app password
app.config['MAIL_DEFAULT_SENDER'] = 'admin@gmail.com'

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Cria pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ======================================
# FORMULÁRIOS
# ======================================


class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegistrationForm(FlaskForm):
    tipo = RadioField('Tipo de Usuário',
                      choices=[('aluno', 'Aluno'), ('professor', 'Professor')],
                      validators=[DataRequired()])
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    matricula = StringField('Matrícula', validators=[DataRequired()])
    curso = StringField('Curso')
    areas_interesse = StringField('Áreas de Interesse')
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    password2 = PasswordField('Repita a Senha',
                              validators=[DataRequired(),
                                          EqualTo('password')])
    submit = SubmitField('Cadastrar')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar redefinição de Senha')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')])
    password2 = PasswordField('Repita a Nova Senha',
                              validators=[DataRequired(),
                                          EqualTo('password')])
    submit = SubmitField('Alterar Senha')


class ProjetoForm(FlaskForm):
    titulo = StringField('Título do Projeto',
                         validators=[DataRequired(),
                                     Length(max=140)])
    area_conhecimento = SelectField('Área do Conhecimento',
                                    choices=[
                                        ('Ciências Agrárias', 'Ciências Agrárias'),
                                        ('Ciências Biológicas', 'Ciências Biológicas'),
                                        ('Ciências da Saúde', 'Ciências da Saúde'),
                                        ('Ciências Exatas e da Terra', 'Ciências Exatas e da Terra'),
                                        ('Engenharias', 'Engenharias'),
                                        ('Ciências Humanas', 'Ciências Humanas'),
                                        ('Ciências Sociais Aplicadas', 'Ciências Sociais Aplicadas'),
                                        ('Linguística, Letras e Artes', 'Linguística, Letras e Artes')
                                    ],
                                    validators=[DataRequired()])
    tipo_vaga = RadioField('Tipo de Bolsa',
                           choices=[('voluntario', 'Voluntário'),
                                    ('bolsista', 'Bolsista')],
                           validators=[DataRequired()])
    descricao = TextAreaField('Descrição do Projeto',
                              validators=[DataRequired()])
    requisitos = TextAreaField('Requisitos', validators=[DataRequired()])
    submit = SubmitField('Publicar Projeto')


class CandidaturaForm(FlaskForm):
    mensagem = TextAreaField('Mensagem',
                             validators=[DataRequired(),
                                         Length(max=500)])
    submit = SubmitField('Enviar Candidatura')


class ComentarioForm(FlaskForm):
    texto = TextAreaField('Comentário',
                          validators=[DataRequired(),
                                      Length(max=500)])
    submit = SubmitField('Enviar Comentário')


class MensagemForm(FlaskForm):
    corpo = TextAreaField('Mensagem',
                          validators=[DataRequired(),
                                      Length(max=1000)])
    submit = SubmitField('Enviar')


class EditarPerfilForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    sobre = TextAreaField('Sobre você',
                          validators=[Optional(), Length(max=500)])
    curso = StringField('Curso', validators=[Optional()])
    areas_interesse = StringField('Áreas de Interesse',
                                  validators=[Optional()])
    foto = FileField('Foto de Perfil', validators=[Optional()])
    submit = SubmitField('Salvar Alterações')


# ======================================
# ROTAS PRINCIPAIS
# ======================================


login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user = Aluno.query.filter_by(matricula=user_id).first()
    if user:
        user.tipo = 'aluno'
        return user
    user = Professor.query.filter_by(matricula=user_id).first()
    if user:
        user.tipo = 'professor'
        return user
    # Buscar admin pelo id (inteiro)
    try:
        admin = Admin.query.filter_by(id=int(user_id)).first()
        if admin:
            admin.tipo = 'admin'
            return admin
    except (ValueError, TypeError):
        pass
    return None


@app.route('/')
def index():
    projetos = Projeto.query.filter_by(status='aberto').order_by(
        Projeto.titulo.asc()).limit(5).all()
    return render_template('index.html', projetos=projetos)

@app.route('/form_login')
def form_login():
    return render_template('auth/login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        senha = request.form.get('senha')
        user = Aluno.query.filter_by(matricula=matricula).first()
        if not user:
            user = Professor.query.filter_by(matricula=matricula).first()
        if user and check_password_hash(user.senha, senha):
            if not user.aprovado:
                flash('Seu cadastro ainda não foi aprovado pelo administrador.', 'warning')
                return render_template('auth/login.html')
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Matrícula ou senha inválidos.', 'danger')
    return render_template('auth/login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.senha, senha):
            login_user(admin)
            flash('Login de administrador realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    professores = Professor.query.all()
    alunos = Aluno.query.all()
    return render_template('admin/dashboard.html', professores=professores, alunos=alunos)

@app.route('/admin/aprovar_usuario/<tipo>/<matricula>', methods=['POST'])
@login_required
def admin_aprovar_usuario(tipo, matricula):
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    if tipo == 'professor':
        user = Professor.query.filter_by(matricula=matricula).first()
    else:
        user = Aluno.query.filter_by(matricula=matricula).first()
    if user:
        user.aprovado = True
        db.session.commit()
        flash('Usuário aprovado com sucesso!', 'success')
    else:
        flash('Usuário não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/excluir_usuario/<tipo>/<matricula>', methods=['POST'])
@login_required
def admin_excluir_usuario(tipo, matricula):
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    if tipo == 'professor':
        user = Professor.query.filter_by(matricula=matricula).first()
    else:
        user = Aluno.query.filter_by(matricula=matricula).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'info')
    else:
        flash('Usuário não encontrado.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/redefinir_senha/<tipo>/<matricula>', methods=['POST'])
@login_required
def admin_redefinir_senha(tipo, matricula):
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    nova_senha = request.form.get('nova_senha')
    if tipo == 'professor':
        user = Professor.query.filter_by(matricula=matricula).first()
    else:
        user = Aluno.query.filter_by(matricula=matricula).first()
    if user and nova_senha:
        user.senha = generate_password_hash(nova_senha)
        db.session.commit()
        flash('Senha redefinida com sucesso!', 'success')
    else:
        flash('Usuário não encontrado ou senha inválida.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/candidaturas')
@login_required
def admin_candidaturas():
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    candidaturas = MembroProjeto.query.filter_by(status='pendente').all()
    return render_template('admin/candidaturas.html', candidaturas=candidaturas)

@app.route('/admin/aprovar_candidatura/<int:id>', methods=['POST'])
@login_required
def admin_aprovar_candidatura(id):
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    membro = MembroProjeto.query.get_or_404(id)
    membro.status = 'aceito'
    db.session.commit()
    flash('Candidatura aprovada!', 'success')
    return redirect(url_for('admin_candidaturas'))

@app.route('/admin/recusar_candidatura/<int:id>', methods=['POST'])
@login_required
def admin_recusar_candidatura(id):
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        abort(403)
    membro = MembroProjeto.query.get_or_404(id)
    membro.status = 'recusado'
    db.session.commit()
    flash('Candidatura recusada!', 'info')
    return redirect(url_for('admin_candidaturas'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Verifica se já existe matrícula ou email
        if form.tipo.data == 'professor':
            existe = Professor.query.filter(
                (Professor.matricula == form.matricula.data) | 
                (Professor.email == form.email.data)
            ).first()
            if existe:
                flash('Matrícula ou email já cadastrados para professor.', 'danger')
                return render_template('auth/register.html', form=form)
            novo = Professor(
                matricula=form.matricula.data,
                nome=form.nome.data,
                email=form.email.data,
                senha=generate_password_hash(form.password.data)
            )
        else:
            existe = Aluno.query.filter(
                (Aluno.matricula == form.matricula.data) | 
                (Aluno.email == form.email.data)
            ).first()
            if existe:
                flash('Matrícula ou email já cadastrados para aluno.', 'danger')
                return render_template('auth/register.html', form=form)
            novo = Aluno(
                matricula=form.matricula.data,
                nome=form.nome.data,
                email=form.email.data,
                senha=generate_password_hash(form.password.data)
            )
        db.session.add(novo)
        db.session.commit()
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Aluno.query.filter_by(email=form.email.data).first() or Professor.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Verifique seu email para instruções de redefinição de senha')
        return redirect(url_for('login'))

    return render_template('auth/reset_password_request.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Tenta verificar o token em Aluno e Professor
    user = None
    for cls in (Aluno, Professor):
        if hasattr(cls, 'verify_reset_password_token'):
            user = cls.verify_reset_password_token(token)
            if user:
                break
    if not user:
        flash('Token inválido ou expirado')
        return redirect(url_for('reset_password_request') )

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Sua senha foi alterada com sucesso!')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/projetos/listar')
def listar_projetos():
    page = request.args.get('page', 1, type=int)
    area = request.args.get('area', None)
    query = request.args.get('q', None)

    projetos_query = Projeto.query.filter_by(status='aberto')

    if area:
        projetos_query = projetos_query.filter_by(area_conhecimento=area)

    if query:
        projetos_query = projetos_query.filter(
            Projeto.titulo.ilike(f'%{query}%')
            | Projeto.descricao.ilike(f'%{query}%')
            | Projeto.requisitos.ilike(f'%{query}%'))

    projetos = projetos_query.order_by(Projeto.data_criacao.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    areas = db.session.query(Projeto.area_conhecimento).distinct().all()
    areas = [area[0] for area in areas if area[0]]

    return render_template('projetos/listar_projetos.html',
                           projetos=projetos,
                           areas=areas,
                           area_selecionada=area)


@app.route('/projetos/<int:id>', methods=['GET', 'POST'])
def detalhes_projeto(id):
    projeto = Projeto.query.get_or_404(id)

    if request.method == 'POST':
        if 'texto' in request.form:  # Comentário
            if current_user.is_authenticated:
                pass  # Comentários não implementados
            else:
                flash('Faça login para comentar', 'warning')

    candidatura_atual = None
    if current_user.is_authenticated and current_user.tipo == 'aluno':
        candidatura_atual = MembroProjeto.query.filter_by(
            matricula=current_user.matricula, id_projeto=projeto.id).first()

    membros_projeto = MembroProjeto.query.filter_by(id_projeto=id).all()
    # Buscar alunos (todos os membros: aceitos e pendentes) para exibir nomes no template
    alunos_matriculas = [m.matricula for m in membros_projeto]
    from src.models import Aluno
    alunos = Aluno.query.filter(Aluno.matricula.in_(alunos_matriculas)).all() if alunos_matriculas else []
    alunos_por_matricula = {a.matricula: a for a in alunos}

    mensagens_recebidas = []
    if current_user.is_authenticated:
        from src.models import MensagemProjeto
        mensagens_recebidas = MensagemProjeto.query.filter_by(id_projeto=id, destinatario_matricula=current_user.matricula).order_by(MensagemProjeto.data_envio.desc()).all()

    from src.models import ComentarioProjeto
    comentarios = ComentarioProjeto.query.filter_by(id_projeto=id, resposta_id=None).order_by(ComentarioProjeto.data_envio.desc()).all()
    # Buscar nomes dos autores para exibir no template
    autores_matriculas = set([c.autor_matricula for c in comentarios])
    for c in comentarios:
        autores_matriculas.update([r.autor_matricula for r in c.respostas])
    from src.models import Aluno, Professor
    nomes_autores = {}
    for matricula in autores_matriculas:
        aluno = Aluno.query.filter_by(matricula=matricula).first()
        if aluno:
            nomes_autores[matricula] = aluno.nome
        else:
            prof = Professor.query.filter_by(matricula=matricula).first()
            if prof:
                nomes_autores[matricula] = prof.nome
            else:
                nomes_autores[matricula] = matricula
    # Permissões: professor autor ou aluno aceito
    is_professor_autor = hasattr(current_user, 'tipo') and current_user.tipo == 'professor' and current_user.matricula == projeto.user_id
    is_aluno_membro = False
    if hasattr(current_user, 'tipo') and current_user.tipo == 'aluno':
        membro_atual = MembroProjeto.query.filter_by(id_projeto=id, matricula=current_user.matricula, status='aceito').first()
        is_aluno_membro = membro_atual is not None

    return render_template('projetos/detalhes.html',
                           projeto=projeto,
                           candidatura_atual=candidatura_atual,
                           membros_projeto=membros_projeto,
                           mensagens_recebidas=mensagens_recebidas,
                           alunos=alunos,
                           alunos_por_matricula=alunos_por_matricula,
                           comentarios=comentarios,
                           nomes_autores=nomes_autores,
                           is_professor_autor=is_professor_autor,
                           is_aluno_membro=is_aluno_membro)


@app.route('/projetos/criar', methods=['GET', 'POST'])
@login_required
def criar_projeto():
    if current_user.tipo != 'professor':
        flash('Apenas professores podem criar projetos', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        requisitos = request.form.get('requisitos', '').strip()
        tipo_vaga = request.form.get('tipo_vaga', '').strip()
        area_conhecimento = request.form.get('area_conhecimento', '').strip()
        if titulo and descricao and requisitos and tipo_vaga and area_conhecimento:
            projeto = Projeto(
                titulo=titulo,
                descricao=descricao,
                requisitos=requisitos,
                tipo_vaga=tipo_vaga,
                area_conhecimento=area_conhecimento,
                user_id=current_user.matricula,
                status='aberto'
            )
            db.session.add(projeto)
            db.session.commit()
            flash('Projeto criado com sucesso!', 'success')
            return redirect(url_for('perfil'))
        else:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('criar_projeto'))

    return render_template('projetos/criar.html')


@app.route('/projetos/<int:id>/candidatar', methods=['POST'])
@login_required
def candidatar_projeto(id):
    if current_user.tipo != 'aluno':
        abort(403)
    projeto = Projeto.query.get_or_404(id)
    membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=current_user.matricula).first()
    if membro:
        flash('Você já se candidatou a este projeto.', 'info')
    else:
        membro = MembroProjeto(id_projeto=id, matricula=current_user.matricula, status='pendente')
        db.session.add(membro)
        db.session.commit()
        flash('Candidatura enviada com sucesso!', 'success')
    return redirect(url_for('detalhes_projeto', id=id))

@app.route('/projetos/<int:id>/cancelar_candidatura', methods=['POST'])
@login_required
def cancelar_candidatura(id):
    if current_user.tipo != 'aluno':
        abort(403)
    membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=current_user.matricula).first()
    if membro and membro.status == 'pendente':
        db.session.delete(membro)
        db.session.commit()
        flash('Candidatura cancelada.', 'info')
    else:
        flash('Não foi possível cancelar a candidatura.', 'danger')
    return redirect(url_for('detalhes_projeto', id=id))

@app.route('/projetos/<int:id>/aceitar_aluno/<matricula>', methods=['POST'])
@login_required
def aceitar_aluno(id, matricula):
    projeto = Projeto.query.get_or_404(id)
    if current_user.tipo != 'professor':
        abort(403)
    membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=matricula).first()
    if membro and membro.status == 'pendente':
        membro.status = 'aceito'
        db.session.commit()
        flash('Aluno aceito no projeto!', 'success')
    else:
        flash('Ocorreu um erro.', 'danger')
    return redirect(url_for('detalhes_projeto', id=id))

@app.route('/projetos/<int:id>/recusar_aluno/<matricula>', methods=['POST'])
@login_required
def recusar_aluno(id, matricula):
    projeto = Projeto.query.get_or_404(id)
    if current_user.tipo != 'professor':
        abort(403)
    membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=matricula).first()
    if membro and membro.status == 'pendente':
        membro.status = 'recusado'
        db.session.commit()
        flash('Aluno recusado.', 'info')
    else:
        flash('Ocorreu um erro.', 'danger')
    return redirect(url_for('detalhes_projeto', id=id))


@app.route('/perfil')
@login_required
def perfil():
    matricula = request.args.get('matricula')
    user = None
    if matricula:
        user = Aluno.query.options(joinedload(getattr(Aluno, 'membros_projeto'))).filter_by(matricula=matricula).first()
        if not user:
            user = Professor.query.options(joinedload(getattr(Professor, 'projetos'))).filter_by(matricula=matricula).first()
    if not user:
        if current_user.is_authenticated and hasattr(current_user, 'membros_projeto'):
            user = Aluno.query.options(joinedload(getattr(Aluno, 'membros_projeto'))).filter_by(matricula=current_user.matricula).first()
        elif current_user.is_authenticated and hasattr(current_user, 'projetos'):
            user = Professor.query.options(joinedload(getattr(Professor, 'projetos'))).filter_by(matricula=current_user.matricula).first()
        else:
            user = current_user
    # Ajustes de exibição para Admin: nome e sobre fixos
    if hasattr(user, 'tipo') and user.tipo == 'admin':
        setattr(user, 'nome', 'ADMIN')
        setattr(user, 'sobre', 'Perfil Administrador')
    # Verificar se o perfil pertence ao usuário logado
    is_owner = user.matricula == current_user.matricula
    return render_template('usuarios/perfil.html', user=user, is_owner=is_owner)


@app.route('/perfil/editar', methods=['POST'])
@login_required
def editar_perfil():
    # Impedir edição para administrador
    if hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
        flash('Administradores não podem editar o perfil.', 'warning')
        return redirect(url_for('perfil'))
    sobre = request.form.get('sobre', '').strip()
    if sobre:
        current_user.sobre = sobre
        db.session.commit()
        flash('Campo atualizado com sucesso!', 'success')
    else:
        flash('Campo obrigatório.', 'danger')
    return redirect(url_for('perfil'))


# ======================================
# ROTAS AJAX
# ======================================


@app.route('/perfil/editar_nome', methods=['POST'])
@login_required
def editar_nome():
    # Impedir edição para administrador
    if hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
        flash('Administradores não podem editar o nome.', 'warning')
        return redirect(url_for('perfil'))
    novo_nome = request.form.get('nome', '').strip()
    if not novo_nome:
        flash('Nome obregatório.', 'danger')
        return redirect(url_for('perfil'))
    current_user.nome = novo_nome
    db.session.commit()
    flash('Nome atualizado com sucesso!', 'success')
    return redirect(url_for('perfil'))


@app.route('/perfil/alterar_foto', methods=['POST'])
@login_required
def alterar_foto():
    # Impedir alteração de foto para administrador
    if hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
        flash('Administradores não podem alterar a foto do perfil.', 'warning')
        return redirect(url_for('perfil'))
    if 'foto' not in request.files:
        flash('Arquivo não enviado.', 'danger')
        return redirect(url_for('perfil'))

    file = request.files['foto']
    if file.filename == '':
        flash('Arquivo inválido.', 'danger')
        return redirect(url_for('perfil'))

    if not allowed_file(file.filename):
        flash('Extensão não permitida.', 'danger')
        return redirect(url_for('perfil'))

    filename = secure_filename(f"{current_user.matricula}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    current_user.foto_perfil = filename
    db.session.commit()

    flash('Foto de perfil atualizada com sucesso!', 'success')
    return redirect(url_for('perfil'))


@app.route('/projetos/criar_ajax', methods=['POST'])
@login_required
def criar_projeto_ajax():
    if current_user.tipo != 'professor':
        return {
            'success': False,
            'error': 'Apenas professores podem criar projetos.'
        }, 403

    data = request.get_json()
    titulo = data.get('titulo', '').strip()
    descricao = data.get('descricao', '').strip()
    requisitos = data.get('requisitos', '').strip()
    tipo_vaga = data.get('tipo_vaga', '').strip()
    area_conhecimento = data.get('area_conhecimento', '').strip()

    if not (titulo and descricao and requisitos and tipo_vaga
            and area_conhecimento):
        return {
            'success': False,
            'error': 'Todos os campos são obrigatórios.'
        }, 400

    projeto = Projeto(titulo=titulo,
                      descricao=descricao,
                      requisitos=requisitos,
                      tipo_vaga=tipo_vaga,
                      area_conhecimento=area_conhecimento,
                      user_id=current_user.id)
    db.session.add(projeto)
    db.session.commit()
    return {
        'success': True,
        'projeto_id': projeto.id,
        'titulo': projeto.titulo
    }


@app.route('/perfil/atualizar_areas', methods=['POST'])
@login_required
def atualizar_areas():
    data = request.get_json()
    areas = data.get('areas', [])
    if not isinstance(areas, list):
        return {'success': False, 'error': 'Formato inválido para áreas.'}, 400

    current_user.areas_interesse = ','.join(areas)
    db.session.commit()
    return {'success': True}


@app.route('/projetos/<int:id>/alterar_status', methods=['POST'])
@login_required
def alterar_status_projeto(id):
    projeto = Projeto.query.get_or_404(id)
    if current_user.tipo != 'professor' or current_user.matricula != projeto.user_id:
        abort(403)
    novo_status = request.form.get('status')
    if novo_status in ['aberto', 'em processo', 'encerrado', 'finalizado']:
        projeto.status = novo_status
        db.session.commit()
        flash('Status do projeto atualizado!', 'success')
    else:
        flash('Status inválido.', 'danger')
    return redirect(url_for('detalhes_projeto', id=id))

@app.route('/projetos/<int:id>/remover_aluno/<matricula>', methods=['POST'])
@login_required
def remover_aluno(id, matricula):
    projeto = Projeto.query.get_or_404(id)
    if current_user.tipo != 'professor' or current_user.matricula != projeto.user_id:
        abort(403)
    membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=matricula, status='aceito').first()
    if membro:
        db.session.delete(membro)
        db.session.commit()
        flash('Aluno removido do projeto.', 'info')
    else:
        flash('Não foi possível remover o aluno.', 'danger')
    return redirect(url_for('detalhes_projeto', id=id))


@app.route('/projetos/<int:id>/mensagens')
@login_required
def mensagens_projeto(id):
    projeto = Projeto.query.get_or_404(id)
    # Somente professor autor ou aluno aceito pode ver mensagens do projeto
    is_professor_autor = hasattr(current_user, 'tipo') and current_user.tipo == 'professor' and current_user.matricula == projeto.user_id
    is_aluno_membro = False
    if hasattr(current_user, 'tipo') and current_user.tipo == 'aluno':
        membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=current_user.matricula, status='aceito').first()
        is_aluno_membro = membro is not None
    if not (is_professor_autor or is_aluno_membro):
        abort(403)

    msgs_recebidas = MensagemProjeto.query.filter_by(id_projeto=id, destinatario_matricula=current_user.matricula).order_by(MensagemProjeto.data_envio.desc()).all()
    # Marcar como lidas
    for msg in msgs_recebidas:
        msg.lida = True
    # Mensagens enviadas pelo usuário atual neste projeto
    msgs_enviadas = MensagemProjeto.query.filter_by(id_projeto=id, remetente_matricula=current_user.matricula).order_by(MensagemProjeto.data_envio.desc()).all()
    db.session.commit()
    # Construir mapa de nomes por matrícula
    from src.models import Aluno, Professor
    matriculas = set([m.remetente_matricula for m in msgs_recebidas] + [m.destinatario_matricula for m in msgs_enviadas])
    alunos = Aluno.query.filter(Aluno.matricula.in_(matriculas)).all() if matriculas else []
    profs = Professor.query.filter(Professor.matricula.in_(matriculas)).all() if matriculas else []
    nomes_por_matricula = {a.matricula: a.nome for a in alunos}
    for p in profs:
        nomes_por_matricula[p.matricula] = p.nome
    return render_template('projetos/mensagens.html', mensagens=msgs_recebidas, mensagens_enviadas=msgs_enviadas, nomes_por_matricula=nomes_por_matricula, projeto_id=id)

@app.route('/projetos/<int:id>/mensagens/notificacoes')
@login_required
def notificacoes_mensagens(id):
    count = MensagemProjeto.query.filter_by(id_projeto=id, destinatario_matricula=current_user.matricula, lida=False).count()
    return {'nao_lidas': count}


# ======================================
# FUNÇÕES AUXILIARES
# ======================================


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message('Redefinição de Senha - IFB Projetos', recipients=[user.email])
    msg.body = f'''Para redefinir sua senha, clique no link abaixo:

{url_for('reset_password', token=token, _external=True)}

Se você não solicitou a redefinição de senha, ignore esta mensagem.
O link expirará em 10 minutos.
'''
    mail.send(msg)


# ======================================
# INICIALIZAÇÃO
# ======================================


def create_database():
    with app.app_context():
        db.create_all()
        # Criação do usuário admin 
        from src.models import Admin
        from werkzeug.security import generate_password_hash
        if not Admin.query.filter_by(username='admin').first():
            load_dotenv()
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin = Admin(username=admin_username, senha=generate_password_hash(admin_password))
            db.session.add(admin)
            db.session.commit()
            print("Administrador criado com sucesso!")
        else:
            print("Administrador já existe.")
        print("Banco de dados criado com sucesso!")


@app.route('/projetos/<int:id>/comentar', methods=['POST'])
@login_required
def comentar_projeto(id):
    texto = request.form.get('comentario')
    resposta_id = request.form.get('resposta_id')
    if not texto:
        flash('Comentário vazio.', 'warning')
        return redirect(url_for('detalhes_projeto', id=id))
    from src.models import ComentarioProjeto

    comentario = ComentarioProjeto()
    comentario.id_projeto = id
    comentario.autor_matricula = current_user.matricula
    comentario.texto = texto
    comentario.resposta_id = resposta_id if resposta_id else None
    db.session.add(comentario)
    db.session.commit()
    flash('Comentário enviado com sucesso!', 'success')
    return redirect(url_for('detalhes_projeto', id=id))

@app.route('/projetos/<int:id>/enviar_mensagem', methods=['POST'])
@login_required
def enviar_mensagem_projeto(id):
    destinatario = request.form.get('destinatario')
    conteudo = request.form.get('mensagem')
    resposta_a_id = request.form.get('resposta_a')
    if not destinatario or not conteudo:
        flash('Preencha todos os campos para enviar a mensagem.', 'danger')
        return redirect(url_for('detalhes_projeto', id=id))

    # Restringir quem pode enviar mensagem: professor autor do projeto ou aluno aceito no projeto
    projeto = Projeto.query.get_or_404(id)
    is_professor_autor = hasattr(current_user, 'tipo') and current_user.tipo == 'professor' and current_user.matricula == projeto.user_id
    is_aluno_membro = False
    if hasattr(current_user, 'tipo') and current_user.tipo == 'aluno':
        membro = MembroProjeto.query.filter_by(id_projeto=id, matricula=current_user.matricula, status='aceito').first()
        is_aluno_membro = membro is not None
    if not (is_professor_autor or is_aluno_membro):
        abort(403)

    nova_msg = MensagemProjeto(
        id_projeto=id,
        remetente_matricula=current_user.matricula,
        destinatario_matricula=destinatario,
        conteudo=conteudo
    )
    # Validação extra: o destinatário precisa ser o professor autor OU um aluno aceito do projeto
    destinatario_valido = False
    if destinatario == projeto.user_id:
        destinatario_valido = True
    else:
        membro_dest = MembroProjeto.query.filter_by(id_projeto=id, matricula=destinatario, status='aceito').first()
        destinatario_valido = membro_dest is not None
    if not destinatario_valido:
        abort(403)
    db.session.add(nova_msg)
    # Se for resposta a uma mensagem recebida, marcar a original como lida
    if resposta_a_id:
        try:
            original = MensagemProjeto.query.filter_by(id=int(resposta_a_id), id_projeto=id, destinatario_matricula=current_user.matricula).first()
            if original:
                original.lida = True
        except (ValueError, TypeError):
            pass
    db.session.commit()
    flash('Mensagem enviada com sucesso!', 'success')
    return redirect(url_for('detalhes_projeto', id=id))

if __name__ == '__main__':
    create_database()
    app.run(host='0.0.0.0', port=8080, debug=True)
