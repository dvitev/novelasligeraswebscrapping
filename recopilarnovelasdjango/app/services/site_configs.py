SITE_CONFIGS = {
    "novelbin": {
        "base_url": "https://novelbin.com",
        "chapter_content_selector": "#chr-content",
        "chapter_title_selector": ".chr-title h2",
        "next_chapter_selector": "#next_chap",
        "remove_selectors": [".ads-holder", "script", ".hidden"],
        "encoding": "utf-8",
    },
    "fanmtl": {
        "base_url": "https://www.fanmtl.com",
        "chapter_content_selector": ".chapter-content",
        "chapter_title_selector": ".chapter-title",
        "next_chapter_selector": "a.next-chapter",
        "remove_selectors": [".ad-container", "script", "ins"],
        "encoding": "utf-8",
    },
    "mtlnovel": {
        "base_url": "https://www.mtlnovel.com",
        "chapter_content_selector": ".chapter-content",
        "chapter_title_selector": ".current-crumb span",
        "next_chapter_selector": "a.next",
        "remove_selectors": [".donate-section", "script", ".ad-zone"],
        "encoding": "utf-8",
    },
}


def get_site_config(site_key: str) -> dict:
    return SITE_CONFIGS.get(site_key, {})


def get_all_site_keys() -> list:
    return list(SITE_CONFIGS.keys())