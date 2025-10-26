# -*- coding: utf-8 -*-
import logging
from .selenium import SelScrape  # Nutzt die refactored Chrome Headless Klasse!

logger = logging.getLogger(__name__)

class ScrapeWorkerFactory:
    """
    Factory zum Erzeugen von Chrome Headless Scraper-Worker-Threads.
    """
    def __init__(self, config, search_engine, queries, screenshot_dir=None):
        self.config = config
        self.search_engine = search_engine  # z.B. 'google', 'bing'
        self.queries = queries  # Liste von Suchanfragen
        self.screenshot_dir = screenshot_dir
        self.workers = []

    def create_workers(self):
        """
        Erzeuge einen Worker für jede Suchanfrage.
        """
        self.workers = [
            SelScrape(
                config = self.config,
                search_engine_name = self.search_engine,
                query = q,
                screenshot_dir = self.screenshot_dir
            )
            for q in self.queries
        ]
        logger.info(f"{len(self.workers)} Scraper-Worker für {self.search_engine} erzeugt.")

    def run_all(self):
        """
        Startet alle Scraper-Worker nacheinander und speichert die Ergebnisse als Liste.
        """
        results = []
        for worker in self.workers:
            html = worker.search()
            # Optional: weitere Verarbeitung/Parsing hier
            results.append(html)
            worker.quit()
        return results

# ==================== Beispielnutzung ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = {}  # Deine Konfiguration ggf. laden
    queries = ["site:python.org web scraping", "openai gpt", "selenium tutorials"]

    factory = ScrapeWorkerFactory(
        config=config,
        search_engine="google",
        queries=queries,
        screenshot_dir="./screenshots"
    )
    factory.create_workers()
    results = factory.run_all()
    logger.info(f"Scraping abgeschlossen. Ergebnisse pro Query: {len(results)}.")
