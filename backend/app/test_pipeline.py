import asyncio

from app.models.raw_page import RawPage
from app.services.crawler.crawler import WebCrawler
from app.services.processor.html_processor import HTMLProcessor


URL = "https://mastersunion.org/pgp-in-applied-ai-and-agentic-systems"


async def main():

    crawler = WebCrawler()
    processor = HTMLProcessor()

    await crawler.start()

    html = await crawler.crawl(URL)

    with open("page.html", "w", encoding="utf-8") as f:
        f.write(html)

    await crawler.close()

    page = RawPage(
        url=URL,
        html=html
    )

    document, chunks = processor.process(page)

    print("=" * 80)
    print(document.title)
    print("=" * 80)

    print(f"\nTotal Chunks: {len(chunks)}\n")

    for chunk in chunks[:10]:

        print(f"Heading: {chunk.heading}")
        print(chunk.text[:400])
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())