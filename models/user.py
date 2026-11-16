from con_sql_alchemy import bd


class UserModel(bd.Model):
    __tablename__ = "Utilizadores"

    # Campos pedidos no PDF
    id = bd.Column(bd.Integer, primary_key=True, autoincrement=True)
    username = bd.Column(bd.String(40), unique=True, nullable=False)
    email = bd.Column(bd.String(255), unique=True, nullable=False)
    # O hash da palavra-passe é maior do que 40 caracteres.
    password = bd.Column(bd.String(255), nullable=False)
    tipo = bd.Column(bd.String(20), nullable=False, default="utilizador")

    # Um utilizador pode ter várias tarefas.
    tarefas = bd.relationship(
        "TarefaModel",
        back_populates="utilizador",
        cascade="all, delete-orphan",
    )

    def __init__(self, username, email, password, tipo="utilizador"):
        self.username = username
        self.email = email
        self.password = password
        self.tipo = tipo

    def json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "tipo": self.tipo,
        }

    @classmethod
    def find_user(cls, username):
        user = cls.query.filter_by(username=username).first()
        if user:
            return user
        return None

    @classmethod
    def find_by_email(cls, email):
        user = cls.query.filter_by(email=email).first()
        if user:
            return user
        return None

    def save_user(self):
        bd.session.add(self)
        try:
            bd.session.commit()
        except Exception:
            bd.session.rollback()
            raise

    def delete_user(self):
        bd.session.delete(self)
        try:
            bd.session.commit()
        except Exception:
            bd.session.rollback()
            raise