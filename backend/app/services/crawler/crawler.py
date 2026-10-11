from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.async_api import async_playwright


class WebCrawler:

    """
    Generic website crawler.

    Responsibilities:
    - Fetch webpages using Playwright
    - Discover internal links
    - Discover linked PDF documents
    - Stay within the starting domain
    - Avoid duplicate URLs
    - Avoid irrelevant/non-HTML resources
    - Respect crawl depth and page limits

    It does NOT:
    - Parse HTML into documents
    - Create chunks
    - Generate embeddings
    - Perform retrieval

    PDF files are only discovered here.
    PDF downloading and processing is handled by
    WebIngestionService.
    """

    SKIP_PATH_KEYWORDS = {
        "login",
        "logout",
        "signin",
        "signup",
        "register",
        "cart",
        "checkout",
        "privacy",
        "terms",
        "cookie",
        "wp-admin",
        "feed",
        "xmlrpc",
    }

    # IMPORTANT:
    # .pdf is intentionally NOT here.
    #
    # PDFs are valid crawl targets and will be processed
    # separately by WebIngestionService.
    SKIP_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".mp4",
        ".mp3",
        ".avi",
        ".mov",
        ".zip",
        ".rar",
        ".7z",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    }

    def __init__(
        self,
        max_pages: int = 25,
        max_depth: int = 2,
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth

        self.playwright = None
        self.browser = None
        self.context = None

    # =====================================================
    # BROWSER LIFECYCLE
    # =====================================================

    async def start(self):

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True
        )

        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )

    async def close(self):

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    # =====================================================
    # URL NORMALIZATION
    # =====================================================

    @staticmethod
    def normalize_url(url: str) -> str:

        parsed = urlparse(url)

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]

        if netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        path = parsed.path or "/"

        # Normalize trailing slash
        if path != "/":
            path = path.rstrip("/")

        return urlunparse(
            (
                scheme,
                netloc,
                path,
                "",
                parsed.query,
                "",
            )
        )

    # =====================================================
    # PDF CHECK
    # =====================================================

    @staticmethod
    def is_pdf_url(url: str) -> bool:

        parsed = urlparse(url)

        return Path(
            parsed.path
        ).suffix.lower() == ".pdf"

    # =====================================================
    # DOMAIN CHECK
    # =====================================================

    @staticmethod
    def same_domain(
        url: str,
        base_domain: str,
    ) -> bool:

        parsed = urlparse(url)

        return (
            parsed.netloc.lower()
            == base_domain.lower()
        )

    # =====================================================
    # URL FILTERING
    # =====================================================

    def is_allowed_url(
        self,
        url: str,
        base_domain: str,
    ) -> bool:

        parsed = urlparse(url)

        # Only HTTP/HTTPS
        if parsed.scheme not in {
            "http",
            "https",
        }:
            return False

        # Stay on same domain
        if not self.same_domain(
            url,
            base_domain,
        ):
            return False

        path = parsed.path.lower()

        # -------------------------------------------------
        # IMPORTANT:
        # PDFs are explicitly allowed.
        # -------------------------------------------------

        if self.is_pdf_url(url):
            return True

        # Skip irrelevant paths
        if any(
            keyword in path
            for keyword in self.SKIP_PATH_KEYWORDS
        ):
            return False

        # Skip irrelevant/non-HTML resources
        if any(
            path.endswith(extension)
            for extension in self.SKIP_EXTENSIONS
        ):
            return False

        return True

    # =====================================================
    # LINK DISCOVERY
    # =====================================================

    async def find_links(
        self,
        page,
        base_url: str,
        base_domain: str,
    ) -> list[str]:

        links = await page.evaluate(
            """
            () => Array.from(
                document.querySelectorAll("a[href]")
            ).map(
                a => a.getAttribute("href")
            )
            """
        )

        discovered = []

        for link in links:

            if not link:
                continue

            link = link.strip()

            # Ignore anchors/javascript/mail/tel links
            if (
                link.startswith("#")
                or link.startswith("javascript:")
                or link.startswith("mailto:")
                or link.startswith("tel:")
            ):
                continue

            full_url = urljoin(
                base_url,
                link,
            )

            full_url = self.normalize_url(
                full_url
            )

            if not self.is_allowed_url(
                full_url,
                base_domain,
            ):
                continue

            discovered.append(
                full_url
            )

        return list(
            dict.fromkeys(discovered)
        )

    # =====================================================
    # SINGLE HTML PAGE FETCH
    # =====================================================

    async def fetch_page(
        self,
        page,
        url: str,
    ) -> str | None:

        try:

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            if response is None:
                return None

            status = response.status

            if status >= 400:

                print(
                    f"Skipping {url} "
                    f"(HTTP {status})"
                )

                return None

            # Give JavaScript-rendered content
            # a short opportunity to appear.
            try:

                await page.wait_for_load_state(
                    "networkidle",
                    timeout=5000,
                )

            except Exception:

                # networkidle is not required
                pass

            return await page.content()

        except Exception as exc:

            print(
                f"Failed to crawl {url}: {exc}"
            )

            return None

    # =====================================================
    # MULTI-PAGE CRAWL
    # =====================================================

    async def crawl(
        self,
        url: str,
    ) -> list[dict]:

        if not url:

            raise ValueError(
                "A website URL is required."
            )

        start_url = self.normalize_url(
            url
        )

        parsed = urlparse(start_url)

        if parsed.scheme not in {
            "http",
            "https",
        }:

            raise ValueError(
                "Only HTTP and HTTPS URLs are supported."
            )

        base_domain = parsed.netloc

        if not self.context:
            await self.start()

        page = await self.context.new_page()

        queue = deque(
            [
                (
                    start_url,
                    0,
                )
            ]
        )

        visited = set()

        pages = []

        try:

            while (
                queue
                and len(pages) < self.max_pages
            ):

                current_url, depth = queue.popleft()

                if current_url in visited:
                    continue

                visited.add(current_url)

                print(
                    f"Crawling "
                    f"[{len(pages) + 1}/{self.max_pages}] "
                    f"depth={depth}: "
                    f"{current_url}"
                )

                # =================================================
                # PDF
                # =================================================
                #
                # Do NOT send PDF URLs to Playwright.
                #
                # We only record the URL here.
                # WebIngestionService will download/process it.
                # =================================================

                if self.is_pdf_url(
                    current_url
                ):

                    pages.append(
                        {
                            "url": current_url,
                            "type": "pdf",
                            "depth": depth,
                        }
                    )

                    continue

                # =================================================
                # HTML PAGE
                # =================================================

                html = await self.fetch_page(
                    page,
                    current_url,
                )

                if not html:
                    continue

                pages.append(
                    {
                        "url": current_url,
                        "type": "html",
                        "html": html,
                        "depth": depth,
                    }
                )

                # Don't discover more pages at max depth
                if depth >= self.max_depth:
                    continue

                links = await self.find_links(
                    page,
                    current_url,
                    base_domain,
                )

                for link in links:

                    if link in visited:
                        continue

                    # Prevent queue explosion
                    if (
                        len(visited)
                        + len(queue)
                        >= self.max_pages * 3
                    ):
                        break

                    queue.append(
                        (
                            link,
                            depth + 1,
                        )
                    )

        finally:

            await page.close()

        return pages