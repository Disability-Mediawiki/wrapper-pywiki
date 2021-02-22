"""Testing the eTranslation module"""

import etranslation as et
translate_client = et.Client()

message = "Le rapide renard brun saute au-dessus du chien fainéant"
language = "FR"
translation = translate_client.translate(message, source_language=language, format_='txt')
print(translation)
