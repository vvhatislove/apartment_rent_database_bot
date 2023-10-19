class User:
    def __init__(self, id_: int, name: str, tg_user_id: int, is_admin: bool):
        self.id_ = id_
        self.name = name
        self.tg_user_id = tg_user_id
        self.is_admin = is_admin
