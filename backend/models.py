from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Replicating Supabase 'public' schema

class User(db.Model):
    __tablename__ = 'users' # Custom auth table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    profile = db.relationship('Profile', backref='user', uselist=False)
    roles = db.relationship('UserRole', backref='user', lazy=True)

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'
    id = db.Column(db.Integer, primary_key=True) # Changed from uuid to int for simplicity in SQLite, or keep string if needed. Keeping simple.
    # Actually, Supabase uses UUIDs. Let's stick to Integer for SQLite simplicity unless string is strictly required by frontend.
    # Frontend might expect string IDs. Let's use string for IDs to be safe with existing frontend types that might expect UUID strings.
    # But for new DB, auto-increment int is easier. I will cast to string in API if needed.
    
    nome = db.Column(db.String(200), nullable=False)
    nif = db.Column(db.String(50), nullable=False, unique=True)
    unidade = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=True)
    nome = db.Column(db.String(200))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Carrinho(db.Model):
    __tablename__ = 'carrinhos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    identificador_fisico = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='DISPONIVEL') # DISPONIVEL, EM_USO, MANUTENCAO
    ip_esp32 = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class UsoCarrinho(db.Model):
    __tablename__ = 'uso_carrinho'
    id = db.Column(db.Integer, primary_key=True)
    carrinho_id = db.Column(db.Integer, db.ForeignKey('carrinhos.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_hora_fim = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='EM_USO')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    carrinho = db.relationship('Carrinho', backref='usos')
    funcionario = db.relationship('Funcionario', backref='usos')

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'user'
