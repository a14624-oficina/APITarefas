from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models.user import UserModel


def utilizador_publico(user):
    """Devolve apenas os dados que podem ser expostos pela API."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "tipo": user.tipo,
    }


def identidade_e_do_utilizador(user):
    try:
        return int(get_jwt_identity()) == user.id
    except (TypeError, ValueError):
        return False


def e_admin():
    return get_jwt().get("tipo") == "admin"


class User(Resource):
    @jwt_required()
    def get(self, username):
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            return {"mensagem": "Utilizador não encontrado."}, 404
        if not (e_admin() or identidade_e_do_utilizador(user)):
            return {"mensagem": "Não tem permissões para consultar este utilizador."}, 403
        return utilizador_publico(user), 200

    @jwt_required()
    def delete(self, username):
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            return {"mensagem": "Utilizador não encontrado."}, 404
        if not (e_admin() or identidade_e_do_utilizador(user)):
            return {"mensagem": "Não tem permissões para eliminar este utilizador."}, 403
        try:
            user.delete_user()
            return {"mensagem": "Utilizador removido com sucesso."}, 200
        except Exception:
            return {"mensagem": "Não foi possível remover o utilizador."}, 500


class UserRegistar(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument("username", type=str, required=True,
                            help="O nome de utilizador é obrigatório.")
    argumentos.add_argument("email", type=str, required=True,
                            help="O endereço de email é obrigatório.")
    argumentos.add_argument("password", type=str, required=True,
                            help="A palavra-passe é obrigatória.")

    def post(self):
        dados = self.argumentos.parse_args()
        username = (dados["username"] or "").strip()
        email = (dados["email"] or "").strip().lower()
        password = dados["password"] or ""

        if not username or not email or not password:
            return {"mensagem": "Username, email e palavra-passe são obrigatórios."}, 400
        if "@" not in email:
            return {"mensagem": "O endereço de email não é válido."}, 400

        if UserModel.query.filter_by(email=email).first() is not None:
            return {"mensagem": "Já existe um utilizador com este email."}, 400
        if UserModel.query.filter_by(username=username).first() is not None:
            return {"mensagem": "Já existe um utilizador com este username."}, 400

        # O tipo é sempre definido no servidor; o pedido não pode criar admins.
        novo_utilizador = UserModel(
            username=username,
            email=email,
            password=generate_password_hash(password),
            tipo="utilizador",
        )
        try:
            novo_utilizador.save_user()
            return {
                "mensagem": "Utilizador registado com sucesso.",
                "utilizador": utilizador_publico(novo_utilizador),
            }, 201
        except Exception:
            return {"mensagem": "Não foi possível registar o utilizador."}, 500


class UserLogin(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument("email", type=str, required=True,
                            help="O endereço de email é obrigatório.")
    argumentos.add_argument("password", type=str, required=True,
                            help="A palavra-passe é obrigatória.")

    def post(self):
        dados = self.argumentos.parse_args()
        email = (dados["email"] or "").strip().lower()
        password = dados["password"] or ""
        user = UserModel.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password, password):
            return {"mensagem": "O email ou a palavra-passe estão incorretos."}, 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={"tipo": user.tipo},
        )
        return {"token_de_acesso": token}, 200


