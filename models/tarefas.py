from con_sql_alchemy import bd


class TarefaModel(bd.Model):
    __tablename__ = "tarefas"

    # O ID é inteiro e criado automaticamente pela base de dados.
    id = bd.Column(bd.Integer, primary_key=True)
    titulo = bd.Column(bd.String(200), nullable=False)
    descricao = bd.Column(bd.Text)
    estado = bd.Column(bd.String(20), nullable=False, default="Pendente")
    utilizador_id = bd.Column(bd.Integer,bd.ForeignKey("Utilizadores.id"),nullable=False,
    )

    # Relação: cada tarefa pertence a um utilizador.
    utilizador = bd.relationship("UserModel", back_populates="tarefas")

    def __init__(self, titulo, descricao, estado, utilizador_id):
        self.titulo = titulo
        self.descricao = descricao
        self.estado = estado
        self.utilizador_id = utilizador_id

    def json(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "estado": self.estado,
            "utilizador_id": self.utilizador_id,
        }

    @classmethod
    def find_tarefa(cls, tarefa_id):
        tarefa = cls.query.filter_by(id=tarefa_id).first()
        if tarefa:
            return tarefa
        return None

    def save_tarefa(self):
        bd.session.add(self)
        bd.session.commit()

    def update_tarefa(self, titulo_atualizado, descricao_atualizada, estado_atualizado):
        self.titulo = titulo_atualizado
        self.descricao = descricao_atualizada
        self.estado = estado_atualizado

    def delete_tarefa(self):
        bd.session.delete(self)
        bd.session.commit()