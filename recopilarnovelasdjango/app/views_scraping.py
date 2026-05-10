import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from celery import chain

logger = logging.getLogger("scraping")


class IniciarScrapingView(APIView):
    def post(self, request):
        novela_id = request.data.get("novela_id")
        site_key = request.data.get("site_key", "novelbin")
        start_url = request.data.get("start_url")
        max_chapters = request.data.get("max_chapters")

        if not novela_id or not start_url:
            return Response(
                {"error": "novela_id and start_url are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import scrape_novel_chapters
        from .repositories import NovelaRepository

        novela_repo = NovelaRepository()
        novela = novela_repo.find_by_id(novela_id)

        if not novela:
            return Response(
                {"error": f"Novela not found: {novela_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        from redis import Redis
        from django.conf import settings
        try:
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            active_key = f"scraping:active:{novela_id}"
            if redis_client.exists(active_key):
                return Response(
                    {"error": "Ya existe una tarea de scraping activa para esta novela"},
                    status=status.HTTP_409_CONFLICT
                )
            redis_client.setex(active_key, 7200, "1")
            redis_client.close()
        except Exception as e:
            logger.warning(f"Could not check active task: {e}")

        task = scrape_novel_chapters.delay(
            novela_id=novela_id,
            site_key=site_key,
            start_url=start_url,
            max_chapters=max_chapters
        )

        return Response({
            "task_id": task.id,
            "status": "PENDING",
            "novela_id": novela_id,
            "message": "Scraping task started"
        }, status=status.HTTP_202_ACCEPTED)


class ProgresoScrapingView(APIView):
    def get(self, request, task_id):
        from django.conf import settings
        from redis import Redis

        try:
            redis_client = Redis.from_url(settings.CELERY_RESULT_BACKEND)
            key = f"celery-task-meta-{task_id}"
            task_data = redis_client.get(key)
            redis_client.close()

            if task_data:
                import json
                data = json.loads(task_data)
                return Response({
                    "task_id": task_id,
                    "status": data.get("status", "UNKNOWN"),
                    "current": data.get("result", {}).get("current", 0),
                    "chapter": data.get("result", {}).get("chapter", ""),
                    "saved": data.get("result", {}).get("saved", 0),
                    "failed": data.get("result", {}).get("failed", 0),
                })

            result = AsyncResult(task_id)
            return Response({
                "task_id": task_id,
                "status": result.state,
                "result": result.result if result.ready() else None,
            })

        except Exception as e:
            logger.error(f"Error getting task progress: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CancelarScrapingView(APIView):
    def post(self, request, task_id):
        from recopilarnovelasdjango.celery import app

        try:
            app.control.revoke(task_id, terminate=True, signal="SIGTERM")

            from django.conf import settings
            from redis import Redis
            try:
                redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
                keys = redis_client.keys(f"scraping:active:*")
                for key in keys:
                    redis_client.delete(key)
                redis_client.close()
            except:
                pass

            return Response({
                "task_id": task_id,
                "status": "REVOKED",
                "message": "Task cancelled successfully"
            })

        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TareasActivasView(APIView):
    def get(self, request):
        from recopilarnovelasdjango.celery import app

        try:
            inspector = app.control.inspect()
            active_tasks = inspector.active() or {}

            tasks = []
            for worker, worker_tasks in active_tasks.items():
                for task in worker_tasks:
                    task_id = task.get("id")
                    name = task.get("name", "")
                    if "scrape" in name.lower():
                        result = AsyncResult(task_id)
                        task_info = {
                            "task_id": task_id,
                            "name": name,
                            "worker": worker,
                            "status": result.state,
                        }
                        if result.info and isinstance(result.info, dict):
                            task_info.update(result.info.get("meta", {}))
                        tasks.append(task_info)

            return Response(tasks)

        except Exception as e:
            logger.error(f"Error getting active tasks: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )