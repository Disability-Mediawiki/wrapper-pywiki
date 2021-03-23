import pywikibot

# SITE LINK https://www.wikidata.org/wiki/Wikidata:Pywikibot_-_Python_3_Tutorial/Setting_sitelinks
site = pywikibot.Site("test", "wikidata")
repo = site.data_repository()
item = pywikibot.ItemPage(repo, "Q210194")
sitedict = {'site':'enwiki', 'title':'Douglas Adams'}
item.setSitelink(sitedict, summary=u'Setting (/updating?) sitelink.')



#DISCLAIMER! This adds sitelink to wikidata.org, not the test site!
site = pywikibot.Site("en", "wikipedia")
repo = site.data_repository()
item = pywikibot.ItemPage(repo, u"Q42")
page = pywikibot.Page(site, u"Douglas Adams")
item.setSitelink(page, summary=u'Setting (/updating?) sitelink.')

# SITE LINK