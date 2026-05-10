import re
from typing import Optional
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


EXCLUDED_GENRES = ["Yaoi", "Lgbt+", "Yuri", "Shounen ai", "Shoujo ai"]


class NovelaRepository(BaseRepository):
    def __init__(self):
        super().__init__("app_novela")

    def find_all_novelas(self, sitio_id: str = None, limit: int = 0) -> list:
        filter_dict = {}
        if sitio_id:
            filter_dict["sitio_id"] = sitio_id
        return self.find_all(filter_dict, sort=[("titulo", 1)], limit=limit)

    def find_novela_by_id(self, id: str) -> Optional[dict]:
        return self.find_by_id(id)

    def find_novelas_by_sitio(self, sitio_id: str, exclude_genres: bool = True) -> list:
        filter_dict = {"sitio_id": sitio_id}
        if exclude_genres:
            genre_pattern = "|".join(EXCLUDED_GENRES)
            filter_dict["genero"] = {"$not": re.compile(genre_pattern, re.IGNORECASE)}
        return self.find_all(filter_dict, sort=[("titulo", 1)])

    def find_novelas_with_conteo_aggregate(self, sitio_id: str = None) -> list:
        match_stage = {}
        if sitio_id:
            match_stage["sitio_id"] = sitio_id

        pipeline = [
            {"$match": match_stage},
            {"$lookup": {
                "from": "app_capitulo",
                "localField": "_id",
                "foreignField": "novela_id",
                "as": "capitulos"
            }},
            {"$lookup": {
                "from": "app_contenidocapitulo",
                "localField": "_id",
                "foreignField": "novela_id",
                "as": "contenidos"
            }},
            {"$project": {
                "_id": 1,
                "titulo": 1,
                "nombre": 1,
                "sinopsis": 1,
                "autor": 1,
                "genero": 1,
                "status": 1,
                "url": 1,
                "imagen_url": 1,
                "sitio_id": 1,
                "cantidad_capitulos": {"$size": "$capitulos"},
                "cantidad_contenido": {"$size": "$contenidos"}
            }},
            {"$sort": {"titulo": 1}}
        ]

        return self.aggregate(pipeline)

    def find_novelas_with_conteo(self, sitio_id: str = None) -> list:
        return self.find_novelas_with_conteo_aggregate(sitio_id)

    def get_conteo_novela_aggregate(self, novela_id: str) -> Optional[dict]:
        pipeline = [
            {"$match": {"_id": ObjectId(novela_id)}},
            {"$lookup": {
                "from": "app_capitulo",
                "localField": "_id",
                "foreignField": "novela_id",
                "as": "capitulos"
            }},
            {"$lookup": {
                "from": "app_contenidocapitulo",
                "localField": "_id",
                "foreignField": "novela_id",
                "as": "contenidos"
            }},
            {"$project": {
                "_id": 1,
                "titulo": 1,
                "nombre": 1,
                "sinopsis": 1,
                "autor": 1,
                "genero": 1,
                "status": 1,
                "url": 1,
                "imagen_url": 1,
                "cantidad_capitulos": {"$size": "$capitulos"},
                "cantidad_contenido_capitulos": {"$size": "$contenidos"}
            }}
        ]

        results = self.aggregate(pipeline)
        return results[0] if results else None

    def get_generos_by_sitio_aggregate(self, sitio_id: str) -> list:
        pipeline = [
            {"$match": {"sitio_id": sitio_id}},
            {"$project": {
                "genero_array": {
                    "$split": [{"$ifNull": ["$genero", ""]}, ","]
                }
            }},
            {"$unwind": "$genero_array"},
            {"$project": {
                "genero": {"$trim": {"input": "$genero_array"}}
            }},
            {"$match": {
                "genero": {"$ne": ""},
                "genero": {"$not": {"$in": EXCLUDED_GENRES}}
            }},
            {"$group": {"_id": None, "generos": {"$addToSet": "$genero"}}},
            {"$project": {"_id": 0, "generos": 1}}
        ]

        results = self.aggregate(pipeline)
        if results:
            return sorted(results[0].get("generos", []))
        return []

    def search_novelas(self, query: str, sitio_id: str = None) -> list:
        filter_dict = {"titulo": {"$regex": query, "$options": "i"}}
        if sitio_id:
            filter_dict["sitio_id"] = sitio_id
        return self.find_all(filter_dict, sort=[("titulo", 1)])

    def create_novela(self, data: dict) -> str:
        return self.insert(data)

    def update_novela(self, id: str, data: dict) -> bool:
        return self.update(id, data)

    def delete_novela(self, id: str) -> bool:
        return self.delete(id)

    def count_novelas_by_sitio(self, sitio_id: str) -> int:
        return self.count({"sitio_id": sitio_id})