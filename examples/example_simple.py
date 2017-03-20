import serpscrap
import pprint

keywords = ['python tutorials']
scrap = serpscrap.SerpScrap()
scrap.init(keywords=keywords)
result = scrap.scrap_serps()

pprint.pprint(result)
