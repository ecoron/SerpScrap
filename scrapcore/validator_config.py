# -*- coding: utf-8 -*-
from scrapcore.tools import ConfigurationError as Error


class ValidatorConfig():

    def validate(self, config):

        if not isinstance(config, dict):
            raise Error('config is not a dict')

        if config.get('num_results_per_page') > 100:
            raise Error('num_results_per_page must be lower then 100')

        valid_search_types = ['normal', 'video', 'news', 'image']
        if config.get('search_type') not in valid_search_types:
            raise Error('Invalid search type!')

        if config.get('use_own_ip') != True and len(config.get('proxy_file')) == 0:
            raise Error('No proxy_file provided and using own IP is disabled.')

        if config.get('scrape_method') not in ('selenium'):
            raise Error('No such scrape_method {}'.format(config.get('scrape_method')))

        if config.get('screenshot') is True and \
            (config.get('dir_screenshot') is None or
             len(config.get('dir_screenshot')) < 1):
            raise Error('No config dir_screenshot found')