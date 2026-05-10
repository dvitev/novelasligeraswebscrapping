import logging
import time
import random
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger("scraping")

try:
    from .services.scraper_service import ChapterScraper, get_scraper_pool
    from .services.site_configs import get_site_config
    from .repositories import CapituloRepository, ContenidoRepository
except ImportError:
    ChapterScraper = None
    get_site_config = None


@shared_task(bind=True, max_retries=3)
def scrape_novel_chapters(self, novela_id: str, site_key: str, start_url: str, max_chapters: int = None):
    if ChapterScraper is None:
        logger.error("scraper_service not available")
        return {"status": "error", "message": "Scraper service not available"}

    site_config = get_site_config(site_key)
    if not site_config:
        return {"status": "error", "message": f"Site config not found for: {site_key}"}

    pool = get_scraper_pool()
    scraper = pool.get_scraper(site_key, site_config)

    chapters_saved = 0
    chapters_failed = 0
    current_url = start_url
    chapter_num = 1

    try:
        if not scraper.warm_up(site_config.get("base_url", "")):
            logger.warning("Warm-up failed, continuing anyway")

        while current_url:
            if max_chapters and chapter_num > max_chapters:
                logger.info(f"Reached max chapters limit: {max_chapters}")
                break

            task_state = self.app.AsyncResult(self.request.id)
            if task_state.info.get("status") == "REVOKED":
                logger.info("Task was revoked, saving progress")
                break

            try:
                content = scraper.scrape_chapter(current_url)
                if content:
                    result = _save_chapter(novela_id, chapter_num, content)
                    if result:
                        chapters_saved += 1
                    else:
                        chapters_failed += 1
                        _mark_for_retry(novela_id, chapter_num, current_url)
                else:
                    chapters_failed += 1
                    _mark_for_retry(novela_id, chapter_num, current_url)

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": chapter_num,
                        "chapter": content.get("title", f"Chapter {chapter_num}") if content else "Unknown",
                        "saved": chapters_saved,
                        "failed": chapters_failed,
                    }
                )

                current_url = scraper.scrape_next_chapter()
                chapter_num += 1

                time.sleep(random.uniform(2, 5))

            except Exception as e:
                logger.error(f"Error scraping chapter {chapter_num}: {e}")
                chapters_failed += 1
                if chapters_failed >= 5:
                    logger.error("Too many consecutive failures, stopping")
                    break

    except SoftTimeLimitExceeded:
        logger.warning("Soft time limit exceeded, saving progress")
        scraper.close()
        return {
            "status": "partial",
            "saved": chapters_saved,
            "failed": chapters_failed,
            "last_chapter": chapter_num,
            "message": "Task stopped due to time limit",
        }
    finally:
        scraper.close()
        pool.cleanup_orphaned_chrome()

    return {
        "status": "completed",
        "saved": chapters_saved,
        "failed": chapters_failed,
        "total_chapters": chapter_num - 1,
    }


def _save_chapter(novela_id: str, chapter_num: int, content: dict):
    from datetime import datetime

    try:
        capitulo_repo = CapituloRepository()
        contenido_repo = ContenidoRepository()

        existing = capitulo_repo.find_capitulo_by_numero(novela_id, chapter_num)
        if existing:
            logger.info(f"Chapter {chapter_num} already exists, skipping")
            return None

        chapter_data = {
            "novela_id": novela_id,
            "numero": chapter_num,
            "titulo": content.get("title", f"Chapter {chapter_num}"),
            "url": content.get("url", ""),
            "created_at": datetime.utcnow(),
        }

        capitulo = capitulo_repo.insert(chapter_data)

        if capitulo and "_id" in capitulo:
            contenido_data = {
                "novela_id": novela_id,
                "capitulo_id": str(capitulo["_id"]),
                "contenido": content.get("content", ""),
                "html": content.get("html", ""),
                "created_at": datetime.utcnow(),
            }
            contenido_repo.insert(contenido_data)
            logger.info(f"Saved chapter {chapter_num}: {content.get('title')}")

    except Exception as e:
        logger.error(f"Failed to save chapter {chapter_num}: {e}")


@shared_task
def retry_failed_chapters():
    from .repositories import ContenidoRepository

    logger.info("Retry queue: Processing failed chapters")
    contenido_repo = ContenidoRepository()

    failed = contenido_repo.find_failed_contenidos()
    retried = 0

    for item in failed:
        logger.info(f"Retrying chapter: {item.get('capitulo_id')}")
        retried += 1

    return {"status": "completed", "retried": retried}


def _mark_for_retry(novela_id: str, chapter_num: int, url: str):
    from datetime import datetime

    try:
        contenido_repo = ContenidoRepository()
        contenido_repo.insert({
            "novela_id": novela_id,
            "capitulo_numero": chapter_num,
            "url": url,
            "status": "pending_retry",
            "created_at": datetime.utcnow(),
        })
        logger.warning(f"Chapter {chapter_num} marked for retry")
    except Exception as e:
        logger.error(f"Failed to mark chapter for retry: {e}")


@shared_task
def scrape_novel_list(sitio_id: str, site_key: str):
    from .repositories import SitioRepository

    if ChapterScraper is None:
        logger.error("scraper_service not available")
        return {"status": "error", "message": "Scraper service not available"}

    sitio_repo = SitioRepository()
    sitio = sitio_repo.find_by_id(sitio_id)

    if not sitio:
        return {"status": "error", "message": f"Sitio not found: {sitio_id}"}

    site_config = get_site_config(site_key)
    if not site_config:
        return {"status": "error", "message": f"Site config not found for: {site_key}"}

    pool = get_scraper_pool()
    scraper = pool.get_scraper(site_key, site_config)

    novel_urls = []

    try:
        if not scraper.warm_up(site_config.get("base_url", "")):
            logger.warning("Warm-up failed")

        base_url = sitio.get("url", "")
        if base_url:
            scraper.driver.get(base_url)
            time.sleep(random.uniform(3, 5))

            novel_links = scraper.driver.find_elements("css selector", "a.novel-link")
            for link in novel_links:
                href = link.get_attribute("href")
                if href:
                    novel_urls.append(href)

    except Exception as e:
        logger.error(f"Error scraping novel list: {e}")
    finally:
        scraper.close()

    logger.info(f"Found {len(novel_urls)} novels to scrape")

    from celery import group
    jobs = []
    for url in novel_urls[:10]:
        jobs.append(scrape_novel_chapters.s(sitio_id, site_key, url))

    if jobs:
        group(jobs).apply_async()
        logger.info(f"Dispatched {len(jobs)} scraping tasks")

    return {"status": "completed", "novels_found": len(novel_urls)}


@shared_task(bind=True)
def cleanup_stale_tasks(self):
    from celery.result import AsyncResult
    from datetime import datetime, timedelta

    logger.info("Running cleanup of stale tasks")

    stale_threshold = datetime.utcnow() - timedelta(minutes=30)

    try:
        active_tasks = []
        i = self.app.control.inspect()
        active_tasks = i.active() or {}

        cleaned = 0
        for worker, tasks in active_tasks.items():
            for task in tasks:
                task_id = task.get("id")
                if task_id:
                    result = AsyncResult(task_id)
                    if result.info and isinstance(result.info, dict):
                        last_update = result.info.get("timestamp")
                        if last_update and isinstance(last_update, datetime):
                            if last_update < stale_threshold:
                                self.app.control.revoke(task_id, terminate=True, signal="SIGTERM")
                                cleaned += 1

        logger.info(f"Cleaned up {cleaned} stale tasks")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    try:
        pool = get_scraper_pool()
        pool.cleanup_orphaned_chrome()
    except Exception as e:
        logger.warning(f"Could not cleanup Chrome processes: {e}")

    return {"status": "completed", "cleaned_tasks": cleaned}


@shared_task
def scrape_ongoing_novels():
    from .repositories import NovelaRepository

    logger.info("Scraping ongoing novels for new chapters")

    novela_repo = NovelaRepository()
    ongoing_novelas = novela_repo.find_by_filter({"status": "ongoing"})

    dispatched = 0
    for novela in ongoing_novelas:
        if novela.get("sitio_id"):
            scrape_novel_chapters.delay(
                str(novela["_id"]),
                novela.get("site_key", "novelbin"),
                novela.get("url", ""),
                max_chapters=10,
            )
            dispatched += 1

    logger.info(f"Dispatched {dispatched} ongoing novel scraping tasks")

    return {"status": "completed", "dispatched": dispatched}