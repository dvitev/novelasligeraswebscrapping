from typing import Any, Optional
from bson import ObjectId
from pymongo.collection import Collection
from app.db import get_db


class BaseRepository:
    def __init__(self, collection_name: str):
        self.collection: Collection = get_db()[collection_name]

    def find_all(self, filter_dict: dict = None, sort: list = None, limit: int = 0) -> list:
        query = filter_dict or {}
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_by_id(self, id: str) -> Optional[dict]:
        try:
            return self.collection.find_one({"_id": ObjectId(id)})
        except Exception:
            return None

    def find_one(self, filter_dict: dict) -> Optional[dict]:
        return self.collection.find_one(filter_dict)

    def find_by_filter(self, filter_dict: dict, sort: list = None, skip: int = 0, limit: int = 0) -> list:
        cursor = self.collection.find(filter_dict)
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    def insert(self, data: dict) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def insert_many(self, data_list: list) -> list:
        result = self.collection.insert_many(data_list)
        return [str(id) for id in result.inserted_ids]

    def update(self, id: str, data: dict, upsert: bool = False) -> bool:
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data},
                upsert=upsert
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception:
            return False

    def update_many(self, filter_dict: dict, data: dict) -> int:
        result = self.collection.update_many(filter_dict, {"$set": data})
        return result.modified_count

    def update_one_by_filter(self, filter_dict: dict, data: dict) -> bool:
        result = self.collection.update_one(filter_dict, {"$set": data})
        return result.modified_count > 0 or result.upserted_id is not None

    def delete(self, id: str) -> bool:
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def delete_many(self, filter_dict: dict) -> int:
        result = self.collection.delete_many(filter_dict)
        return result.deleted_count

    def aggregate(self, pipeline: list) -> list:
        return list(self.collection.aggregate(pipeline))

    def count(self, filter_dict: dict = None) -> int:
        query = filter_dict or {}
        return self.collection.count_documents(query)

    def distinct(self, field: str, filter_dict: dict = None) -> list:
        query = filter_dict or {}
        return self.collection.distinct(field, query)