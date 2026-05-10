import os
import time
import random
import logging
from typing import Optional, Dict, Any

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger("scraping")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

RATE_LIMIT_MIN = int(os.environ.get("SCRAPING_RATE_LIMIT_MIN", "2"))
RATE_LIMIT_MAX = int(os.environ.get("SCRAPING_RATE_LIMIT_MAX", "5"))
MAX_RETRIES = int(os.environ.get("SCRAPING_MAX_RETRIES", "3"))
MAX_CHAPTERS_PER_SESSION = int(os.environ.get("SCRAPING_MAX_CHAPTERS_PER_SESSION", "500"))
MAX_CHAPTERS_PER_DRIVER = int(os.environ.get("SCRAPING_MAX_CHAPTERS_PER_DRIVER", "50"))
DRIVER_INACTIVITY_TIMEOUT = int(os.environ.get("SCRAPING_DRIVER_INACTIVITY_TIMEOUT", "300"))  # 5 minutes

_robots_cache: Dict[str, float] = {}


class ChapterScraper:
    def __init__(self, site_key: str, site_config: Dict[str, Any]):
        self.site_key = site_key
        self.site_config = site_config
        self.driver: Optional[uc.Chrome] = None
        self.chapters_scraped = 0
        self.consecutive_failures = 0
        self.last_activity = time.time()

    def create_driver(self) -> uc.Chrome:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--window-size={1920 + random.randint(-50, 50)},{1080 + random.randint(-50, 50)}")

        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"--user-agent={user_agent}")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.popups": 2,
        }
        options.add_experimental_option("prefs", prefs)

        proxy = os.environ.get("SCRAPING_PROXY")
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")

        driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)

        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)

        return driver

    def _init_driver(self):
        if self.driver is None:
            self.driver = self.create_driver()

    def wait_for_cloudflare(self, timeout: int = 30) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: not self._is_cloudflare_challenge(d)
            )
            time.sleep(random.uniform(1, 2))
            return True
        except TimeoutException:
            logger.warning(f"Cloudflare challenge timeout after {timeout}s")
            return False

    def _is_cloudflare_challenge(self, driver) -> bool:
        page_title = driver.title.lower()
        if "just a moment" in page_title or "attention required" in page_title:
            return True

        try:
            if driver.find_element(By.ID, "cf-challenge"):
                return True
        except:
            pass

        try:
            if driver.find_element(By.ID, "challenge-running"):
                return True
        except:
            pass

        return False

    def _get_robots_delay(self, url: str) -> float:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        cache_key = f"{parsed.scheme}://{parsed.netloc}"

        if cache_key in _robots_cache:
            return _robots_cache[cache_key]

        try:
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                for line in response.text.split("\n"):
                    if line.lower().startswith("crawl-delay:"):
                        delay = float(line.split(":")[1].strip())
                        _robots_cache[cache_key] = delay
                        logger.info(f"robots.txt delay for {cache_key}: {delay}s")
                        return delay
        except Exception:
            pass

        _robots_cache[cache_key] = 0.0
        return 0.0

    def warm_up(self, base_url: str) -> bool:
        self._init_driver()
        try:
            logger.info(f"Warming up: {base_url}")
            self.driver.get(base_url)
            time.sleep(random.uniform(3, 5))
            return self.wait_for_cloudflare(timeout=30)
        except Exception as e:
            logger.error(f"Warm-up failed: {e}")
            return False

    def scrape_chapter(self, url: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        self._init_driver()

for attempt in range(MAX_RETRIES):
                try:
                    robots_delay = self._get_robots_delay(url)
                    if robots_delay > 0:
                        time.sleep(robots_delay)
                    self.driver.get(url)
                time.sleep(random.uniform(2, 4))

                if not self.wait_for_cloudflare(timeout=30):
                    raise Exception("Cloudflare challenge failed")

                self._scroll_progressive()

                content = self._extract_content(url)
                if content:
                    self.consecutive_failures = 0
                    self.chapters_scraped += 1
                    self.update_activity()
                    return content

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {url}: {e}")
                if retry_count >= 2:
                    self.consecutive_failures += 1
                time.sleep(5 * (2 ** attempt))

        return None

    def _simulate_mouse_movement(self):
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(3, 6)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            actions.perform()
        except Exception:
            pass

    def _scroll_progressive(self):
        self._simulate_mouse_movement()
        try:
            for _ in range(3):
                self.driver.execute_script(f"window.scrollBy(0, {random.randint(250, 350)});")
                time.sleep(random.uniform(0.5, 1.0))
            self.driver.execute_script("window.scrollTo(0, 0);")
        except Exception:
            pass

    def _extract_content(self, url: str) -> Optional[Dict[str, Any]]:
        config = self.site_config

        try:
            title_elem = self.driver.find_element(By.CSS_SELECTOR, config.get("chapter_title_selector", "h1"))
            title = title_elem.text.strip() if title_elem else ""
        except Exception:
            title = ""

        try:
            content_elem = self.driver.find_element(By.CSS_SELECTOR, config.get("chapter_content_selector", "#content"))
            html_content = content_elem.get_attribute("innerHTML")
        except Exception as e:
            logger.error(f"Content element not found: {e}")
            return None

        try:
            html_content = html_content.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception:
            pass

        soup = BeautifulSoup(html_content, "lxml")

        remove_selectors = config.get("remove_selectors", [])
        for selector in remove_selectors:
            for elem in soup.select(selector):
                elem.decompose()

        for tag in soup.find_all(["script", "style", "iframe"]):
            tag.decompose()

        for elem in soup.find_all(class_=lambda x: x and any(k in str(x).lower() for k in ["ad", "sponsor", "donate", "social"])):
            elem.decompose()

        for elem in soup.find_all("div"):
            if not elem.get_text(strip=True):
                elem.decompose()

        text_content = self._clean_text(soup)

        return {
            "title": title,
            "content": text_content,
            "html": str(soup),
            "url": url,
            "site_key": self.site_key,
        }

    def _clean_text(self, soup: BeautifulSoup) -> str:
        for br in soup.find_all("br"):
            if br.next_sibling and br.next_sibling.name == "br":
                new_p = soup.new_tag("p")
                br.replace_with(new_p)

        text = soup.get_text(separator="\n", strip=True)

        text = "\n".join(line for line in text.split("\n") if line.strip())

        try:
            text = text.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception:
            pass

        return text

    def scrape_next_chapter(self) -> Optional[str]:
        config = self.site_config
        next_selector = config.get("next_chapter_selector")

        if not next_selector:
            return None

        try:
            next_link = self.driver.find_element(By.CSS_SELECTOR, next_selector)
            href = next_link.get_attribute("href")
            if href:
                return href
        except Exception:
            pass

        return None

    def should_restart(self) -> bool:
        if self.chapters_scraped >= MAX_CHAPTERS_PER_SESSION:
            logger.info(f"Reached max chapters per session: {MAX_CHAPTERS_PER_SESSION}")
            return True
        if self.chapters_scraped >= MAX_CHAPTERS_PER_DRIVER:
            logger.info(f"Reached max chapters per driver: {MAX_CHAPTERS_PER_DRIVER}")
            return True
        if time.time() - self.last_activity > DRIVER_INACTIVITY_TIMEOUT:
            logger.info(f"Driver inactive for >{DRIVER_INACTIVITY_TIMEOUT}s, restarting")
            return True
        if self.consecutive_failures >= 2:
            logger.warning("Too many consecutive failures, recreating driver")
            return True
        return False

    def update_activity(self):
        self.last_activity = time.time()

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ScraperPool:
    def __init__(self, max_instances: int = 3):
        self.max_instances = max_instances
        self.active_drivers: Dict[str, ChapterScraper] = {}

    def get_scraper(self, site_key: str, site_config: Dict[str, Any]) -> ChapterScraper:
        if site_key in self.active_drivers:
            scraper = self.active_drivers[site_key]
            if scraper.driver is not None and not scraper.should_restart():
                return scraper
            scraper.close()
            del self.active_drivers[site_key]

        if len(self.active_drivers) >= self.max_instances:
            self._cleanup_lru()

        scraper = ChapterScraper(site_key, site_config)
        self.active_drivers[site_key] = scraper
        return scraper

    def _cleanup_lru(self):
        if self.active_drivers:
            oldest_key = next(iter(self.active_drivers))
            old_scraper = self.active_drivers.pop(oldest_key)
            old_scraper.close()

    def cleanup_all(self):
        for scraper in self.active_drivers.values():
            scraper.close()
        self.active_drivers.clear()

    def cleanup_orphaned_chrome(self):
        import subprocess
        try:
            subprocess.run(
                ["pkill", "-f", "chrome"],
                capture_output=True,
                timeout=10
            )
            logger.info("Cleaned up orphaned Chrome processes")
        except Exception as e:
            logger.warning(f"Failed to cleanup orphaned Chrome: {e}")


_scraper_pool: Optional[ScraperPool] = None


def get_scraper_pool() -> ScraperPool:
    global _scraper_pool
    if _scraper_pool is None:
        max_instances = int(os.environ.get("MAX_CHROME_INSTANCES", "3"))
        _scraper_pool = ScraperPool(max_instances=max_instances)
    return _scraper_pool