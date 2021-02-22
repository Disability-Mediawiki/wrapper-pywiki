import base64
import json
import os
import sys
import time
import re
import boto3
import requests
import pandas as pd
import uuid
import base64
from botocore.exceptions import ClientError
from google.cloud import translate_v2 as gt


s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
secret_client = boto3.client('secretsmanager')


google_credentials = json.loads(secret_client.get_secret_value(SecretId="google_credentials")["SecretString"])
with open("/tmp/google_credentials.json", "w") as json_file:
    json.dump(google_credentials, json_file)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/tmp/google_credentials.json"


# Detecting loop in translations : more than 4 characters repeated at least 4 times
LOOP = re.compile(r"(.{4,})\1\1")

class TranslatorClient():

    def __init__(self):

        client = boto3.client('sts')
        account_id = client.get_caller_identity()["Account"]
        if account_id == "294118183257":
            environment = "cnect-prime"
        elif account_id == "799253154846":
            environment = "cnect-prod"
        else:
            raise Exception("The AWS environment is not connected")

        
        self.environment = environment

        credentials = self.load_credentials()
        self.etranslation_user = credentials["user"]
        self.etranslation_pwd = credentials["password"]
        
        self.http_destinations={
            "cnect-prime": "https://x6415xgkgb.execute-api.eu-west-1.amazonaws.com/prod/",
            "cnect-prod": "https://e5hd14xd95.execute-api.eu-central-1.amazonaws.com/prod/"
        }
        self.translation_bucket = {
            "cnect-prime": "doris-etranslation-bucket",
            "cnect-prod": "etranslation-bucket"
        }

        self.google_translate_client = gt.Client()

    def load_credentials(self, region_name="eu-central-1"):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        try:
            return json.loads(client.get_secret_value(
                SecretId="etranslation_api"
            )["SecretString"])
        except:
            raise Exception("eTranslation credentials not found")

    def is_looping_text(self, text):
        match = LOOP.search(text)
        if match is not None and " " in match.group(1):
            return match.group(1)
        return None

    def translate_with_google(self, text):
        translation = self.google_translate_client.translate(text, target_language="en")
        return translation["translatedText"]
        

    def translate_dataframe(self, dataframe, source_language):
        
        url = 'https://webgate.ec.europa.eu/etranslation/si/translate'
        headers = {'content-type': 'application/json'}

        temp_file_name = f"/tmp/{uuid.uuid4()}.xlsx"
        dataframe.to_excel(temp_file_name, index=False, header=None)
        content = base64.b64encode(open(temp_file_name, "rb").read()).decode("utf-8")
        os.remove(temp_file_name)

        body = {
            'priority': 0,
            'externalReference' : 123,
            'callerInformation' : {
                'application' : 'DORIS_CNECT20151014',
                'username' : 'DorisMTService'
            },
            "documentToTranslateBase64": {
                "content":  content,
                "format": "xlsx",
            },
            'sourceLanguage' : source_language,
            'targetLanguages' : ['EN'],
            'domain' : 'GEN',
            'destinations' : {
                "httpDestinations": [self.http_destinations[self.environment]]
            }
        }

        response = requests.post(url, data=json.dumps(body), headers=headers, auth=requests.auth.HTTPDigestAuth(self.etranslation_user, self.etranslation_pwd))
        try:
            response_id = int(response.text)
        except:
            print("eTranslation failed")
            return None

        if response_id < 0:
            print(f"eTranslation failed with following code: {response_id}")
            return None
       
        translated = None
        while not translated:
            try:
                s3_client.download_file(self.translation_bucket[self.environment], str(response_id), str(response_id))
                translated=True
            except Exception as e:
                time.sleep(1)
    
        
        translation = pd.read_excel(str(response_id), header=None)
        
        # Detect failed translations (loops) and resend to Google Translate
        for i, entry in enumerate(translation.values.tolist()):
            if len(entry[2]) > 4000 and self.is_looping_text(entry[2]) is not None:
                try:
                    google_translation = self.translate_with_google(dataframe.loc[i, 2])
                    translation.loc[i, 2] = google_translation
                except:
                    pass

        s3.Object(self.translation_bucket[self.environment], str(response_id)).delete()
        os.remove(str(response_id))

        return translation


if __name__ == "__main__":

    client = TranslatorClient()

    df = pd.DataFrame([
        ["Q42", "SUMMARY", "Ceci est un test"],
        ["Q2476446", "SUMMARY", "Nos bureaux sont ouverts tous les jours de 8h à 12h30 et de 14h à 18h Quatre personnes pour vous accueillir : Emilie Maillot chargée de l’accueil et assistante administrative- elle est remplacée actuellement par Claudine Meletta Catherine CHARLERY directrice, évaluatrice à Agen, Nérac (le mardi toute la journée , au centre Haussmann) et Aiguillon (le jeudi) Delphine Le Parc évaluatrice à Agen Graziella Griso évaluatrice à Agen et prochainement à Marmande Patricia Klein, évaluatrice sur l'antenne de Villeneuve **SYLLABE** reçoit toute personne désireuse de vérifier ou valider ses compétences en français ou plus généralement en savoirs de base afin de pouvoir s’orienter plus facilement dans sa recherche d’emploi ou dans sa formation à visée professionnelle. **_Comment le public vient-il à SYLLABE_** _?_ * spontanément * suite à une orientation faite par une structure d’accueil : Pôle emploi, Cap Emploi, Mission Locale, PLIE, CMS, CCAS, Agence de Travail Temporaire, Structures de l’ IAE, entreprise, etc. **_Pourquoi venir ?_** * Parce qu’on ne maîtrise pas suffisamment les compétences clé, que l’on ait été scolarisé ou non, en France ou à l’étranger. Vont être alors considérées plusieurs typologies de publics : * les personnes scolarisées en France seront dites * Illettrées si elles maîtrisent très insuffisamment les compétences de base * « Remise à Niveau » si elles maîtrisent insuffisamment les compétences clé au regard de leur objectif * les personnes scolarisées dans leur pays d’origine seront dites : * analphabètes si elles n’ont suivi aucune scolarité (ou une scolarité de moins de 3 ans) * FLE (Français Langue Etrangère) si elles ont suivi une scolarité plus ou moins longue dans leur pays) * FLS (Français Langue de Scolarisation) si elles ont appris le français **_Que s’y passe-t-il ?_** * un entretien d’accueil permettant un pré repérage du niveau de communication * une évaluation des compétences en langue française / compétences clés liées ou non à un objectif précis d’insertion professionnelle (emploi direct ou formation qualifiante) * un bilan de cette évaluation avec si nécessaire et si possible une orientation en formation avec prise de rendez-vous avec le centre de formation correspondant (professionnels) ou une association de bénévoles * l’orientation vers telle ou telle formation est présentée à la personne et à la structure prescriptrice (cela est rendu possible par la connaissance pratiquement au jour le jour des offres de formations) * le bilan est adressé au prescripteur et au centre de formation **_et puis :_** * la personne est revue à la fin de la formation (ou pendant si nécessaire) pour une nouvelle évaluation afin de mesurer les évolutions et organiser une suite de parcours. Chaque parcours est propre à la personne, « taillé sur mesure » .. ** _jusqu’à ce que le parcours s’achève_** _Accueil, évaluation, positionnement, orientation et suivi des parcours de formation:_ Dès la création de Syllabe, des chartes de partenariat ont été signées avec d'un côté les prescripteurs ( Pôle emploi, Mission Locale, Plie, CMS, structures de l'IAE, CCAS etc) et de l'autre les organismes de formation (professionnels et bénévoles) proposant de la formation aux savoirs de base, compétences clés. Dès lors, toute personne qui souhaite s'engager dans un tel parcours de formation doit au préalable venir à SYLLABE afin d'y vérifier ses compétences et leur adéquation avec le projet professionnel retenu. Une évaluatrice la reçoit et lui propose divers exercices liés à des référentiels de compétences afin de vérifier les quatre compétences de langue (compréhensions et productions écrite et orale), les capacités mathématiques, de raisonnement logique ainsi que les capacités liées à la bureautique de base. \- Un bilan est rédigé, \- un positionnement est effectué à l'aide de différents référentiels en lien avec la typologie de la personne ( nous utilisons ainsi le CECR - cadre européen commun de référence pour les langues- et le référentiel des compétences en situation professionnelle de l'ANLCI -Agence Nationale de Lutte contre l'Illettrisme-) \- une orientation en formation est proposée en lien avec la typologie de la personne, son niveau, son projet. \- le lien est fait à la fois avec le prescripteur et l'organisme de formation choisi. Parfois le parcours de formation sera constitué d'un assemblage de plusieurs interventions. Le positionnement et l’orientation en formation sont validés par la personne concernée et aussi par son « prescripteur ». Notre accompagnement / suivi de parcours s’arrête lorsque la personne atteint le niveau de compétences linguistique ou compétences clés qui correspond à son objectif. **En fonction du profil de la personne, nous l'orientons vers des parcours proposés par les organismes de formation ayant remporté les appels d'offres de la Région, de l'OFII ou de la DDCSPP, de l'ACSÉ.** **En complément de ces p"],    
        ["Q19", "SUMMARY", "Le chien est dans la cuisine"]
    ])
    
    print(client.translate_dataframe(df, "fr"))
