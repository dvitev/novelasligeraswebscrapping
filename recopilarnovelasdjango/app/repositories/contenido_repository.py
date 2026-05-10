from typing import Optional
from app.repositories.base_repository import BaseRepository


class ContenidoRepository(BaseRepository):
    def __init__(self):
        super().__init__("app_contenidocapitulo")

    def find_contenidos_by_novela(self, novela_id: str) -> list:
        return self.find_all({"novela_id": novela_id})

    def find_contenidos_by_capitulo(self, capitulo_id: str) -> list:
        return self.find_all({"capitulo_id": capitulo_id})

    def find_contenido_by_id(self, id: str) -> Optional[dict]:
        return self.find_by_id(id)

    def find_contenido_by_capitulo(self, capitulo_id: str) -> Optional[dict]:
        return self.find_one({"capitulo_id": capitulo_id})

    def count_contenidos_by_novela(self, novela_id: str) -> int:
        return self.count({"novela_id": novela_id})

    def count_contenidos_by_capitulo(self, capitulo_id: str) -> int:
        return self.count({"capitulo_id": capitulo_id})

    def create_contenido(self, data: dict) -> str:
        return self.insert(data)

    def update_contenido(self, id: str, data: dict) -> bool:
        return self.update(id, data)

    def delete_contenido(self, id: str) -> bool:
        return self.delete(id)

    def delete_contenidos_by_novela(self, novela_id: str) -> int:
        return self.delete_many({"novela_id": novela_id})

    def delete_contenidos_by_capitulo(self, capitulo_id: str) -> int:
        return self.delete_many({"capitulo_id": capitulo_id})

    def find_failed_contenidos(self) -> list:
        return self.find_all({"status": "failed"})

    def mark_as_failed(self, capitulo_id: str) -> bool:
        return self.update_many({"capitulo_id": capitulo_id}, {"status": "failed"}) > 0

    def mark_as_pending_retry(self, capitulo_id: str) -> bool:
        return self.update_many({"capitulo_id": capitulo_id}, {"status": "pending_retry"}) > 0