===========
Result Data
===========

The result is returned as list of dictionaries like the example below.
If url_scrape is enabled it may contain an additional property.
If you prefer to save the results use the as_csv() method.

.. code-block:: python

   {
    'query': 'example',
    'query_num_results total': 'Ungefähr 1.740.000.000 Ergebnisse (0,50 '
                               'Sekunden)\xa0',
    'query_num_results_page': 10,
    'query_page_number': 1,
    'related_keywords': [{'keyword': 'example deutsch', 'rank': 1},
                         {'keyword': 'example email', 'rank': 2},
                         {'keyword': 'example definition', 'rank': 3},
                         {'keyword': 'example rapper', 'rank': 4},
    'serp_domain': 'dictionary.cambridge.org',
    'serp_rank': 4,
    'serp_rating': None,
    'serp_sitelinks': None,
    'serp_snippet': 'example Bedeutung, Definition example: something that is '
                    'typical of the group of things that it is a member of: .',
    'serp_title': 'example Bedeutung im Cambridge Englisch Wörterbuch',
    'serp_type': 'results',
    'serp_url': 'http://dictionary.cambridge.org/de/worterbuch/englisch/example',
    'serp_visible_link': 'dictionary.cambridge.org/de/worterbuch/englisch/example'
   }
