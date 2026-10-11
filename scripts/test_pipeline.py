crawler = WebCrawler()

processor = HTMLProcessor()

chunker = Chunker()

html = await crawler.crawl(URL)

page = RawPage(
    url=URL,
    html=html
)

document = processor.process(page)

chunks = chunker.create_chunks(document)

print(document.title)

print(len(chunks))

for chunk in chunks[:5]:
    print(chunk.heading)