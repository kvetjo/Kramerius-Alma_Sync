import requests

#----------data------------

apikey = "" #insert api key

alma_host = "https://api-eu.hosted.exlibrisgroup.com/"
service_id_alma = "62491036000006986" 
electronic_collection_alma = 61491036010006986
note_restriction = "pokus ze 16/1/23"
pernament_url_kram = "https://kramerius.cuni.cz/uuid/uuid:" #URL to link the external repository
mms_id = 990001369460106986
uuid_id = "233dd9c5-c5d8-4d05-9886-e78d9ea7ab9d" #ID of document in external repository
material_type = "JOURNAL"

# #-----------code-------------
# #1st attempt
# #api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernament_url_kram) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(note_restriction), 'coverage_details': {'perpetual_date_coverage_parameters': [], 'perpetual_embargo_information': None, 'global_date_coverage_parameters': [], 'local_embargo_information': None, 'local_date_coverage_parameters': [{'until_month': {'desc': None, 'value': ''}, 'from_month': {'desc': None, 'value': ''}, 'until_issue': '', 'until_volume': '', 'from_volume': '', 'from_day': {'desc': None, 'value': ''}, 'from_year': '1913', 'from_issue': '', 'until_day': {'desc': None, 'value': ''}, 'until_year': '1914'}, {'until_month': {'desc': None, 'value': ''}, 'from_month': {'desc': None, 'value': ''}, 'until_issue': '', 'until_volume': '', 'from_volume': '', 'from_day': {'desc': None, 'value': ''}, 'from_year': '1915', 'from_issue': '', 'until_day': {'desc': None, 'value': ''}, 'until_year': '1916'}], 'coverage_in_use': {'desc': 'Only local', 'value': '0'}, 'global_embargo_information': None}}

# #2nd attempt
# #api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernament_url_kram) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(note_restriction)}

# #put--
# api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernament_url_kram) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(note_restriction), 'coverage_details': {'local_date_coverage_parameters': [{'from_year': '1913', 'until_year': '1914'}, {'from_year': '1915', 'until_year': '1916'}], 'coverage_in_use': {'desc': 'Only local', 'value': '0'}}}

# api = str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma) +"/e-services/"+ str(service_id_alma) +"/portfolios/53507107460006986?apikey=" + apikey + "&format=json"


# #api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios?apikey=" + apikey + "&format=json"

# #api_path = str(alma_host) + "almaws/v1/electronic/e-collections/61491036010006986?apikey=" + apikey + "&format=json"


# headers = {
#     'Content-Type': 'application/json',
#     }

# r = requests.put(api, headers=headers, json=api_body)
# #r = requests.put(api_path, headers=headers, json=api_body)
# print(r.status_code)
# print(r.content)
# vysledek = r.json()
# mms = vysledek["resource_metadata"]
# print(mms)


def api_vytvor_portfolio_pro_periodikum():

    #nejdřív vytvoř portfolio klasicky
    api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernament_url_kram) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(note_restriction)}
    api_path = str(alma_host) + "almaws/v1/bibs/" + str(mms_id) + "/portfolios?apikey=" + apikey + "&format=json"
    headers = {
    'Content-Type': 'application/json',
    }
    r = requests.post(api_path, headers=headers, json=api_body)
    print(r.status_code)
    print(r.content)
    vysledek = r.json()
    id_portfolia = vysledek["id"]
    print("id_portfolia", id_portfolia)
    #teď pomocí put vytvořené portfolio updatuj
    api_body = {'is_local':True,'is_standalone':False,'resource_metadata':{'mms_id':{'value':str(mms_id),'link':str(alma_host) + 'almaws/v1/bibs/'+str(mms_id)}}, 'electronic_collection':{'id':{'value':str(electronic_collection_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+str(service_id_alma)},'service':{'value':str(service_id_alma),'link':str(alma_host) + 'almaws/v1/electronic/e-collections/'+ str(electronic_collection_alma)+'/e-services/'+str(service_id_alma)}},'availability':{'value':'11','desc':'Available'},'material_type':{'value':str(material_type)},'linking_details':{'url':'','url_type':{'value':'static'},'url_type_override':{'value':'static'},'dynamic_url':'','dynamic_url_override':'','static_url':'','static_url_override':'jkey=' + str(pernament_url_kram) + str(uuid_id),'parser_parameters':'','parser_parameters_override':'','proxy_enabled':{'value':'false','desc':'No'},'proxy':''},'authentication_note':str(note_restriction), 'coverage_details': {'local_date_coverage_parameters': [{'from_year': '1913', 'until_year': '1914'}, {'from_year': '1915', 'until_year': '1916'}], 'coverage_in_use': {'desc': 'Only local', 'value': '0'}}}
    zjisti_id_portfolia = id_portfolia
    api = str(alma_host) + "almaws/v1/electronic/e-collections/"+ str(electronic_collection_alma) +"/e-services/"+ str(service_id_alma) +"/portfolios/"+ str(zjisti_id_portfolia) +"?apikey=" + apikey + "&format=json"

    r = requests.put(api, headers=headers, json=api_body)
    print(r.status_code)
    print(r.content)




api_vytvor_portfolio_pro_periodikum()