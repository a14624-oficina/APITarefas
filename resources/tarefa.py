from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from con_sql_alchemy import bd
from models.tarefas import TarefaModel


ESTADOS_VALIDOS = {"Pendente", "Em curso", "Concluída"}


def utilizador_autenticado():
    """Devolve o ID do utilizador guardado como identidade no token JWT."""
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def e_admin():
    """O login tem de incluir o tipo do utilizador nas claims do token."""
    return get_jwt().get("tipo") == "admin"


def tarefa_json(tarefa):
    return {
        "id": tarefa.id,
        "titulo": tarefa.titulo,
        "descricao": tarefa.descricao,
        "estado": tarefa.estado,
        "utilizador_id": tarefa.utilizador_id,
    }


def tarefa_visivel(tarefa, user_id, admin):
    """Um admin pode aceder a qualquer tarefa; um utilizador só à sua."""
    return admin or tarefa.utilizador_id == user_id


class Tarefas(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument("titulo", type=str, required=True,
                            help="O título da tarefa é obrigatório.")
    argumentos.add_argument("descricao", type=str, default="")
    argumentos.add_argument("estado", type=str, default="Pendente")

    @jwt_required()
    def get(self):
        user_id = utilizador_autenticado()
        admin = e_admin()
        if user_id is None:
            return {"mensagem": "Identidade de utilizador inválida no token."}, 401

        query = TarefaModel.query
        if not admin:
            query = query.filter_by(utilizador_id=user_id)

        return {"tarefas": [tarefa_json(t) for t in query.all()]}, 200

    @jwt_required()
    def post(self):
        user_id = utilizador_autenticado()
        if user_id is None:
            return {"mensagem": "Identidade de utilizador inválida no token."}, 401

        dados = self.argumentos.parse_args()
        titulo = (dados.get("titulo") or "").strip()
        estado = dados.get("estado") or "Pendente"
        if not titulo:
            return {"mensagem": "O título da tarefa não pode ficar vazio."}, 400
        if estado not in ESTADOS_VALIDOS:
            return {"mensagem": "Estado inválido. Use Pendente, Em curso ou Concluída."}, 400

        tarefa = TarefaModel(
            titulo=titulo,
            descricao=dados.get("descricao") or "",
            estado=estado,
            utilizador_id=user_id,  # Não aceitar o ID do dono enviado pelo cliente.
        )
        try:
            bd.session.add(tarefa)
            bd.session.commit()
            return tarefa_json(tarefa), 201
        except Exception:
            bd.session.rollback()
            return {"mensagem": "Não foi possível criar a tarefa."}, 500


class Tarefa(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument("titulo", type=str, required=False)
    argumentos.add_argument("descricao", type=str, required=False)
    argumentos.add_argument("estado", type=str, required=False)

    @jwt_required()
    def get(self, tarefa_id):
        user_id = utilizador_autenticado()
        if user_id is None:
            return {"mensagem": "Identidade de utilizador inválida no token."}, 401

        tarefa = TarefaModel.query.get(tarefa_id)
        if tarefa is None:
            return {"mensagem": "Tarefa não encontrada."}, 404
        if not tarefa_visivel(tarefa, user_id, e_admin()):
            return {"mensagem": "Não tem permissões para consultar esta tarefa."}, 403
        return tarefa_json(tarefa), 200

    @jwt_required()
    def put(self, tarefa_id):
        user_id = utilizador_autenticado()
        if user_id is None:
            return {"mensagem": "Identidade de utilizador inválida no token."}, 401

        tarefa = TarefaModel.query.get(tarefa_id)
        if tarefa is None:
            return {"mensagem": "Tarefa não encontrada."}, 404
        if not tarefa_visivel(tarefa, user_id, e_admin()):
            return {"mensagem": "Não tem permissões para alterar esta tarefa."}, 403

        dados = self.argumentos.parse_args()
        if all(dados.get(campo) is None for campo in ("titulo", "descricao", "estado")):
            return {"mensagem": "Indique pelo menos um campo para alterar."}, 400

        if dados.get("titulo") is not None:
            titulo = dados["titulo"].strip()
            if not titulo:
                return {"mensagem": "O título da tarefa não pode ficar vazio."}, 400
            tarefa.titulo = titulo
        if dados.get("descricao") is not None:
            tarefa.descricao = dados["descricao"]
        if dados.get("estado") is not None:
            if dados["estado"] not in ESTADOS_VALIDOS:
                return {"mensagem": "Estado inválido. Use Pendente, Em curso ou Concluída."}, 400
            tarefa.estado = dados["estado"]

        try:
            bd.session.commit()
            return tarefa_json(tarefa), 200
        except Exception:
            bd.session.rollback()
            return {"mensagem": "Não foi possível alterar a tarefa."}, 500

    @jwt_required()
    def delete(self, tarefa_id):
        user_id = utilizador_autenticado()
        if user_id is None:
            return {"mensagem": "Identidade de utilizador inválida no token."}, 401

        tarefa = TarefaModel.query.get(tarefa_id)
        if tarefa is None:
            return {"mensagem": "Tarefa não encontrada."}, 404
        if not tarefa_visivel(tarefa, user_id, e_admin()):
            return {"mensagem": "Não tem permissões para eliminar esta tarefa."}, 403

        try:
            bd.session.delete(tarefa)
            bd.session.commit()
            return {"mensagem": "Tarefa eliminada com sucesso."}, 200
        except Exception:
            bd.session.rollback()
            return {"mensagem": "Não foi possível eliminar a tarefa."}, 500