Skript 'kramerius-to-portfolio.py' vznikl v rámci projektu, který má za cíl automaticky synchronizovat obsah Krameria s Almou. Konkrétně je jeho cílem přidávat 
e-portfolia (tzn. odkazy) k bibliografickým záznamům tak, aby dokumenty, které byly naimportovány do Krameria měla v Almě odkaz na Krameria.


Celý projekt se skládá z několika složek a skriptu a congigu:
-------------------------------------------------------------
složka "important_logs" --> zde jsou logy, které jsou důležité pro script samotný. Bez nich nebude správně fungovat
        last_import_datetime.txt --> zde je uložen datum posledního proběhlého importu. Díky tomu je script schopný navazovat na předešlé importy. 
        all_uuid_mmsid.json --> zde jsou uloženy identifikátory všech dokumentů, které jsou dostupné v krameriovi (krom těch co jsou specifikovány v configu k ingnorování..). To je důležité pro sledování odstraněných dokumentů.
složka "portfolio_logs" --> zde jsou logy které jsou užitečné pro uživatele/lidi - skript s nimi nepracuje, jen je generuje. Jsou zde základní informace i proběhlých importech.
složka "experimental" --> zde není nic důležitého, jen zkušební skriptíky. 

konfigurační soubor portfolia.conf:
    - zde se provádějí základní nastavení celého běhu skriptu. Snaha byla zde specifikovat proměnné, které by se mohly v budoucnu změnit nebo by bylo potřeba je přepsat
    z důvodu nasazení skriptu na ostatní kramerie (FSV, 1LF). 
    
    Důležité pole:
        * zapnout_automaticky_import      --> v případě, že je nastavený démon CRON, tak automatický import se provádí podle nastavení zde (True: zapnuto; False: vypnuto)
        * zapnout_kontrolu_odstranenych   --> toto nastavení řeší zda se mají v Almě odstranovat portfolia dokumentům, které byly v Krameriovi smazány
        * ignorovat_tyto_modely           --> zde je výčet modelů, se kterými se nemá pracovat.
        * posilat_mail                    --> zde se zapíná služba, která rozesílá emailem logy o zpracování (stejné co jsou v "portfolio_logs"). Adresa kam je specifikována níže. Testoval jsem více adres najednou a moc to nefugnovalo :-(
        * kontrola_existujiciho_portfolia --> toto pole může nabývat 4 hodnoty (none; overwrite_old, append_new, keep_old) - nastavuje jak má přistupovat k tomu, když v záznamu potká už existující portfolio.
            * none --> kontrola se vůbec neprovádí a portfolio se rovnou nahrává
            * overwrite_old --> pokud narazí na existující krameriovské portfolio, tak ho smaže a nahraje nové
            * append_new --> pokud narazí na existující krameriovské portfolio, tak na něj neseahá a k němu nahraje nové
            * keep_old --> pokud narazí na existující krameriovské portfolio, tak nic nenahrává a ponechává staré 
            Uvědomil jsem si ex post, že 'none' a 'append_new' dělají vlastně stejnou věc :-)
        * electronic_collection_id        --> zde je identifikátor krameriovské kolekce -- ná základě něho se zjišťuje, jestli v záznamu už existuje portfolio na krameria
        * poznamka_omezeni                --> textová informace, která se objeví u e-portfolia v případě, že je dokument v Krameriu vede jako "private"


Script "kramerius_to_portfolio.py":
    skript má 3 metody spuštění, výběr metody se provádí zakomentováním/odkomentováním volání příslušné funkce přímo v kódu:
        - full_import_komplet()
        - inkrementalni_import(zapnuto)
        - specificky_import(dokumenty_k_importu)

full_import_komplet()
- cílem této metody je projet celého krameria a pro každý dostupný dokument vytvořit v Almě portfolio
- cílem tedy je první nalití informací do Almy
- problém je ale v tom, že to bude trvat relativně dlouho. Pro tuto potřebu jsou preferovány jiné metody, které má na starosti Hanka z EIZ. 

inkremetalni_import(zapnuto)
- tato metoda počítá s tím, že script bude pravidelně spouštěn na pozadí pomocí CRONu. Informace o tom jak spustit CRON viz dole
- každé spuštění, přes OAI-PMH, kontroluje nové přírůstky, které pak následně naimportuje jako eportfolio do ALMY.
- tato metoda umí i hlídat odstraněné dokumenty z Krameria, kterým pak portfolio maže z ALMY
- vstupní argument "zapnuto" se automaticky bere z konfiguračního souboru

specificky_import(dokumenty_k_importu)
- Tento import se pokusí naimportovat portfolio pouze vybraným dokumentům, které se dodají v listu nebo dictionary. To kde list nebo dictionary seženeš záleží na tobě.
- vstupní argument "dokumenty_k_importu" může být typu list anebo i dictionary. Příklady jak má vypadat vstup:
    * formát list --> ['9856f934-13db-11ed-90ce-fa163e4ea95f', '5993851d-c99c-4aad-a3d0-526973b64118', ...]  --> uuid
    * formát dict --> {'da965d3e-59f2-47ef-a3a6-bc129f598e64': '9925646109406986', 'e3ee7cf0-17c5-447e-a2cc-510a9ff96f39': '990005583860106986'} --> uuid:mms_id




------------------------------------------------------------------------------------------------------------------------------------------------

JAK SPUSTIT CRON JOB:
skript musí mít dobře nastavené práva --> chmod -R 777
příkaz v shellu: "crontab -e" --> otevře soubor, ve kterým se specifikují CRON úlohy
    Do tohoto souboru přidej následující řádky:
        1. řádek "SHELL=/bin/bash"      #bez uvozovek... řekne cronu, že má automaticky pracovat s jazykem bash
        2. řádek "* * * * * source /opt/local/dt2psp/bin/activate && source /opt/local/dt2psp/set_pythonpath.sh && /opt/local/dt2psp/bin/python3 /opt/local/kramerius-alma/experimental/cron_print.py >> /opt/local/kramerius-alma/experimental/cron.out"
            tento řádek spustí virtualenv a pak skript. * * * * * ->specifikují kdy se bude skript pouštět (https://crontab.guru/#*_*_*_*_*)
            >> /opt/local/kramerius-alma/experimental/cron.out  ----> specifikuje kde bude uložený to co jde na print

--------------------------------------------------------------------------------------------------------------------------------------------------



