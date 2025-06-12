import os
import sys
# DON'T CHANGE THIS !!! / NÃO ALTERE ISSO !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.sms import db
from src.routes.sms import sms_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'sms_service_secret_key_2025'

# Enable CORS for all routes / Habilita CORS para todas as rotas
CORS(app, origins="*")

# Register SMS blueprint / Registra blueprint SMS
app.register_blueprint(sms_bp, url_prefix='/api')

# Database configuration / Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files and handle SPA routing
    Serve arquivos estáticos e gerencia roteamento SPA
    """
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Run the application / Executa a aplicação
    app.run(host='0.0.0.0', port=5000, debug=True)

