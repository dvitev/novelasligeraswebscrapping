"""
Health check endpoint for MongoDB connectivity.
"""
import os
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger('app')

MONGODB_HOST = os.environ.get("MONGODB_HOST", "192.168.1.11")
MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "recopilarnovelas")


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint that verifies MongoDB connectivity.
    
    Returns:
        200: {"status": "healthy", "database": "recopilarnovelas"}
        503: {"status": "unhealthy", "error": "Database connection failed"}
    """
    try:
        client = MongoClient(
            host=MONGODB_HOST,
            port=MONGODB_PORT,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        client.admin.command('ping')
        
        return Response(
            {
                "status": "healthy",
                "database": MONGODB_DATABASE,
                "mongodb_host": MONGODB_HOST,
            },
            status=status.HTTP_200_OK
        )
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {
                "status": "unhealthy",
                "error": "Database connection failed",
                "details": str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return Response(
            {
                "status": "unhealthy",
                "error": "Unexpected error",
                "details": str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )