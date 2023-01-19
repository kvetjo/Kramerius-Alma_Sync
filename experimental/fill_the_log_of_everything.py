import json
import requests
import configparser
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
configFilePath = r"../portfolia.conf"
config.read(configFilePath)

zapnout_automaticky_import = config.get("obecne", "zapnout_automaticky_import")
zapnout_kontrolu_odstranenych = config.get("obecne", "zapnout_kontrolu_odstranenych")
pernamentni_url_krameria = config.get("obecne", "pernamentni_url_krameria") 
zakazane_modely = config.get("obecne", "ignorovat_tyto_modely")
oai_path = config.get("obecne", "oai_resolver")
kramerius_api_point = config.get("obecne", "kramerius_api_point") #https://kramerius.cuni.cz/search/api/v5.0
prefix_oai_id = config.get("obecne", "prefix_oai_identifier")

alma_host = config.get("alma", "alma_host")
apikey_alma = config.get("alma", "apikey")
service_id_alma = config.get("alma", "service_id")
electronic_collection_alma = config.get("alma", "electronic_collection_id")
poznamka_omezeni = config.get("alma", "poznamka_omezeni")
kontrola_existujiciho_portfolia = str(config.get("alma", "kontrola_existujiciho_portfolia")).lower()


def zpracovani_sysna_podminka(id_element):
    """na vstupu je hodnota vytažená z xml z oai. cilem je vložit hodnotu do správného formátu. Pokud te nejde nebo se nejedná o UKUK sysno, tak vrátí hodnotu 'zkontroluj' """
    str_id_element = str(id_element.string)
    if "CZ-PRCU" in str(id_element).upper():
        if str_id_element.startswith("99") and str_id_element.endswith("06986"):
            return str_id_element
        elif len(str_id_element) == 9:
            return "99" + str_id_element + "0106986"
        else:
            return "zkontroluj"

    else:
        return "zkontroluj"

def ziskej_mmsid(uuid):
  print(uuid)
  api_path = str(kramerius_api_point) + "/item/uuid:" + str(uuid) + "/streams/BIBLIO_MODS" #kramerius_api_point se bere z konfiguračního souboru
  r = requests.get(api_path)
  result = r.content.decode("utf-8") 
  #print(result)

  soup = BeautifulSoup(result, 'xml')
  
  id_element = soup.recordIdentifier
  #print(id_element)
  if id_element is None:
    #print("vracím: zkontroluj")
    return "zkontroluj"

  
  transformed_systemove_cislo = zpracovani_sysna_podminka(id_element)
  #print("transformed_systemove_cislo", str(transformed_systemove_cislo))
  return transformed_systemove_cislo


def get_just_used_models():
    """funkce vráti seznam modelů, které nejsou zakázané v configu. Tzn. vyfiltruje zakázané ze všech a ty použitelný pak zbydou"""

    list_of_all_models = ["graphic", "page", "map", "sheetmusic", "archive", "manuscript", 
        "monograph", "monographunit", "periodical", "periodicalvolume", 
        "periodicalitem", "soundrecording", "soundunit", "track", "internalpart", 
        "article", "collection", "convolute", "supplement", "sheetmusic"
        ]
    
    list_zakazane_modely = str(zakazane_modely).replace(" ", "").split(",") #tohle se získává z configu

    for model in list_zakazane_modely:
        list_of_all_models.remove(model)
    
    return list_of_all_models

def ziskej_seznam_vsech_dokumentu_v_krameriu():
    """
    Tato funkce má za cíl vytvořit aktuální seznam všech dokumentu dostupných v Krameriu.
    Cílem je získat pouze nadřazené UUID (rodičovské). Tento seznam dát na výstup v nějaké hezky zformátované verzi.
    Jako nástroj k tomuto úkonu je použitá Krameriovská API, která se dotazuje přímo SOLRu. Vypadá, že je to rychlejší než oaipmh.
    """
        
    seznam_modelu_se_kterymi_se_pracuje = get_just_used_models()


    #"fl" určuje to, co se má vypsat na výstup
    fl = "PID" #PID%20AND%20fedora.model
    q = ""
    for model in seznam_modelu_se_kterymi_se_pracuje:
        #zde se tvoří query, tedy vytváří se řetězec pouze s těmi modely, které opravdu chceme
        str_model = "fedora.model:%22" + str(model) + "%22"
        str_model = str_model + "%20OR%20"
        q += str_model
    q = q[:-len("%20OR%20")] #odstraňuji posledni OR --> má být pouze mezi, ne na konci..
    

    api_kram_solr = kramerius_api_point + "/search?fl=" + fl + "&q=" + q + "&wt=json&rows=250000"

    r = requests.get(api_kram_solr)
    result = r.content.decode("utf-8")
    json_result = json.loads(result)
    dataset_json = json_result["response"]["docs"]
    dataset_json_uuid_mmsid = {}
    i = 0
    for element in dataset_json:
            i += 1
            print(i)
            uuid = element["PID"].split(":")
            mms_id = ziskej_mmsid(str(uuid[1]))
            dataset_json_uuid_mmsid[uuid[1]] = mms_id


    dataset_json_uuid_mmsid = str(dataset_json_uuid_mmsid).replace("'", '"')
    with open('../important_logs/pokus_uuid_mmsid.json', 'w') as list_of_all_records_uuid:
        list_of_all_records_uuid.write(str(dataset_json_uuid_mmsid))

    #make_csv_from_simple_json(dataset_json)
    print(dataset_json_uuid_mmsid)

    
def odebrat_ze_souboru(co_k_odberu, cesta_k_souboru):
    with open('../important_logs/pokus_uuid_mmsid.json') as f:
        data = json.load(f)

    for element in co_k_odberu:
        data.pop(element, None)
    data_str = str(data).replace("'", '"')

    with open('../important_logs/pokus_uuid_mmsid.json','w') as f:
        f.write(data_str)

def pridat_do_soubor(co_k_pridani):
    #d['mynewkey'] = 'mynewvalue'
    pass

def read_json_file():
    with open('../important_logs/pokus_uuid_mmsid.json') as f:
        data = json.load(f)
    return data

def Merge(dict1, dict2):
    dict2.update(dict1)
    return dict2
 
# Driver code
dict1 = {'zzz': 10}
dict2 = {'c': 6, 'd': 4, "a":10}
 
# This returns None
ahoj = Merge(dict1, dict2)
 
# changes made in dict2
print(ahoj)





# data = read_json_file()
# list_data = list(data.keys())
# print(list_data)
#ziskej_seznam_vsech_dokumentu_v_krameriu()
# seznam = ["9472f48b-42b2-4fe6-9a36-b724f890dc15", "b7029327-4437-42ef-8017-e9ed464b301e", "a7bd4620-838d-4cc3-b936-6df88dfebcfc"]

# odebrat_ze_souboru(seznam, 9)
