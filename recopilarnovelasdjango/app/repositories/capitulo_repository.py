from typing import Optional
from app.repositories.base_repository import BaseRepository


class CapituloRepository(BaseRepository):
    def __init__(self):
        super().__init__("app_capitulo")

    def find_capitulos_by_novela(self, novela_id: str, sort_order: int = 1) -> list:
        return self.find_all(
            {"novela_id": novela_id},
            sort=[("numero", sort_order)]
        )

    def find_capitulo_by_id(self, id: str) -> Optional[dict]:
        return self.find_by_id(id)

    def find_capitulo_by_numero(self, novela_id: str, numero: int) -> Optional[dict]:
        return self.find_one({"novela_id": novela_id, "numero": numero})

    def count_capitulos_by_novela(self, novela_id: str) -> int:
        return self.count({"novela_id": novela_id})

    def create_capitulo(self, data: dict) -> str:
        return self.insert(data)

    def update_capitulo(self, id: str, data: dict) -> bool:
        return self.update(id, data)

    def delete_capitulo(self, id: str) -> bool:
        return self.delete(id)

    def delete_capitulos_by_novela(self, novela_id: str) -> int:
        return self.delete_many({"novela_id": novela_id})