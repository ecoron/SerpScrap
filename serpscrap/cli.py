import argparse
from serpscrap import SerpScrap, Config

def main():
    parser = argparse.ArgumentParser(description="SerpScrap CLI - Search engine scraping tool")
    parser.add_argument('--keywords', nargs='+', required=True, help='Keywords to search for (separate by space)')
    parser.add_argument('--scrape-urls', action='store_true', help='Also scrape the URLs found in the SERPs')
    args = parser.parse_args()

    config = Config()
    config.set('scrape_urls', args.scrape_urls)

    scrap = SerpScrap()
    scrap.init(config=config.get(), keywords=args.keywords)
    results = scrap.run()

    for result in results:
        print(result)

if __name__ == '__main__':
    main()
