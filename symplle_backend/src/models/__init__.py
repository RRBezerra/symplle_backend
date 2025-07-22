from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Primeiro, crie apenas o objeto db
db = SQLAlchemy()
migrate = None  # Inicialize como None

# Função para inicializar o migrate depois que o app for criado
def init_migrate(app):
    global migrate
    migrate = Migrate(app, db)
