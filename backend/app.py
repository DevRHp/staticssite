import os
import time
import threading
import requests
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Funcionario, Profile, Carrinho, UsoCarrinho, UserRole

app = Flask(__name__)

# --- Keep Alive System ---
def keep_alive_pinger():
    """Pings the server every 14 minutes to prevent sleep."""
    url = "http://127.0.0.1:8000/keep_alive" # Default Gunicorn port
    
    # Better approach for Render: Use the public URL if available
    public_url = os.environ.get('RENDER_EXTERNAL_URL')
    target_url = public_url + "/keep_alive" if public_url else url

    print(f" * Keep-Alive Pinger Initialized. Target: {target_url}")
    
    while True:
        time.sleep(14 * 60) # 14 minutes
        try:
            print(" * Sending Keep-Alive Ping...")
            requests.get(target_url)
        except Exception as e:
            print(f" * Keep-Alive Ping Failed: {e}")

# Start Pinger in Background Thread
# Only start if not in debug/reloader mode to avoid duplicates
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    t = threading.Thread(target=keep_alive_pinger, daemon=True)
    t.start()

@app.route('/keep_alive')
def keep_alive():
    return jsonify({"status": "alive", "timestamp": time.time()})

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "Backend do Marcelinho funcionando!"})


# Configure for local development
app.config['SECRET_KEY'] = 'dev_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS to allow requests from Vite (http://localhost:8080 or similar)
CORS(app, supports_credentials=True)

db.init_app(app)

with app.app_context():
    db.create_all()
    # Seed Admin if not exists
    # Ensure Admin exists or update password if needed
    admin = User.query.filter_by(email='admin@123').first()
    if not admin:
        admin = User(email='admin@123', password=generate_password_hash('Marionete12'))
        db.session.add(admin)
        db.session.commit()
    else:
        # Optional: Reset password on restart to ensure it matches hardcoded value
        admin.password = generate_password_hash('Marionete12')
        db.session.commit()
        
    # Ensure role
    if not UserRole.query.filter_by(user_id=admin.id, role='admin').first():
        role = UserRole(user_id=admin.id, role='admin')
        db.session.add(role)
        db.session.commit()
        
    print("Admin seeded/updated: admin@123 / Marionete12")

# --- Auth Routes ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email
            }
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
        
    hashed = generate_password_hash(password)
    user = User(email=email, password=hashed)
    db.session.add(user)
    db.session.commit()
    
    # Create Profile (default)
    profile = Profile(user_id=user.id, email=email)
    db.session.add(profile)
    # Default Role (user)
    role = UserRole(user_id=user.id, role='user')
    db.session.add(role)
    db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({'success': True})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'user': None})
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'user': None})
        
    is_admin = bool(UserRole.query.filter_by(user_id=user.id, role='admin').first())
    
    return jsonify({
        'user': {'id': user.id, 'email': user.email},
        'session': {'user': {'id': user.id, 'email': user.email}}, # Mock Supabase session structure slightly
        'isAdmin': is_admin
    })

# --- Application Routes ---

@app.route('/api/carrinhos', methods=['GET'])
def get_carrinhos():
    carrinhos = Carrinho.query.order_by(Carrinho.nome).all()
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'identificador_fisico': c.identificador_fisico,
        'status': c.status,
        'ip_esp32': c.ip_esp32
    } for c in carrinhos])

@app.route('/api/carrinhos', methods=['POST'])
def create_carrinho():
    data = request.json
    new_c = Carrinho(
        nome=data.get('nome'),
        identificador_fisico=data.get('identificador_fisico'),
        ip_esp32=data.get('ip_esp32'),
        status='DISPONIVEL'
    )
    db.session.add(new_c)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/uso_carrinho/ativos', methods=['GET'])
def get_usos_ativos():
    # Join with Funcionario and Carrinho
    # Expected format mirrors Supabase: *, funcionario:funcionarios(*), carrinho:carrinhos(*)
    usos = UsoCarrinho.query.filter_by(status='EM_USO').all()
    results = []
    
    for u in usos:
        results.append({
            'id': u.id,
            'carrinho_id': u.carrinho_id,
            'funcionario_id': u.funcionario_id,
            'status': u.status,
            'data_hora_inicio': u.data_hora_inicio.isoformat(),
            'funcionario': {
                'id': u.funcionario.id,
                'nome': u.funcionario.nome,
                'unidade': u.funcionario.unidade
            },
            'carrinho': {
                'id': u.carrinho.id,
                'nome': u.carrinho.nome,
                'identificador_fisico': u.carrinho.identificador_fisico
            }
        })
    return jsonify(results)

@app.route('/api/funcionarios/validate', methods=['POST'])
def validate_nif():
    data = request.json
    nif = data.get('nif')
    
    func = Funcionario.query.filter_by(nif=nif, ativo=True).first()
    if not func:
        return jsonify({'error': 'Funcionario not found'}), 404
        
    return jsonify({
        'id': func.id,
        'nome': func.nome,
        'unidade': func.unidade,
        'nif': func.nif
    })
    
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    carrinho_id = data.get('carrinho_id')
    funcionario_id = data.get('funcionario_id')
    
    c = Carrinho.query.get(carrinho_id)
    if not c or c.status != 'DISPONIVEL':
        return jsonify({'error': 'Carrinho indisponível'}), 400
        
    # Update Cart
    c.status = 'EM_USO'
    
    # Create Usage
    usage = UsoCarrinho(
        carrinho_id=carrinho_id,
        funcionario_id=funcionario_id,
        status='EM_USO',
        data_hora_inicio=datetime.utcnow()
    )
    db.session.add(usage)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/return', methods=['POST'])
def return_cart():
    data = request.json
    carrinho_id = data.get('carrinho_id')
    funcionario_id = data.get('funcionario_id')

    c = Carrinho.query.get(carrinho_id)
    if not c: return jsonify({'error': 'Not found'}), 404
    
    usage = UsoCarrinho.query.filter_by(
        carrinho_id=carrinho_id, 
        funcionario_id=funcionario_id, 
        status='EM_USO'
    ).first()
    
    if not usage:
         return jsonify({'error': 'Uso não encontrado'}), 404
         
    c.status = 'DISPONIVEL'
    usage.status = 'FINALIZADO'
    usage.data_hora_fim = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'success': True})

# --- ESP32 Routes ---

@app.route('/api/esp32/get_status', methods=['GET'])
def esp32_get_status():
    # ESP32 requests: /api/esp32/get_status?nome=LIM01
    nome_carrinho = request.args.get('nome')
    print(f" * ESP32 Check: {nome_carrinho}")
    
    if not nome_carrinho:
        return jsonify({'error': 'Nome nao fornecido'}), 400
        
    carrinho = Carrinho.query.filter_by(nome=nome_carrinho).first()
    
    if carrinho:
        # Returns simple string for easy parsing on ESP32
        # Format: "STATUS:EM_USO" or "STATUS:DISPONIVEL"
        return f"STATUS:{carrinho.status}", 200
    else:
        return "ERROR:Carrinho nao encontrado", 404

# --- Admin Routes ---

@app.route('/api/admin/carrinhos/<int:id>', methods=['PUT'])
def update_carrinho(id):
    c = Carrinho.query.get(id)
    if not c: return jsonify({'error': 'Not found'}), 404
    data = request.json
    c.nome = data.get('nome', c.nome)
    c.identificador_fisico = data.get('identificador_fisico', c.identificador_fisico)
    c.ip_esp32 = data.get('ip_esp32', c.ip_esp32)
    c.status = data.get('status', c.status)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/carrinhos/<int:id>', methods=['DELETE'])
def delete_carrinho(id):
    c = Carrinho.query.get(id)
    if not c: return jsonify({'error': 'Not found'}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/funcionarios', methods=['GET'])
def get_funcionarios():
    funcs = Funcionario.query.order_by(Funcionario.nome).all()
    return jsonify([{
        'id': f.id,
        'nome': f.nome,
        'nif': f.nif,
        'unidade': f.unidade,
        'ativo': f.ativo
    } for f in funcs])

@app.route('/api/admin/funcionarios', methods=['POST'])
def create_funcionario():
    data = request.json
    f = Funcionario(
        nome=data.get('nome'),
        nif=data.get('nif'),
        unidade=data.get('unidade'),
        ativo=data.get('ativo', True)
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/funcionarios/<int:id>', methods=['PUT'])
def update_funcionario(id):
    f = Funcionario.query.get(id)
    if not f: return jsonify({'error': 'Not found'}), 404
    data = request.json
    f.nome = data.get('nome', f.nome)
    f.nif = data.get('nif', f.nif)
    f.unidade = data.get('unidade', f.unidade)
    f.ativo = data.get('ativo', f.ativo)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/funcionarios/<int:id>', methods=['DELETE'])
def delete_funcionario(id):
    f = Funcionario.query.get(id)
    if not f: return jsonify({'error': 'Not found'}), 404
    db.session.delete(f)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/historico', methods=['GET'])
def get_historico():
    usos = UsoCarrinho.query.order_by(UsoCarrinho.data_hora_inicio.desc()).limit(100).all()
    results = []
    for u in usos:
        results.append({
            'id': u.id,
            'carrinho_id': u.carrinho_id,
            'funcionario_id': u.funcionario_id,
            'status': u.status,
            'data_hora_inicio': u.data_hora_inicio.isoformat(),
            'data_hora_fim': u.data_hora_fim.isoformat() if u.data_hora_fim else None,
            'funcionario': {
                'id': u.funcionario.id,
                'nome': u.funcionario.nome,
                'nif': u.funcionario.nif
            },
            'carrinho': {
                'id': u.carrinho.id,
                'nome': u.carrinho.nome
            }
        })
    return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True, port=5000)
