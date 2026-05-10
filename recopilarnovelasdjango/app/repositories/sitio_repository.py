from typing import Optional
from app.repositories.base_repository import BaseRepository


class SitioRepository(BaseRepository):
    def __init__(self):
        super().__init__("app_sitio")

    def find_all_sitios(self) -> list:
        return self.find_all(sort=[("nombre", 1)])

    def find_sitio_by_id(self, id: str) -> Optional[dict]:
        return self.find_by_id(id)

    def find_sitio_by_nombre(self, nombre: str) -> Optional[dict]:
        return self.find_one({"nombre": nombre})

    def create_sitio(self, data: dict) -> str:
        return self.insert(data)

    def update_sitio(self, id: str, data: dict) -> bool:
        return self.update(id, data)

    def delete_sitio(self, id: str) -> bool:
        return self.delete(id)

    def count_novelas_by_sitio(self, sitio_id: str) -> int:
        from app.repositories.novela_repository import NovelaRepository
        novela_repo = NovelaRepository()
        return novela_repo.count({"sitio_id": sitio_id})