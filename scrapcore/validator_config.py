# -*- coding: utf-8 -*-
from scrapcore.tools import ConfigurationError as Error


class ValidatorConfig:
    """Validates the configuration dictionary for the scraper."""

    def validate(self, config: dict):
        """Validate the provided configuration dictionary."""
        if not isinstance(config, dict):
            raise Error('Config is not a dict')

        if config.get('num_results_per_page', 0) > 10:
            raise Error('num_results_per_page must be lower than 10')

        valid_search_types = ['normal', 'video', 'news', 'image']
        if config.get('search_type') not in valid_search_types:
            raise Error(f"Invalid search type: {config.get('search_type')}")

        if not config.get('use_own_ip', False) and not config.get('proxy_file', ''):
            raise Error('No proxy_file provided and using own IP is disabled.')

        if config.get('scrape_method') not in ('selenium',):
            raise Error(f"No such scrape_method {config.get('scrape_method')}")

        if config.get('screenshot') is True:
            dir_screenshot = config.get('dir_screenshot')
            if not dir_screenshot or not isinstance(dir_screenshot, str) or len(dir_screenshot) < 1:
                raise Error('No config dir_screenshot found')
