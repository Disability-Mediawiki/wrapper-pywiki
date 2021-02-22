# application config
import configparser
config = configparser.ConfigParser()
config.read('config/application.config.ini')


mylang = "wikidata"
family = "wikidata"
# usernames['my']['my'] = u'Max'
# usernames['my']['my'] = u'DG Regio'
usernames['my']['my'] = u'WikibaseAdmin'
# usernames['my']['my'] = u''+config.get('wikibase','user')+''
password_file = "user-password.py"
minthrottle = 0
maxthrottle = 0
