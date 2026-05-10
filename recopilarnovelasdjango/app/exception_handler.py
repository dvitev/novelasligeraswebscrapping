"""
Custom exception handler for Django REST Framework.
Provides consistent JSON error responses for different error types.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from bson.errors import InvalidId
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger('app')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that converts specific errors to appropriate HTTP responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': {
                'code': response.status_code,
                'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            }
        }
        response.data = error_data
        return response

    # Handle bson.errors.InvalidId (invalid ObjectId format)
    if isinstance(exc, InvalidId):
        logger.warning(f"Invalid ObjectId: {exc}")
        return Response(
            {
                'error': {
                    'code': 400,
                    'message': 'Invalid ID format. Ensure the ID is a valid MongoDB ObjectId.'
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle pymongo ConnectionFailure / ServerSelectionTimeoutError
    if isinstance(exc, (ConnectionFailure, ServerSelectionTimeoutError)):
        logger.error(f"MongoDB connection error: {exc}")
        return Response(
            {
                'error': {
                    'code': 503,
                    'message': 'Service temporarily unavailable. Database connection failed.'
                }
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # Handle pymongo.errors (other MongoDB errors)
    if 'pymongo' in str(type(exc).__module__):
        logger.error(f"MongoDB error: {exc}")
        return Response(
            {
                'error': {
                    'code': 500,
                    'message': 'Database operation failed. Please try again later.'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Handle unexpected exceptions
    logger.exception(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {
            'error': {
                'code': 500,
                'message': 'An unexpected error occurred. Please contact the administrator.'
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )