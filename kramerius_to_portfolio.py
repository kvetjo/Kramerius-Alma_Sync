import requests
import json
from sickle import Sickle
from bs4 import BeautifulSoup
import smtplib
import configparser
from datetime import datetime
from datetime import timedelta

cesta_k_all_uuid_mmsid = "/opt/local/kramerius-alma/important_logs/all_uuid_mmsid.json"
cesta_k_last_import_datetime = "/opt/local/kramerius-alma/important_logs/last_import_datetime.txt"
config = configparser.ConfigParser()
configFilePath = r"/opt/local/kramerius-alma/portfolia.conf"
config.read(configFilePath)

zapnout_automaticky_import = config.get("obecne", "zapnout_automaticky_import")
zapnout_kontrolu_odstranenych = config.get("obecne", "zapnout_kontrolu_odstranenych")
pernamentni_url_krameria = config.get("kramerius", "pernamentni_url_krameria") 
zakazane_modely = config.get("obecne", "ignorovat_tyto_modely")
oai_path = config.get("kramerius", "oai_resolver")
kramerius_api_point = config.get("kramerius", "kramerius_api_point") #https://kramerius.cuni.cz/search/api/v5.0
prefix_oai_id = config.get("kramerius", "prefix_oai_identifier")

poslat_mail = config.get("email", "posilat_mail")
server_name_email = config.get("email", "server_name")
send_to_adress_email = config.get("email", "send_to_adress")
send_from_adress_email = config.get("email", "send_from_adress")
subject_email = config.get("email", "subject")

alma_host = config.get("alma", "alma_host")
apikey_alma = config.get("alma", "apikey")
service_id_alma = config.get("alma", "service_id")
electronic_collection_alma = config.get("alma", "electronic_collection_id")
poznamka_omezeni = config.get("alma", "poznamka_omezeni")
kontrola_existujiciho_portfolia = str(config.get("alma", "kontrola_existujiciho_portfolia")).lower()

#------------------------------confing----------------------------------
#mmsid = 990021814480106986  #Title: Rolník ve styku s úřady finančními
material_type = "BOOK"
#uuid_cislo = "3a1ea361-25f7-4e21-af23-3885ded09d35"
#-----------------------------------------------------------------------

#----------mail-------------
def send_email_to_alma_team(server, from_who, to_who, subject, msg):
    SERVER = str(server)
    FROM = str(from_who)
    TO = [str(to_who)] # must be a list

    SUBJECT = str(subject)
    TEXT = str(msg)

    # Prepare actual message
    message = """From: %s\r\nTo: %s\r\nSubject: %s\r\n\

    %s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)

    # Send the mail
    server = smtplib.SMTP(SERVER)
    #server.login("kvetjo", "")
    server.sendmail(FROM, TO, message)
    server.quit()
    print("---> e-mail s kontrolní dávkou byl odeslán na tuto adresu: " + str(to_who))


def odeslat_mail_podminka(obsah_mailu, mail_zapnuto=False):
    """Pokud nejsou žádné dokumenty k manuální opravě pošle se emailem jiná zpráva, než když jsou dokumenty k manuální opravě
    * hodnota mail_zapnuto se bere z configu a říká, jestli se má e-mail odeslat nebo nemá
    """
    
    if mail_zapnuto is True or mail_zapnuto == "True" or mail_zapnuto == "true":

        send_email_to_alma_team(server_name_email, send_from_adress_email, send_to_adress_email, subject_email, str(obsah_mailu))

    else:
        print("INFO: odesílání e-mailu bylo vypnuto v konfiguračním souboru")
#--------------------------------------------



#-------------odstraňování portfolií--------------
# def odstranit_portfolio(mms_id):
#     portfolio_id = get_portfolio_id(mms_id)
    
#     api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios/" + str(portfolio_id) + "?apikey=" + apikey_alma + "&format=json"
#     r =requests.delete(api_path)
#     print(r.status_code)

#     if str(r.status_code) == "204":
#         print("PORTFOLIO ODSTRANĚNO!")


def get_portfolio_id(mms_id):  
    api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios?apikey=" + apikey_alma + "&format=json"
    r = requests.get(api_path)
    vysledek = r.json()
    print(vysledek)
    collection = vysledek["portfolio"][0]["electronic_collection"]
    portfolio_id = vysledek["portfolio"][0]["id"]
    # print(json.dumps(vysledek, indent=2, sort_keys=True))
    return portfolio_id
#-------------------------------------------------------------



#------ funkce pro výpis jednoho portfolia------

def retrieve_portfolio(mms_id, portfolio_id="None"):
    """tato funkce vrátí JSON s portfoliem pro konkrétní dokument. 
    """
    if portfolio_id == "None":
        api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios" + "?apikey=" + apikey_alma + "&format=json"
    else:
        api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios/" + str(portfolio_id) + "?apikey=" + apikey_alma + "&format=json"
    # https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/990021814480106986/portfolios/53498176650006986?apikey=
    headers = {
        'Content-Type': 'application/json',
        }

    odpoved = requests.get(api_path, headers=headers)
    print(odpoved.status_code)
    print(odpoved.content)
    new_str = odpoved.content.decode()
    json_odpoved = json.loads(new_str)
    print(json_odpoved)
    #print(json_odpoved["portfolio"][0]["electronic_collection"]["id"]["value"])

    if portfolio_id == "None":
        print(json_odpoved["portfolio"])
        print("total_count_portfolios:", json_odpoved["total_record_count"])
        total_count = json_odpoved["total_record_count"]
        if total_count == 0:
            return None
        else:
            return json_odpoved["portfolio"]

    else:
        print(json_odpoved)
        return json_odpoved
#----------------------------------------------------------------
#json_object = retrieve_portfolio(990000581960106986)
# print(len(json_object))
# for element in json_object:
#     print(element["electronic_collection"]["id"]["value"])
#     print("-------")


#--------------vytvoř_portfolio-----------------
def vytvorit_portfolio(mms_id, uuid_cislo, material_type="BOOK", licence="policy:public"):

    #standalone True = bez kolekce
    #preparing_data = {"link": "https://kramerius.cuni.cz/uuid/uuid:3a1ea361-25f7-4e21-af23-3885ded09d35/","is_standalone": True, "availability": {"value": "11"}, "material_type": {"value": "BOOK"}, "authentication_note": "Ahoj Hanko!", "linking_details": { "url": "https://kramerius.cuni.cz/uuid/uuid:3a1ea361-25f7-4e21-af23-3885ded09d35/", "static_url" : "https://kramerius.cuni.cz/uuid/uuid:3a1ea361-25f7-4e21-af23-3885ded09d35/" }}

    #TOHLE FUNGUJE 
    
    if licence == "policy:private":
        preparing_data = {"is_local":True,"is_standalone":False,"resource_metadata":{"mms_id":{"value":str(mms_id),"link":str(alma_host) + "almaws/v1/bibs/"+str(mms_id)}}, "electronic_collection":{"id":{"value":str(electronic_collection_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+str(service_id_alma)},"service":{"value":str(service_id_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma)+"/e-services/"+str(service_id_alma)}},"availability":{"value":"11","desc":"Available"},"material_type":{"value":str(material_type)},"linking_details":{"url":"","url_type":{"value":"static"},"url_type_override":{"value":"static"},"dynamic_url":"","dynamic_url_override":"","static_url":"","static_url_override":"jkey=" + str(pernamentni_url_krameria) + str(uuid_cislo),"parser_parameters":"","parser_parameters_override":"","proxy_enabled":{"value":"false","desc":"No"},"proxy":""},"public_note":str(poznamka_omezeni)}
    if licence == "policy:public":
        preparing_data = {"is_local":True,"is_standalone":False,"resource_metadata":{"mms_id":{"value":str(mms_id),"link":str(alma_host) + "almaws/v1/bibs/"+str(mms_id)}}, "electronic_collection":{"id":{"value":str(electronic_collection_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+str(service_id_alma)},"service":{"value":str(service_id_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma)+"/e-services/"+str(service_id_alma)}},"availability":{"value":"11","desc":"Available"},"material_type":{"value":str(material_type)},"linking_details":{"url":"","url_type":{"value":"static"},"url_type_override":{"value":"static"},"dynamic_url":"","dynamic_url_override":"","static_url":"","static_url_override":"jkey=" + str(pernamentni_url_krameria) + str(uuid_cislo),"parser_parameters":"","parser_parameters_override":"","proxy_enabled":{"value":"false","desc":"No"},"proxy":""}}

 
    #fungují obě api_path - můžeš si vybrat
    api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios?apikey=" + apikey_alma + "&format=json"
    #api_path = str(alma_host) + "almaws/v1/electronic/e-collections/"+str(electronic_collection_alma)+"/e-services/"+ str(service_id_alma) +"/portfolios?apikey=" + apikey_alma + "&format=json"
    
        
    headers = {
        'Content-Type': 'application/json',
        }


    odpoved = requests.post(api_path, headers=headers, json=preparing_data)
    print(odpoved.status_code)
    print("odpoved.content---->")
    print(odpoved.content)
    vysledek = odpoved.json()
    id_portfolia = vysledek["id"]
    return str(odpoved.status_code), str(id_portfolia)
#----------------------------------------------------------



#-----------------získání_nových_dokumentů_v_Krameriovi---------------------

def change_log_last_import():
    """tato funkce přepíše imformaci v souboru ve složce 'last_import_datetime'. Tato informace slouží pro program k zapamatování si, který
    den naposledy dělal import do almy, díky čemu nastaví v příším importu nový datum na kdy má navázat.
    """
    now = datetime.now()
    #dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    date_string = now.strftime("%Y-%m-%d")

    with open(cesta_k_last_import_datetime, 'w') as f:
        f.write(str(date_string))

def get_date_from_log_last_import():
    """Tato funkce získá informaci z 'important_log.txt' ve složce '/last_import_datetime'. Tato informace je použita pro OAI resolver, kterému se nastaví 
    nová hodnota od kdy má sklízet (tzn. nebudou se sklízet již importované dokumenty)
    """
    f = open(cesta_k_last_import_datetime, "r")
    posledni_datum = f.read()
    f.close()

    return posledni_datum

def add_a_day_in_date(date_to_modify, how_many_to_add=1):
    """Tato funkce přidá den získanému datumu z logu. Tahle operace je potřeba pro navázání oai sklízení následujícím dnem."""
    Begindatestring = str(date_to_modify)  
    Begindate = datetime.strptime(Begindatestring, "%Y-%m-%d")
    middle_date = Begindate + timedelta(days=how_many_to_add)
    Enddate = middle_date.strftime("%Y-%m-%d")
    #Enddate = datetime.strptime(str(middle_date), "%Y-%m-%d")

    return Enddate

def ziskej_dokument_oai(uuid_dokumentu):
    sickle = Sickle(oai_path)
    print(str(prefix_oai_id)+uuid_dokumentu)
    record = sickle.GetRecord(metadataPrefix='oai_dc', identifier=str(prefix_oai_id)+"uuid:"+uuid_dokumentu)
    return record

def zjisti_nove_dokumenty(zadej_datum_od):
    """přes OAI sklízí identifikátory nově přidaných dokumentu. Datum od kdy má začít sklízet se specifikuje argumentem 'zadej_datum_od'. 
    Pracuje s cestou k OAI, která je specifikovaná v konfiguračním souboru.
    * pokud se do 'zadej_datum_od' zadá datum, vypíše pouze dokumenty, které byly přidané po tomto dni (formát: RRRR-MM-DD)
    * pokud se do 'zadej_datum_od' zadá klíčové slovo 'komplet', tak vypíše všechny dokumenty dostupné v krameriovi
    """
    #oai_path se bere z konfiguračního souboru
    sickle = Sickle(oai_path)
    list_zakazane_modely = str(zakazane_modely).replace(" ", "").split(",") #tohle se získává z configu

    if zadej_datum_od == "komplet":
        records = sickle.ListIdentifiers(metadataPrefix='oai_dc')
    else:
        try:
            records = sickle.ListIdentifiers(**{'metadataPrefix': 'oai_dc','from': str(zadej_datum_od)})
        except:
            #pokud bylo oaipmh prázdy, Sickle házel error
            records = []

    seznam_novych_dokumentu = []
    for r in records:
        
        model_of_document = ziskej_obsah_xml_elementu(r, "setSpec") #získá obsah elementu
        if model_of_document in list_zakazane_modely:
            #pokud narazí na model např: periodicalitem, periodicalvolume, supplement.. tak přeskakuje -> nebude v seznamu ke zpracování
            continue
        
        splitted = str(r).split("cz:uuid:")
        splitted_a = splitted[1]
        root_uuid = splitted_a[:36]
        seznam_novych_dokumentu.append(root_uuid)

    print("Počet dokumentu ke zpracovaní: " + str(len(seznam_novych_dokumentu)))
    return seznam_novych_dokumentu

def ziskej_obsah_xml_elementu(xml_soubor, nazev_elementu):
    """stringová operace - šetří čas že se vyhne parsování xmlka"""
    obsah_elementu = str(xml_soubor).partition("<"+ nazev_elementu + ">")[2].partition("</"+ nazev_elementu + ">")[0]
    return obsah_elementu

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

def roztridit_dictionary_do_dvou_dictionary(original_dictionary):
    dict1, dict2 = {}, {}
    for k,v in original_dictionary.items(): (dict1, dict2)["zkontroluj" in v][k] = v #tento řádek roztřídí hodnoty v původním dictionary do dvou nových dictionary (obsah ke kontrole/ručnímu nahrání a obsah k automatickému nahrání)

    return dict1, dict2

def vytvor_log_o_zpracovani(dictionary_k_importu, dictionary_k_oprave, chybne_importy, scenar, dict_chybnych_vysledku_odstraneni = "None", dict_for_check_to_delete = "None", dict_delete_from_alma = "None"):
    """Tato funkce má za úkol vytvořit soubor s informacemi ohledně dokumentů, kterým bylo vytvořeno automaticky portfolio a dokumentů, které bude potřeba 
    manuálně zkontrolovat. Log by se měl vytvářet pro každé spuštění do předem nastavené složky. 
    """
    pocet_k_importu = len(dictionary_k_importu)
    pocet_k_oprave = len(dictionary_k_oprave)
    pocet_spatne_provedenych_importu = len(chybne_importy)

    if dict_chybnych_vysledku_odstraneni == "None" and dict_for_check_to_delete == "None" and dict_delete_from_alma == "None":
        pocet_k_odstraneni = "Kontrola neprovedena"
        pocet_k_oprave_odstranovani = "Kontrola neprovedena"
        pocet_spatne_provedenych_odstraneni = "Kontrola neprovedena"
    else:
        pocet_k_odstraneni = len(dict_delete_from_alma)
        pocet_k_oprave_odstranovani = len(dict_for_check_to_delete)
        pocet_spatne_provedenych_odstraneni = len(dict_chybnych_vysledku_odstraneni)

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    date_string = now.strftime("%Y-%m-%d")
    
    obsah = "Datum a cas zpracovani: {}\n\
Pocet dokumentu k importu: {}\n\
Pocet dokumentu k oprave: {}\n\
Pocet spatne provedenych importu: {}\n\
----\n\
Pocet dokumentu k odstraneni: {}\n\
Pocet dokumentu pro rucni odstraneni: {}\n\
Pocet spatne provedenych API odstraneni: {}\n\
------------------------------\n\n\
Dokumenty k importu:\n{}\n\n\
Dokumenty k importu k rucni oprave:\n{}\n\n\
Chybne importy API:\n{}\n\n\
-------------------------------\n\n\
Dokumenty k odstraneni\n{}\n\n\
Dokumenty s nutnym rucnim odstranenim portfolia:\n{}\n\n\
Chybne odstranovani portfolii API:\n{}".format(str(dt_string),str(pocet_k_importu),str(pocet_k_oprave),str(pocet_spatne_provedenych_importu),str(pocet_k_odstraneni),str(pocet_k_oprave_odstranovani),str(pocet_spatne_provedenych_odstraneni),str(dictionary_k_importu),str(dictionary_k_oprave),str(chybne_importy), str(dict_delete_from_alma), str(dict_for_check_to_delete), str(dict_chybnych_vysledku_odstraneni))
#tohle výše je formátovanej string - na kraji bylo potřeba odstranit odsazení jinak to v souboru dělalo bordel :( 


    with open('portfolio_logs/log'+ str(date_string)+ '_' + str(scenar) +'.txt', 'a') as f:
        f.write(obsah)

    return obsah

def odstranit_portfolio(mms_id, portfolio_id="None"):
    """funkce maže portfolio ze záznamu v almě. K mazání konkrétního portfolia je potřeba zadat i portfolio_id. 
       Pokud portfolio_id není k dispozici, tak si ho program sám najde - smaže první jakékoliv krameriovské portfolio, které mu přijde pod ruku (ostatní nekrameriovská portfolia přeskakuje a neřeší)
    """
    
    if portfolio_id == "None":
        #portfolio_id = get_portfolio_id(mms_id)
        all_portfolios = retrieve_portfolio(mms_id)
        if all_portfolios is None:
            print("Nebylo nalezeno žádné existující porfolio pro dokument:", mms_id)
            return "portfolio_not_found"
        #pokud existuje více portfolií, tak každé z nich projde
        for portfolio in all_portfolios:
            kolekce_portfolia = portfolio["electronic_collection"]["id"]["value"]

            #hledá pouze krameriovská portfolia
            if str(kolekce_portfolia) == str(electronic_collection_alma):
                #bere první portfolio krameriovský na který narazí!
                portfolio_id = portfolio["id"]
                break
        

    api_path = "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/bibs/" + str(mms_id) + "/portfolios/" + str(portfolio_id) + "?apikey=" + str(apikey_alma) + "&format=json"
    r =requests.delete(api_path)
    print(r.status_code)
    if str(r.status_code) == "204":
        print("PORTFOLIO ODSTRANĚNO!")
        return True
    else:
        return False



def vytvorit_portfolio_podminka_kontrola(mms_id, uuid, licence, kontrola_existujiciho_portfolia="none", material_type="BOOK"):
    """tato funkce má za úkol provést kontrolu, jestli vytvářený portfolio již náhodou neexistuje. Výchozí nastavení této funkce je v configu v poli 'kontrola_existujiciho_portfolia'.
    Možné hodnoty pole kontrola_existujiciho_portfolia : none; overwrite_old, append_new, keep_old
    * none --> kontrola se vůbec neprovádí a portfolio se rovnou nahrává
    * overwrite_old --> pokud narazí na existující krameriovské portfolio, tak ho smaže a nahraje nové
    * append_new --> pokud narazí na existující krameriovské portfolio, tak na něj neseahá a k němu nahraje nové
    * keep_old --> pokud narazí na existující krameriovské portfolio, tak nic nenahrává a ponechává staré \n
    Uvědomil jsem si ex post, že 'none' a 'append_new' dělají vlastně stejnou věc :-)
    
    """
    #print("2 kontrola_existujiciho_portfolia:", "00"+kontrola_existujiciho_portfolia+"00")
    #kontroluje zdali je kontrola povolena když je nastaveno None, tak skáže k else kde prostě vytvoří portfolio
    if kontrola_existujiciho_portfolia != "none":
        print("mms_id:", mms_id)
        json_portfolii = retrieve_portfolio(mms_id)
        keep_old = False

        #kontroluje zdali existuje už nějaký portfolio, pokud žádné neexistuje, není co řešit a prostě ho vytvoří
        if json_portfolii is not None:
            #pokud existuje více portfolií, tak každé z nich projde
            for portfolio in json_portfolii:
                kolekce_portfolia = portfolio["electronic_collection"]["id"]["value"]
                id_portfolia = portfolio["id"]

                #hledá pouze krameriovská portfolia
                if str(kolekce_portfolia) == str(electronic_collection_alma):
                    #pokud se jedná o kolekci "Digitalní knihovna Kramerius" tzn. kramerius už má u této knihy odkaz přidaný..

                    if kontrola_existujiciho_portfolia == "overwrite_old":
                        #smazat starý
                        odstranit_portfolio(mms_id, id_portfolia)
                        print("odstranuji")

                    if kontrola_existujiciho_portfolia == "keep_old":
                        keep_old = True

        
        if keep_old is False:
            response = vytvorit_portfolio(mms_id, uuid, material_type=material_type, licence=licence)
            vysledek_vytvareni = response[0]
            id_vytvoreneho_portfolia  = response[1]
            return vysledek_vytvareni, id_vytvoreneho_portfolia
            
    else:
        print("INFO: kontrola již existujícího portfolia byla v konfiguračním souboru vypnuta")
        response = vytvorit_portfolio(mms_id, uuid, material_type=material_type, licence=licence)
        vysledek_vytvareni = response[0]
        id_vytvoreneho_portfolia  = response[1]
        return vysledek_vytvareni, id_vytvoreneho_portfolia

def vytvorit_portfolio_loop(dict_for_loop):
    """dictionary k importu prožene forcyklem a pro každý mmsid zavolá funkci na vytváření portfolia. Vrací dictionary s nepovedeným voláním"""
    dict_nepovedenych_importu = {}
    for key, value in dict_for_loop.items():
        #key -> uuid
        #value -> mms_id
        record = ziskej_dokument_oai(key)
        model_of_document = ziskej_obsah_xml_elementu(record, "setSpec") #zjišťuje typ dokumentu
        licence = ziskej_obsah_xml_elementu(record, "dc:rights.accessPolicy")
        print("DC licence:", licence)
        if model_of_document == "periodical":

            print("INFO: je to časopis")
            vysledek_vytvareni = import_periodik(value, key, licence)

        else:
            response = vytvorit_portfolio_podminka_kontrola(value, key, licence=licence, kontrola_existujiciho_portfolia=kontrola_existujiciho_portfolia)
            vysledek_vytvareni = response[0]

        if vysledek_vytvareni == "200":
            print(value + " ("+ key + ") tomuto dokumentu bylo přidáno portfolio.")
            print("------------------")
        else:

            dict_nepovedenych_importu[key] = [vysledek_vytvareni, value]
    
    return dict_nepovedenych_importu




#--------------------hledani_odstranenych_dokumentu-----------------------



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



def add_new_elements_to_dict(cesta_k_all_uuid_mmsid, novy_prirustky_json):
    """funkce aktualizuje json dokument o nové přírůstky v krameriovi. To je důležité především pro to, aby se dali sledovat následně i úbytky - kdyby byl z krameria odstraněn nějaký dokument"""
    with open(cesta_k_all_uuid_mmsid) as f:
        all_uuid_mmsid = json.load(f)

    all_uuid_mmsid.update(novy_prirustky_json)
    
    all_uuid_mmsid = str(all_uuid_mmsid).replace("'", '"')

    with open(cesta_k_all_uuid_mmsid,'w') as f:
        f.write(all_uuid_mmsid)
    
    print("INFO: byl updatován soubor 'all_uuid_mmsid.json' o nové přírůstky")

def ziskej_seznam_vsech_dokumentu_v_krameriu():
    """
    Tato funkce má za cíl vytvořit AKTUÁLNÍ seznam všech dokumentu dostupných v Krameriu.
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
    dataset_list_uuid = []

    for element in dataset_json:


            uuid = element["PID"].split(":")

            dataset_list_uuid.append(uuid[1])
    
    #dataset_list_uuid ==> aktuální objekty v Kramerius
    return dataset_list_uuid



def nacist_log_json_of_all_records_uuid():
    """
    tato funkce načítá dokumenty, které jsou zapsané v souboru 'all_uuid_mmsid.json'. Výstupem tak je původní stav, který se následně bude porovnávat 
    se stavem aktuálním. \n 
    výstup funkce je ve dvou formátek 1) uuid mmsid, 2) pouze uuid
    """

    with open(cesta_k_all_uuid_mmsid) as f:
        json_data_uuid_mms = json.load(f)
    
    list_data_uuid = list(json_data_uuid_mms.keys())

    return json_data_uuid_mms, list_data_uuid


def find_difference_in_uuid_lists(seznam_puvodni, seznam_ted_aktualizovany):
    """
    Pornová dva seznamy uuid a najde rozdíly. Umí zjistit nové přírůstky ale zároveň úbytky. \n
    Výstupem jsou:
    * missing uuid - dokumenty, které byly odstraněny
    * added uuid - dokumenty, které byly nově naimportovány
    """
    set1_puvodni = set(seznam_puvodni)
    set2_novy = set(seznam_ted_aktualizovany)

    missing = list(sorted(set1_puvodni - set2_novy))
    added = list(sorted(set2_novy - set1_puvodni))

    print('missing:', missing)
    # print('added:', added)
    
    return missing, added

def odebrat_ze_souboru(co_k_odberu, cesta_k_souboru):
    #'important_logs/all_uuid_mmsid.json'
    with open(cesta_k_souboru) as f:
        data = json.load(f)

    for element in co_k_odberu:
        data.pop(element, None)
        print("odebírám:", element)
    data_str = str(data).replace("'", '"')

    with open(cesta_k_souboru,'w') as file1:
        file1.write(data_str)


def odstraneni_portfolii_odstranenych_dokumentu():
    """
    Cílem této funkce je jednak sjednotit všechny kroky potřebné pro zjištění dokumentů, které byly odstraněny z Krameria. Dále pak těmto zjištěným dokumentu odstranit 
    portfolio i v Almě. \n
    Používá se pouze při inkrementálním importu. \n
    Výstupy funkce:
    * dict_chybnych_vysledku_odstraneni --> seznam dokumentů kde byl problém s odstraněním (API not 204)
    * seznam_uuid_k_rucnimu_odstraneni --> seznam dokumentů u kterých nebylo nalezené mms_id a bude potřeba provést odstranění ručně (například replikace)
    * seznam_odstranenych_mmsid --> dokumenty, které budou odstraněny
    """
    dict_chybnych_vysledku_odstraneni = {}
    #testovací listy..
    #seznam_puvodni = ['5c7f2aba-b4c9-11ec-862b-fa163e4ea95f', 'd6b1812a-b4c9-11ec-8f68-fa163e4ea95f', '7ac27950-b4c9-11ec-b2e0-fa163e4ea95f', 'efd4d770-bb99-11e2-b6da-005056827e52', 'eeec6070-283e-415f-b263-ceb01aa7c1b9']
    #seznam_novy = ['5c7f2aba-b4c9-11ec-862b-fa163e4ea95f', 'd6b1812a-b4c9-11ec-8f68-fa163e4ea95f', '7ac27950-b4c9-11ec-b2e0-fa163e4ea95f']
    #87d1a50c-995f-4251-b5df-0a49bb18f1b2
    objekt_puvodni = nacist_log_json_of_all_records_uuid() #načítá původní stav z posledního zjišťování
    seznam_puvodni = objekt_puvodni[1]
    json_puvodni = objekt_puvodni[0]

    seznam_novy = ziskej_seznam_vsech_dokumentu_v_krameriu() #zjišťuje aktuální stav
    
    #test
    #seznam_novy.remove("0d958e78-f1c3-11ea-b327-fa163e4ea95f")
    #seznam_novy.remove('80485eb0-85e2-411a-bf4a-94e62109e9b0')

    vystup = find_difference_in_uuid_lists(seznam_puvodni, seznam_novy)
    print("vystup:")
    print(vystup[0])
    uuid_odstraneny = vystup[0]


    seznam_odstranenych_uuid = []
    seznam_odstranenych_mmsid = []
    seznam_uuid_k_rucnimu_odstraneni = []

    for uuid in uuid_odstraneny:
        odstraneny_mms = json_puvodni[uuid]

        if odstraneny_mms == "zkontroluj":
            seznam_uuid_k_rucnimu_odstraneni.append(uuid)
        else:
            seznam_odstranenych_mmsid.append(odstraneny_mms)
            seznam_odstranenych_uuid.append(uuid)
            #REAL THING
            povedlo_se_odstranit = odstranit_portfolio(odstraneny_mms)
            if str(povedlo_se_odstranit) == "False" or str(povedlo_se_odstranit) == "portfolio_not_found":
                dict_chybnych_vysledku_odstraneni[odstraneny_mms] = "Deleted:" + str(povedlo_se_odstranit)

        #odstranit link v Almě
    print("seznam_odstranenych_mmsid", uuid_odstraneny)
    odebrat_ze_souboru(uuid_odstraneny, cesta_k_all_uuid_mmsid) #tato funkce maže záznamy, které z krameria zmizely, z "all_uuid_mmsid.json"


    #dict_chybnych_vysledku_odstraneni --> seznam dokumentů kde byl problém s odstraněním (API not 204)
    #seznam_uuid_k_rucnimu_odstraneni --> seznam dokumentů u kterých nebylo nalezené mms_id a bude potřeba provést odstranění ručně (například replikace)
    #seznam_odstranenych_mmsid --> dokumenty, které budou odstraněny
    return dict_chybnych_vysledku_odstraneni, seznam_uuid_k_rucnimu_odstraneni, seznam_odstranenych_mmsid

    


#odstraneni_portfolii_odstranenych_dokumentu()






#-------------------------------------------------------------------------

#---------------------periodika---------------------------
def children_of_periodical_document(uuid_periodika):
    """vytvoří list jednotlivých ročníků časopisu. Doptává se na to Krameriovský API"""
    seznam_rocniku = []
    api_path = str(kramerius_api_point) + "/item/uuid:" + str(uuid_periodika) + "/children" #kramerius_api_point se bere z konfiguračního souboru
    r = requests.get(api_path)
    result = r.content.decode("utf-8") 
    json_children = json.loads(result)
    for kid in json_children:
        year = kid["details"]["year"]
        try:
            if "-" in year:
                ys = year.split("-")
                seznam_rocniku.extend(ys)
            else:
                seznam_rocniku.append(year)
        except:
            continue
        
    return seznam_rocniku

def zpracuj_rocniky_periodika(seznam_rocniku):
    """po veškeré provedené transformaci dat vrátí na výstup data OD roku - DO roku v následujícím formátu (př.:)
    * list v listu: [[1861, 1861], [1863, 1872], [1874, 1888], [1894, 1913]]
    """
    seznam_rocniku = list(map(int, seznam_rocniku))
    seznam_rocniku = sorted(seznam_rocniku)

    a = []
    complet_a = []
    start = min(seznam_rocniku)
    end = max(seznam_rocniku)
    for rok in range(start, end+1):
    #řeší to i duplicity :-)
        if rok in seznam_rocniku:
            a.append(rok)

            if rok == end:
                complet_a.append(a)
        else:
            if not a:
                #pokud je "a" prázdné
                pass
            else:
                complet_a.append(a)
                a = []
    rozsahy_pokryti = transformace_pokryti_od_do(complet_a)
    return rozsahy_pokryti

def transformace_pokryti_od_do(seznam_seznamu):
    seznam_rozsahu = []
    for rozsah in seznam_seznamu:
        zacatek = min(rozsah)
        konec = max(rozsah)
        rozsah = [zacatek, konec]
        seznam_rozsahu.append(rozsah)

    #VYSTUP list v listu: [[1861, 1861], [1863, 1872], [1874, 1888], [1894, 1913]] 
    return seznam_rozsahu

def prepis_pokryti_do_JSON(rozsah_pokryti_list):
    """tato funkce umí z výstpu funkce 'zpracuj_rocniky_periodika' vytvořit JSON, který se vloží do 'body' pro API POST volání. Tzn na výstupu této funkce je JSON s coverage_details
    * format pro VSTUP př.: [[1861, 1861], [1863, 1872], [1874, 1888], [1894, 1913]]  --> list listů
    """
    
    seznam_jsonu_pokryti = []
    for jeden_rozsah in rozsah_pokryti_list:
        print(jeden_rozsah)
        dostupne_od_kdy = str(jeden_rozsah[0])
        dostupne_do_kdy = str(jeden_rozsah[1])
        local_date_coverage_parameters = '{"from_year":"SEM_ZADEJ_OD","from_month":{"value":"","desc":null},"from_day":{"value":"","desc":null},"from_volume":"","from_issue":"","until_year":"SEM_ZADEJ_DO","until_month":{"value":"","desc":null},"until_day":{"value":"","desc":null},"until_volume":"","until_issue":""}'
        local_date_coverage_parameters = local_date_coverage_parameters.replace("SEM_ZADEJ_OD", dostupne_od_kdy)
        local_date_coverage_parameters = local_date_coverage_parameters.replace("SEM_ZADEJ_DO", dostupne_do_kdy)

        seznam_jsonu_pokryti.append(local_date_coverage_parameters)
    template ='{"coverage_in_use":{"value":"0","desc":"Only local"},"global_date_coverage_parameters":[],"local_date_coverage_parameters":SEM_ZADEJ_POLE_S_DOSTUPNOSTI,"perpetual_date_coverage_parameters":[],"global_embargo_information":null,"local_embargo_information":null,"perpetual_embargo_information":null}'
    
    coverage_dostupnost_pole = str(seznam_jsonu_pokryti).replace("'", "")

    prepared_template = template.replace("SEM_ZADEJ_POLE_S_DOSTUPNOSTI", coverage_dostupnost_pole)

    print(prepared_template)
    return prepared_template
    

def import_periodik(mms_id, uuid_periodika, licence):
    """tato funkce hledá jednotlivé ročníky dostupné v krameriovi daného periodika a tuto informaci následně podsouvá další funkci na import periodik, kterou sama volá"""
    print("INFO: Budu importovat periodikum. Hledání ročníků...")
    childrens = children_of_periodical_document(uuid_periodika)
    pokryti = zpracuj_rocniky_periodika(childrens)
    a = prepis_pokryti_do_JSON(pokryti)
    #jedná se pouze o část z API body - část s názvem "coverage_details". Tzn. tato část se musí pak vložit do celku. To se provádí ve funkci "api_vytvor_portfolio_pro_periodikum"
    dict_json = json.loads(a)
    print(dict_json)

    vysledek_vytvareni = api_vytvor_portfolio_pro_periodikum(mms_id, uuid_periodika, licence, dict_json)
    
    return vysledek_vytvareni
   
    


def api_vytvor_portfolio_pro_periodikum(mms_id, uuid_id, licence, coverage_details_data):
    """k importu periodik se musí přistupovat odlišně oproti monografiím. U periodik je nutné nejdříve vytvořit klasicky portfolio pomocí metody POST a následně doplnit tomuto portfoliu ročníky pomocí metody PUT"""         

    response = vytvorit_portfolio_podminka_kontrola(mms_id, uuid_id, licence=licence, kontrola_existujiciho_portfolia=kontrola_existujiciho_portfolia, material_type="JOURNAL")
    vysledek_vytvareni = str(response[0])
 
    if vysledek_vytvareni != "200":
        return vysledek_vytvareni
    zjisti_id_portfolia = response[1]
    

    #teď pomocí put vytvořené portfolio updatuj
    headers = {
    'Content-Type': 'application/json',
    }

    if licence == "policy:private":
        api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernamentni_url_krameria) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(poznamka_omezeni)}
    if licence == "policy:public":
        api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernamentni_url_krameria) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''}}

    
    api_body["coverage_details"] = coverage_details_data
    print("api_body")
    print(api_body)
    api = str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma) +"/e-services/"+ str(service_id_alma) +"/portfolios/"+ str(zjisti_id_portfolia) +"?apikey=" + apikey_alma + "&format=json"

    r = requests.put(api, headers=headers, json=api_body)
    print("výsledek aktualizace ročníků", str(r.status_code))
    print(r.content)
    return str(r.status_code)
#---------------------------------------------------------
#api_vytvor_portfolio_pro_periodikum("990001369460106986", "233dd9c5-c5d8-4d05-9886-e78d9ea7ab9d", "policy:private")
#import_periodik("990016809170106986", "396f6243-c1f8-4b19-a467-afa08f5090c2", "policy:public")

# childrens = children_of_periodical_document("cf34828d-b0d3-4a10-9d52-4ea14fff4716")
# #childrens = [1861, 1862, 1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870, 1871, 1872, 1873, 1874, 1875, 1876, 1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885, 1886, 1887, 1888, 1889, 1890, 1891, 1892, 1893, 1894, 1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913]
# childrens = [1861, 1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870, 1871, 1872, 1874, 1875, 1876, 1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885, 1886, 1887, 1888, 1894, 1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913]

# pokryti = zpracuj_rocniky_periodika(childrens)
# print(pokryti)
# a = prepis_pokryti_do_JSON(pokryti)
# dict_json = json.loads(a)
# print(type(dict_json))
# # print(dict_json)

# preparing_data = {"is_local":True,"is_standalone":False,"resource_metadata":{"mms_id":{"value":str(8989),"link":str(alma_host) + "almaws/v1/bibs/"+str(555)}}, "electronic_collection":{"id":{"value":str(electronic_collection_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+str(service_id_alma)},"service":{"value":str(service_id_alma),"link":str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma)+"/e-services/"+str(service_id_alma)}},"availability":{"value":"11","desc":"Available"},"material_type":{"value":str(material_type)},"linking_details":{"url":"","url_type":{"value":"static"},"url_type_override":{"value":"static"},"dynamic_url":"","dynamic_url_override":"","static_url":"","static_url_override":"jkey=" + str(pernamentni_url_krameria) + str("uuid777_cislo"),"parser_parameters":"","parser_parameters_override":"","proxy_enabled":{"value":"false","desc":"No"},"proxy":""},"authentication_note":str(poznamka_omezeni)}
# preparing_data["coverage_details"] = dict_json
# print(preparing_data)



#-------------------scénáře importů-----------------------
def inkrementalni_import(zapnuto):
    """Tento typ importu sleduje nově přidané dokumenty do Krameria, které pak následně importuje do Almy jako portfolio k záznamům. 
    Tento import by měl být dostupný nonstop. Využívá ho pak linux démon CRON. Informace o datumu posledního importu se ukládají do složky 'last_import_datetime' (výchozí informace pro skript).
    Detailní informace o průběhu importu se pak ukládají do složky 'portfolio_logs' (s touto složkou skript pak už nijak dál nepracuje, slouží jako info pro lidi)
    * argument 'zapnuto' slouží k tomu, že pokud bude nastavený CRON démon, i přesto je možné v configu vypnout automatické importování (tzn. buď je možné vypnout celý CRON nebo stačí v configu změnit hodnotu na False)
    """
    if zapnuto is False or zapnuto == "False" or zapnuto == "false":
        zprava = "INFO: import neproběhl, v konfiguračním souboru je automatické importování vypnuto."
        print(zprava)
        return zprava

    posledni_datum = get_date_from_log_last_import()
    sklizeni_od_datum = add_a_day_in_date(posledni_datum)
    print(sklizeni_od_datum)

    if str(zapnout_kontrolu_odstranenych) == "True" or str(zapnout_kontrolu_odstranenych) == "true":
        print("INFO: kontrola odstraněných zapnuta")
        dict_chybnych_vysledku_odstraneni, dict_for_check_to_delete, dict_delete_from_alma = odstraneni_portfolii_odstranenych_dokumentu()
    else:
        print("INFO: kontrola odstraněných vypnuta")
        dict_chybnych_vysledku_odstraneni = "None"
        dict_for_check_to_delete = "None"
        dict_delete_from_alma = "None"

        print("INFO: kontrola pro odstraněný dokumenty z Krameria byla vypnuta v konfiguračním souboru")

    #zadej_datum_od = "2022-10-17" #RRRR-MM-DD
    seznam_novych_dokumentu = zjisti_nove_dokumenty(sklizeni_od_datum)
    print(seznam_novych_dokumentu)
    list_mmsid = list(map(ziskej_mmsid, seznam_novych_dokumentu)) #aplikuje funkci "ziskej_mmsid" na každý prvek v seznamu "seznam_novych_dokumentu" /tzn. vytvoří list mmsid na základě uuid
    dict_uuid_sysno_complet = dict(map(lambda i,j : (i,j) , seznam_novych_dokumentu, list_mmsid)) #vytváří dictionary ze dvou listů (určuje se na základě pořadí v listu)


    add_new_elements_to_dict(cesta_k_all_uuid_mmsid, dict_uuid_sysno_complet)

    dict_import_into_alma, dict_for_check = roztridit_dictionary_do_dvou_dictionary(dict_uuid_sysno_complet)

    chybne_importy = vytvorit_portfolio_loop(dict_import_into_alma)
    #chybne_importy = ["ahoj","test"]

    change_log_last_import()
    obsah_logu = vytvor_log_o_zpracovani(dict_import_into_alma, dict_for_check, chybne_importy, "inkrementalni", dict_chybnych_vysledku_odstraneni, dict_for_check_to_delete, dict_delete_from_alma)

    odeslat_mail_podminka(obsah_logu, poslat_mail)

    print("dict_import_into_alma:")
    print(dict_import_into_alma) #s tímto dictionary se bude pracovat pro automatické nahrávání 
    print()
    print("dict_for_check:")
    print(dict_for_check) #replikace a chybné dokumenty k nahrání do almy ručně



def full_import_komplet():
    """Tento typ importu má za úkol vytvořit portfolio kompletně všem dokumentům v Krameriovi najednou. Pouštět s rozmyslem ;-) bude to trvat dlouho..
    Přeskakuje replikace a další zvláštní dokumenty.. ty pak vypíše do logu nebo pošle e-mailem.
    """

    seznam_novych_dokumentu = zjisti_nove_dokumenty("komplet")

    list_mmsid = list(map(ziskej_mmsid, seznam_novych_dokumentu)) #aplikuje funkci "ziskej_mmsid" na každý prvek v seznamu "seznam_novych_dokumentu" /tzn. vytvoří list mmsid na základě uuid
    dict_uuid_sysno_complet = dict(map(lambda i,j : (i,j) , seznam_novych_dokumentu, list_mmsid)) #vytváří dictionary ze dvou listů (určuje se na základě pořadí v listu)


    dict_import_into_alma, dict_for_check = roztridit_dictionary_do_dvou_dictionary(dict_uuid_sysno_complet)

    #chybne_importy = vytvorit_portfolio_loop(dict_import_into_alma)
    chybne_importy = ["a", "ab"]
    obsah_logu = vytvor_log_o_zpracovani(dict_import_into_alma, dict_for_check, chybne_importy, "komplet")
    odeslat_mail_podminka(obsah_logu, poslat_mail)

    print("dict_import_into_alma:")
    print(dict_import_into_alma) #s tímto dictionary se bude pracovat pro automatické nahrávání 
    print()
    print("dict_for_check:")
    print(dict_for_check) #replikace a chybné dokumenty k nahrání do almy ručně



def specificky_import(dokumenty_k_importu):
    """Tento import se pokusí naimportovat portfolio pouze vybraným dokumentům, které se dodají v listu nebo dictionary. To kde list nebo dictionary seženeš záleží na tobě.
    * formát list --> ['9856f934-13db-11ed-90ce-fa163e4ea95f', '5993851d-c99c-4aad-a3d0-526973b64118', ...]  --> uuid
    * formát dict --> {'da965d3e-59f2-47ef-a3a6-bc129f598e64': '9925646109406986', 'e3ee7cf0-17c5-447e-a2cc-510a9ff96f39': '990005583860106986'} --> uuid:mms_id
    """

    if type(dokumenty_k_importu) is list:
        list_mmsid = list(map(ziskej_mmsid, dokumenty_k_importu)) #aplikuje funkci "ziskej_mmsid" na každý prvek v seznamu "seznam_novych_dokumentu" /tzn. vytvoří list mmsid na základě uuid
        dict_uuid_sysno_complet = dict(map(lambda i,j : (i,j) , dokumenty_k_importu, list_mmsid)) #vytváří dictionary ze dvou listů (určuje se na základě pořadí v listu)
    elif type(dokumenty_k_importu) is dict:
        dict_uuid_sysno_complet = dokumenty_k_importu
    else:
        print("WARNING: objekt nemá správný typ, průchod je umožněn pouze listu a dictionary; tvůj objekt je:", type(dokumenty_k_importu))
        return "WARNING: objekt nemá správný typ, průchod je umožněn pouze listu a dictionary"
    
    

    dict_import_into_alma, dict_for_check = roztridit_dictionary_do_dvou_dictionary(dict_uuid_sysno_complet)

    chybne_importy = vytvorit_portfolio_loop(dict_import_into_alma)
    #chybne_importy = ["ahoj","test"]

    obsah_logu = vytvor_log_o_zpracovani(dict_import_into_alma, dict_for_check, chybne_importy, "vyberova")

    odeslat_mail_podminka(obsah_logu, poslat_mail)

    print("dict_import_into_alma:")
    print(dict_import_into_alma) #s tímto dictionary se bude pracovat pro automatické nahrávání 
    print()
    print("dict_for_check:")
    print(dict_for_check)




#specificky_import(['9856f934-13db-11ed-90ce-fa163e4ea95f', '5993851d-c99c-4aad-a3d0-526973b64118', '86f16399-0ba1-424f-a6bc-a7fd4b2d5c1c', '7e0098a5-2b3a-44de-8b08-b145c24820de'])
inkrementalni_import(zapnout_automaticky_import)
#odstranit_portfolio(990023128400106986)
#full_import_komplet()
#odstraneni_portfolii_odstranenych_dokumentu()
#specificky_import(["413a0ac3-8c8c-4d50-885f-51c46ffe2de3"]) #časopis #Karolinka

#specificky_import(["3a1ea361-25f7-4e21-af23-3885ded09d35"]) #časopis #Karolinka
#json_object = retrieve_portfolio(990000581960106986) #990021814480106986
#print(json_object)
#Český evanjelík
#vysledek_vytvareni = vytvorit_portfolio(990001368840106986, "ee6e9013-4286-4be7-90c8-bd48f787151b", "JOURNAL", [1861, 1863, 1864, 1865, 1867, 1868], licence="policy:public")
#odstranit_portfolio(990001368840106986)


#vysledek_vytvareni = vytvorit_portfolio(990000581960106986, "10a54419-863c-4b9d-9575-fa9da7180b46", "BOOK", licence="policy:private")

#retrieve_portfolio(990001369460106986, 53505106710006986) #Evangelické hlasy
#retrieve_portfolio(990003905670106986, 53505106730006986) #Method


#specificky_import(["10a54419-863c-4b9d-9575-fa9da7180b46", "d4a3483e-8c3e-4c21-8686-2475e745a686", "91e2d4cc-659c-440e-8783-bf581ac63645"])


#------------------------------------POZNÁMKY--------------------------------------
#DONE - vytvořit jednotící funkci pro ten bordel nahoře
#DONE - navázat 'sklizeni_od_datum' do procesu 
#DONE - navázat již hotové funkce zasílání e-mailu do procesu
#DONE - vytvořit nastavování pro hodnotu v configu 'zapnout_automaticky_import' a vložit do workflow
#DONE - navázat funkce vytváření portfolií do workflow
#DONE - vytvořit různé scénáře pracování s tímto programem
    #1) inkrementální import (pouze pro nové dokumenty, jednou za čas samo) - DONE
    #2) full import komplet všeho - DONE (ale otestuj)
    #3) import pouze specifických dokumentů (asi ruční výběr čeho? Do nějakého listu? Nebo do Souboru?) 
#DONE - bude potřeba upravit hlášku o přístupnosti, aby se zobrazovala jen v případě, že dokument je v režimu private
#DONE - kontrola, jestli náhodou portfolio na Krameria už nebylo vytvořený, pokud ano nastavovat a) přepsat b) doplnit c) přeskočit 
#DONE - Hanka chce posílat komplet log do emailu


#TODO - FSV, 1LF :-(

#-------------periodika------------
#TODO - vyřešit problematiku periodik - čeká se na vyjádření ALMA týmu
    #TODO - jak aktualizovat stav periodik?
    #TODO asi by bylo vhodné udělat vedle druhý program, který bude kontrolovat !pouze! přírůsky nových periodik. Tzn. dotaz na oaipmh set pro periodicvolume a pomocí PUT api nějak aktualizovat coverage
    # ale nevím.. musí se vyřešit aby se to nepřekrývalo -> když vytvořím nové cele periodikum.. periodicvolumes budou také vidět v set oai pro periodika.. no a pak se to bude tlouct
#---------------------------------- 
#TODO možná - specifikovat více detailně chyby v dictionary pro kontrolu (tzn. místo "zkontroluj" tam dát třeba "replikace" nebo jiná chyba)


#TODO - vymyslet způsob jak se postavit k tomu, když bude dokument odstraněný. 
    #využití kramerius API pro SOLR query
    #vracet seznam všech dokumentů (pouze hlavní úroveň)
    #příklad SOLR query: https://kramerius.cuni.cz/search/api/v5.0/search?fl=PID&q=collection:%22vc:145f935a-972f-4f62-9ae5-dec88717bcf9%22%20AND%20fedora.model:%22monograph%22&rows=500&wt=json
    #příklad SOLR query: https://kramerius.cuni.cz/search/api/v5.0/search?fl=PID&q=fedora.model:%22map%22&wt=json&rows=40000
        #budu mít dva seznamy: 
            #starý
            #nový
        #cílem bude porovnávání rozdílů - bude se hledat to, co je ve starým ale není v novým. 
        #výsledný rozdíl ?asi uložím do souboru vedle?, se kterým se následně bude pracovat.
        #zavolá se API call na ALMU, aby odstranila pouze krameriovský portfolio
        #zapíše seznam odstraněných někom do logu
    #otázky? - dělat to skrze prostředníka tzn. soubor? 

#vytvorit_portfolio(mmsid)
#odstranit_portfolio(mmsid)


