from datetime import timedelta

from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager

from con_sql_alchemy import bd
from resources.user import UserRegistar, UserLogin
from resources.tarefa import Tarefas, Tarefa

app = Flask(__name__)
api = Api(app)
jwt = JWTManager(app)

# Configuração da aplicação e da base de dados
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tarefas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "mude_esta_chave_por_uma_chave_segura"
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)


@jwt.token_in_blocklist_loader
def verifica_blocklist(jwt_header, jwt_payload):
    token_id = jwt_payload["jti"]
    

@jwt.revoked_token_loader
def token_invalido(jwt_header, jwt_payload):
    return {"mensagem": "Token revogado ou inválido."}, 401


# Rotas de utilizadores e autenticação

api.add_resource(UserRegistar, "/registar")
api.add_resource(UserLogin, "/login")


# Rotas de gestão de tarefas
api.add_resource(Tarefas, "/tarefas")
api.add_resource(Tarefa, "/tarefas/<int:tarefa_id>")


if __name__ == "__main__":
    bd.init_app(app)
    with app.app_context():
        bd.create_all()  # Cria as tabelas declaradas nos modelos SQLAlchemy
    app.run(debug=True)
