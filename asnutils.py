# TODO Interpretar los archivos json y poder extraer datos
# TODO Reutilizar los parseCisco y parseMRT en los chequeos de IXP
# TODO Generar los graficos
# TODO Armar una funcion que arme carpetas si estas no existen
# TODO Armar una funcion que agrupe archivos json y temporales en muchas subcarpetas por los limites de los filesystems

__author__="Ariel Weher y Matias Comba"
__date__ ="$Sep 1, 2014 7:39:33 AM$"

import ConfigParser
import json
import simplejson
import pprint
import os
import urllib2
import csv
import re
import time
from StringIO import StringIO
import gzip

def colorprint(color,txt):
    colores={
        'default':'',
        'amarillo': '\x1b[01;33m',
        'azul': '\x1b[01;34m',
        'cian': '\x1b[01;36m',
        'verde': '\x1b[01;32m',
        'rojo': '\x1b[01;31m'
    }
    print colores[color]+txt+'\x1b[00m'

def generar_reporte_global(CONFIG,force=False):
    """ Genera reportes de todos los ASN y links de la tabla mundial"""
    if (force == False):
        generar = False
    else:
        generar = True
# Veo si existen los archivos preprocesados y los leo
    if (os.path.isfile(CONFIG['tmp_folder']+"RPT_ASNsGlobal") and os.path.isfile(CONFIG['tmp_folder']+"RPT_LinksGlobal")):
        if ((os.stat(CONFIG['tmp_folder']+"RPT_ASNsGlobal").st_size > 0) and (os.stat(CONFIG['tmp_folder']+"RPT_LinksGlobal").st_size > 0)):
            f=open(CONFIG['tmp_folder']+"RPT_ASNsGlobal",'r')
            ASNsGlobales=eval(f.readline())
            f=open(CONFIG['tmp_folder']+"RPT_LinksGlobal",'r')
            LinksGlobales=eval(f.readline())
        else:
            generar = True
    else:
        generar = True
            
    if (generar==True):
        [ASNsGlobales,LinksGlobales]=make_asn_links(CONFIG['feed_dir']+CONFIG['tabla_mundial'])
        f=open(CONFIG['tmp_folder']+"RPT_ASNsGlobal",'w')
        f.write(repr(ASNsGlobales))
        f=open(CONFIG['tmp_folder']+"RPT_LinksGlobal",'w')
        f.write(repr(LinksGlobales))
    
    print("\nReporte de la tabla mundial")
    print ("Cantidad de ASN's en el archivo "+CONFIG['tabla_mundial']+":"+str(len(ASNsGlobales)))
    print ("Cantidad de Links en el archivo "+CONFIG['tabla_mundial']+":"+str(len(LinksGlobales)))
    return 
    
def generar_reporte_pais(CONFIG,PAIS):    
    """De la lista Global de Links genera: ASNs de borde, Upstream de cada AS, Links dentro de un pais """
    f=open(CONFIG['tmp_folder']+"RPT_ASNsGlobal",'r')
    ASNsGlobales=eval(f.readline())
    f=open(CONFIG['tmp_folder']+"RPT_LinksGlobal",'r')
    LinksGlobales=eval(f.readline())
    
    Upstream={"":[]}
    ASNs_BORDER=list()
    Links_Pais=list()
    
    [DicRIR,DicAS]=make_asn_pais(str(CONFIG['feed_dir']+'delegated-'+find_rir_by_country(CONFIG,PAIS).lower()+'-latest'))
    
    for links in LinksGlobales:
        as0,sp,as1=links.partition(",")
        if as1 in Upstream:
            Upstream[as1]|={as0}
        else:
            Upstream[as1]={as0}
            
        if ((as0 in DicRIR[PAIS]) or (as1 in DicRIR[PAIS])):
            ASNs_BORDER+=[as0,as1]
            Links_Pais+=[links]
        
    f=open(CONFIG['tmp_folder']+"RPT_ASNs_"+PAIS+"_BORDER","w")
    f.write(repr(ASNs_BORDER))
    f=open(CONFIG['tmp_folder']+"RPT_Links_bgp-ixp-"+PAIS,"w")
    f.write(repr(Links_Pais))
    
    PaisGL = DicRIR[PAIS] & ASNsGlobales
    
    print ("Cantidad de ASNs de "+PAIS+" en el archivo "+CONFIG['tabla_mundial']+": "+str(len(PaisGL)))
    f=open(CONFIG['tmp_folder']+"RPT_ASNs_"+PAIS+"_"+CONFIG['tabla_mundial'],'w')
    f.write(repr(PaisGL))
    
def download(url,file,mode='w'):
    """ Descarga un archivo y lo guarda en un path """
    opener = urllib2.build_opener()
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print e.code
        print e.read() 
    else:
        w=open(file,mode)

    try:
        ### NEEDS FIX ###
        if response.info().get('Content-Encoding') == 'gzip':
#            print('Usando GZIP para '+file)
            buf = StringIO( response.read())
            f = gzip.GzipFile(fileobj=buf)
            data = f.read().rstrip()
        else:
            data = response.read()
        w.write(data)
    except OSError as e:
        print(e)
        response.close()
        w.close()

def olderthan(file,ttl=86400*7):
    """ Chequea la fecha de modificacion de un archivo """
    try:
        statinfo = os.stat(file) 
        if (statinfo.st_size>10):
            modificado=time.gmtime(statinfo.st_mtime)
            ahora=time.gmtime()
            resta = (time.mktime(ahora) - time.mktime(modificado))
            segundos=int(resta)
            if(segundos > ttl):
                return True
            else:
                return False
    except OSError as e:
        print('No puedo abrir el archivo '+file)
        return True

def parse_asn_rir(CONFIG):
    asn16csv = 'http://www.iana.org/assignments/as-numbers/as-numbers-1.csv'
    asn32csv = 'http://www.iana.org/assignments/as-numbers/as-numbers-2.csv'
    feed = CONFIG['tabla_asn_iana']
    try:
        statinfo = os.stat(feed) 
        if (statinfo.st_size>100):
            if (olderthan(feed,CONFIG['feed_ttl'])):
#               print('El archivo '+feed+' tiene mas de '+CONFIG['feed_ttl']+' segundos desde su creacion, lo bajo de nuevo')
                os.remove(feed)
                for url in [asn16csv,asn32csv]:
                    download(url,feed,'a')
#            else:
#                print('El archivo '+feed+' tiene '+str(int(dias))+' dias, lo conservo')
    except OSError as e:
#        print('No puedo abrir el archivo '+feed+', lo creo')
        for url in [asn16csv,asn32csv]:
            download(url,feed,'a')
    
    with open(feed, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        dicasn = {0:""}
        for row in reader:
            colasn=row[0].rstrip()
            colrir=row[1].rstrip()
            colwhois=row[2].rstrip()
            
            if not (re.match('Assigned',colrir)):
                continue
            
            if (re.match('^[0-9]+',colasn)):
                ix=0
                if(re.match('[0-9]+-',colasn)):
                    inicio,sep,fin = colasn.partition('-')
                    for ix in range (int(inicio),int(fin)+1):
                        dicasn[ix]=colrir[12:]
                else:
                    dicasn[colasn]=colrir[12:]
                    
        with open(CONFIG['tabla_asn_json'], 'wb') as fp:
            json.dump(dicasn, fp)
    
def generar_reporte_ixp(CONFIG,PAIS,RecursosRIR):
    HTML_IN_1=CONFIG['htmli_folder']+'header.html'
    HTML_IN_2=CONFIG['htmli_folder']+'footer.html'
    print("\nReporte de "+PAIS)
    BGPIXP='bgp-ixp-'+PAIS
        
    [pais_ASNs,ASNpais]=make_asn_pais(RecursosRIR['LACNIC'])
    f=open(CONFIG['tmp_folder']+"RPT_Dict_RIR",'w')
    f.write(repr(pais_ASNs))
    f.close()
    f=open(CONFIG['tmp_folder']+"RPT_Dict_AS",'w')
    f.write(repr(ASNpais))
    f.close()
   
    [ASNsIXP,LinksIXP] = make_asn_links(CONFIG['feed_dir']+BGPIXP)
    print ("Cantidad de ASNs en "+BGPIXP+": "+str(len(ASNsIXP)))
    print ("Cantidad de Links en "+BGPIXP+": "+str(len(LinksIXP)))
    
    f=open(CONFIG['tmp_folder']+'asnsixp-'+PAIS+'.txt','w')
    f.write(repr(ASNsIXP))
    f.close()
    
    InterseccionAS = dict()
            
    for ctry in pais_ASNs.keys():
        # Obtenemos la interseccion entre los ASN's que un pais publica
        # en la tabla global y los que estan en el IXP
        InterseccionAS[ctry]=pais_ASNs[ctry] & ASNsIXP
                        
        if len(InterseccionAS[ctry]) > 0:
            print("Cantidad de ASN's de "+str(ctry)+" en el archivo "+str(BGPIXP)+": "+str(len(InterseccionAS[ctry])))
    
        f=open(CONFIG['tmp_folder']+"RPT_ASNs_"+PAIS+"_"+BGPIXP,'w')
        f.write(repr(InterseccionAS[ctry]))
        f=open(CONFIG['tmp_folder']+"RPT_Links_"+PAIS+"_"+BGPIXP,'w')
        f.write(repr(LinksIXP))

def is_asn32(asnumber):
    if(is_asdot(asnumber)):
        return True
        
    if(int(asnumber) > 65535):
        return True
    else: 
        return False
    
def is_asdot(asnumber):
    if (str(asnumber).find('.')):
        return True
    else:
        return False
    
def convert_to_asplain(asnumber):
    if(is_asn32(asnumber) == True):
        if (is_asdot(asnumber)):
            asdot = str(asnumber)
            region,resto = asdot.split('.')
            return int(region) * 65536 + int(resto)
        else:
            return asnumber
    else:
        return asnumber

def convert_to_asdot(asnumber):
    if(is_asn32(asnumber)):
        region = int(asnumber) // 65536
        resto = int(asnumber) % 65536
        return str(str(region)+"."+str(resto))
    else:
        return False
    
def find_rir_by_asn(CONFIG,asnumber):
    """ Encuentra a que RIR hay que hacer la consulta de RDAP
        de acuerdo el numero de sistema autonomo de la clase """
    reservados=[0,23456]
    if asnumber in reservados:
        return 'SPECIAL'
    with open(CONFIG['tabla_asn_json'], 'rb') as archivo:
        data = json.load(archivo)
        return (data[asnumber])

def find_rir_by_country(CONFIG,country):
    """ [TODO] Devuelve el nombre del RIR que atiende a un pais determinado """
    RIRs = ['ARIN','RIPENCC','APNIC','LACNIC','AFRINIC']
    
    for rir in RIRs:
        # TODO
        # 1 abrir delegaciones
        # 2 procesar buscando Pais
        # 3 devolver resultados unicos
        next
    return 'LACNIC'

def update_data(url,file,ttl=86400*7):
    if olderthan(file,ttl):
        print('El archivo '+file+' tiene mas que los '+str(ttl)+' segundos requeridos.')
        print('Descargando '+file+'...')
        download(url,file,'w')
        return True
    else:
        return False
    
def make_asn_pais(archivo):
    """Arma dos Diccionarios [pais:{ASNs}] y [ASN:pais] desde el archivo de
    delegaciones de un RIR"""
    ListaDeASNdelPais={"":{}}
    PaisDelASN={0:""}
    with open(archivo) as rirfile:
        for line in rirfile:
            # lacnic|AR|ipv4|200.3.168.0|2048|20051007|allocated
            # lacnic|MX|asn|278|1|19890331|allocated
            [lacnic,CountryCode,tipo,asnumber,long,fecha]=line.split("|",5)
            if tipo != "asn":
                continue
            elif CountryCode in ListaDeASNdelPais:
                ListaDeASNdelPais[CountryCode].add(asnumber)
            else:
                ListaDeASNdelPais.update({CountryCode:{asnumber}})
            PaisDelASN[asnumber]=CountryCode
    del(ListaDeASNdelPais[""])
    return([ListaDeASNdelPais,PaisDelASN])

def make_asn_links(bgpdump):
    """[NEEDFIX] Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    try:
        fileinfo=os.stat(bgpdump)
    except OSError as e:
        print('Error al acceder al archivo '+bgpdump+': '+str(e))
        return False
    
    dumptype = ribtype(bgpdump)
    
    if (dumptype == 'cisco'):
        ListaASNs,ListaLinks = parseCisco(bgpdump)
        
    if (dumptype == 'mrt'):
        ListaASNs,ListaLinks = parseMRT(bgpdump)
    
    return([set(ListaASNs), set(ListaLinks)])

def rdapwhois(CONFIG,ASNs):
    cachedir=CONFIG['json_folder']
    RDAPurl = dict()
    RDAPurl['LACNIC'] = 'http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/'
    RDAPurl['RIPENCC'] = 'http://rest.db.ripe.net/search.json?query-string=as'
    RDAPurl['ARIN'] = 'http://whois.arin.net/rest/asn/AS'
    RDAPurl['AFRINIC'] = 'http://rest.db.ripe.net/search.json?query-string=as' #el de ripe parece que sirve
    RDAPurl['APNIC'] = RDAPurl['RIPENCC'] # Todavia no esta implementada la busqueda de ASN, solo IPs: http://www.apnic.net/apnic-info/whois_search/about/rdap
    RDAP404=set()
    DatosWHOIS=dict()
    
    try:
        fileinfo=os.stat(cachedir)
    except OSError as e:
        os.mkdir(cachedir)
    
    for asn in ASNs:
        rir=find_rir_by_asn(CONFIG,asn)
        if (rir == 'SPECIAL'):
            next
        if (not RDAPurl[rir.upper()]):
            print('No hay informacion de servidor RDAP para el RIR: '+rir)
            return
        url=RDAPurl[rir]+str(asn)
        archivo=cachedir+str(asn)+'.json'
        
        try:
            statinfo=os.stat(archivo)
            if(statinfo.st_size>1000):
                w=open(archivo,'r')
                try:
                    DatosWHOIS[asn]=json.loads(w.read())
                except ValueError, e:
                    print('Error en el archivo '+archivo+': ',e)
                continue
        except OSError as e:
            elerror=e
            
    
    try:
        request = urllib2.Request(url, headers={'Accept': 'application/json'})
        f = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        RDAP404.add(asn)
    else:
        w=open(archivo,'w')
        DatosWHOIS[asn]=f.read()
        try:
            w.write(DatosWHOIS[asn])
        except OSError as e:
            print('Error en el archivo '+archivo+': ',e)
        f.close()
        w.close()
    
    if (len(RDAP404) > 0):
        print('Se encontraron errores en las consultas RDAP para los siguientes ASNs:'+str(RDAP404))
        
    return(DatosWHOIS)

def whois(CONFIG,ASNs,rir):
    cachedir=CONFIG['json_folder']
    RDAPurl = dict()
    RDAPurl['LACNIC'] = 'http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/'
    RDAPurl['RIPENCC'] = 'http://rest.db.ripe.net/search.json?query-string=as'
    RDAPurl['ARIN'] = 'http://whois.arin.net/rest/asn/AS'
    RDAPurl['AFRINIC'] = 'http://rest.db.ripe.net/search.json?query-string=as' #el de ripe parece que sirve
    RDAPurl['APNIC'] = RDAPurl['RIPENCC'] # Todavia no esta implementada la busqueda de ASN, solo IPs: http://www.apnic.net/apnic-info/whois_search/about/rdap
    RDAP404=set()
    DatosWHOIS=dict()
    
    try:
        fileinfo=os.stat(cachedir)
    except OSError as e:
        os.mkdir(cachedir)
    
    for asn in ASNs:        
        if (not RDAPurl[rir.upper()]):
            print('No hay informacion de servidor RDAP para el RIR: '+rir)
            return
        url=RDAPurl[rir]+str(asn)
        archivo=cachedir+str(asn)+'.json'
        
        try:
            statinfo=os.stat(archivo)
            if(statinfo.st_size>1000):
                w=open(archivo,'r')
                try:
                    DatosWHOIS[asn]=json.loads(w.read())
                except ValueError, e:
                    print('Error en el archivo '+archivo+': ',e)
                continue
        except OSError as e:
            print('No puedo acceder al archivo: '+archivo+', lo consulto.')
            time.sleep(1)
    
    try:
        request = urllib2.Request(url, headers={'Accept': 'application/json'})
        f = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        RDAP404.add(asn)
    else:
        w=open(archivo,'w')
        DatosWHOIS[asn]=f.read()
        try:
            w.write(DatosWHOIS[asn])
        except OSError as e:
            print('Error en el archivo '+archivo+': ',e)
        f.close()
        w.close()
    
    if (len(RDAP404) > 0):
        print('Se encontraron errores en las consultas RDAP en el RIR '+rir+' para los siguientes ASNs:'+str(RDAP404))
        
    return(DatosWHOIS)

def actualizar_feeds(CONFIG):
    """Actualiza los feeds de informacion desde sitios publicos de internet"""
    print('Verificando si hay archivos para descargar...')
    print("\t  * Delegaciones de los RIR")
    rehacer = True #False
    listadodeasn=set()
    for rir in ['arin','ripencc','apnic','lacnic','afrinic']:
        url=CONFIG['deleg_'+rir+'_url']
        archivo=CONFIG['deleg_'+rir]
        if (update_data(url,archivo,CONFIG['feed_ttl'])):
            rehacer = True
            
    if (rehacer == True):
            try:
                statinfo = os.path.isfile(CONFIG['main_feed'])
                if (statinfo):
                    os.remove(CONFIG['main_feed'])
            except IOError as e:
                print ('Error al acceder el archivo: '+CONFIG['main_feed']+': '+e)
                
#            mainfeed = open(CONFIG['main_feed'],'w')
            mainfeed = open(CONFIG['tmp_folder']+'delegaciones','w')

            for rir in ['arin','ripencc','apnic','lacnic','afrinic']:
                archivo=CONFIG['deleg_'+rir]
                print("\t\t  --> Parseando "+archivo)
                
                try:
                    with open(archivo,'r') as delegation:
                        contenido = delegation.readlines()
                        for linea in contenido:
                            if not re.search(r'^(arin|ripencc|apnic|lacnic|afrinic)\|',linea):
#                                print('Linea ignorada: '+linea)
                                next
                            else:
                                if re.search(r'\|summary$',linea):
                                    next
                                else:
                                    mainfeed.write(linea.strip()+"\n")
                except IOError as e:
                    print ('Error al acceder el archivo: '+archivo+': '+e)
            mainfeed.close()
            chuchuua={"":{"":{}}}
            ipv4=dict()
            ipv6=dict()
            f = open(CONFIG['tmp_folder']+'delegaciones','r')
            contenido = f.readlines()
            print('Chequeando CACHE de whois...')
            for linea in contenido:
                linea.strip()
                if re.search(r'asn',linea):
                    datos = linea.split('|')
                    rir = datos[0].strip()
                    pais = datos[1].strip()
                    tipo = datos[2].strip()
                    asn = datos[3].strip()
                    estado = datos[6].strip()
                    listadodeasn.add(int(asn))
#                    if(estado.lower()=='assigned' or estado.lower()=='allocated'):
#                        pepe = whois(CONFIG,listadodeasn,rir.upper())
### FIXME                
#            print(chuchuua)
            
            f.close()
    print("\t  * ASN's asignados por IANA")
    
def unq(seq):
    """ Devuelve un set con elementos unicos """
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def generar_faltantes(CONFIG,PAIS):
    f=open(CONFIG['tmp_folder']+"RPT_ASNs_"+PAIS+'_'+CONFIG['tabla_mundial'],'r')
    ASNsGlobales=eval(f.readline())
    f.close()
    f=open(CONFIG['tmp_folder']+'asnsixp-'+PAIS+'.txt','r')
    ASNsIXP=eval(f.readline())
    f.close()
    
    ASNsFaltantesEnElIXP = ASNsGlobales - ASNsIXP
    noestanenelixp=list()
    
    for item in ASNsFaltantesEnElIXP:
        noestanenelixp.append(item)
    noestanenelixp.sort()    
    datoswhois = rdapwhois(CONFIG,ASNsFaltantesEnElIXP)
    print('ASNs publicados al mundo que faltan en el IXP de '+PAIS+': '+str(len(ASNsFaltantesEnElIXP)))
    
    for faltante in noestanenelixp:
        try:
            with open(CONFIG['json_folder']+faltante+'.json','r') as j:
                jdata = json.load(j)
                print('\t --> AS'+faltante+' '+jdata['entities'][0]['vcardArray'][1][5][3][0].encode('utf-8'))
                print('\t\t Tecnico: '+jdata['entities'][2]['vcardArray'][1][1][3].encode('utf-8'))
                print('\t\t Email: <'+jdata['entities'][2]['vcardArray'][1][3][3].lower()+'>')
        except IOError as e:
            print('\t --> [RDAP-Bug] Error al leer el JSON de AS'+str(faltante))

def parseMRT(bgpfile):
    """Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    with open(bgpfile,'r') as dump:
        dumplines = dump.readlines()
        for linea in dumplines:
            linea = linea.strip()
            aspath= txtxtract(linea,'ASPATH: ',';')
            asns = aspath.split()
            lastasn=0
            for asn in asns:
                if(asn[0] == '{'):
                    asset=txtxtract(asn,'{','}')
                    for componente in asset:
                        ListaASNs+=[componente]
                        ListaLinks+=[asset[0]+','+componente]
                else:
                    ListaASNs+=[asn]
                    if(lastasn > 0):
                        ListaLinks+=[lastasn+','+asn]
                    lastasn=asn
    return([set(ListaASNs), set(ListaLinks)])

def parseCisco(bgpfile):
    """Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    offset=0
    with open(bgpfile,'r') as dump:
        dumplines = dump.readlines()
        while offset < 1:
            for linea in dumplines:
                linea = linea.strip()
                if(re.search(r'.*Path.*',linea)):
                    offset=linea.find('Path')
                    break
                    
        for linea in dumplines:
            if(re.search(r'^\*\>?.*[i\?]$',linea)):
                aspath=linea[offset:-2]
                asns = aspath.split()
                lastasn=0
                for asn in asns:
                    if(asn[0] == '{'):
                        asset=txtxtract(asn,'{','}')
                        for componente in asset:
                            ListaASNs+=[componente]
                            ListaLinks+=[asset[0]+','+componente]
                    else:
                        ListaASNs+=[asn]
                        if(lastasn > 0):
                            ListaLinks+=[lastasn+','+asn]
                        lastasn=asn
        return([set(ListaASNs), set(ListaLinks)])

def txtxtract(texto,st,en):
    """Extrae un pedazo de texto dado un atributo de MRT"""
    chunk = texto.strip()
    inicio = chunk.find(st)
    if(inicio < 1):
            return ''
    minichunk = chunk[inicio:]
    fin = minichunk.find(en)
    if(fin < 1):
            return ''
    buscado = minichunk[len(st):fin]
    return str(buscado)

def ribtype(archivo):
    minhits=5
    chits=0
    mhits=0
    lin=0
    try:
        with open(archivo,'r') as dump:
            contenido = dump.readlines()
            totaldelineas=len(contenido)
            for linea in contenido:
                lin+=1
                linea = linea.strip()
                if(chits >= minhits):
                    return 'cisco'
                if(mhits >= minhits):
                    return 'mrt'
                if(re.search(r'^\*.*(i|\?)$',linea)):
                    chits+=1
                if(re.search(r'^TYPE.*PREFIX.*ASPATH:.*',linea)):
                    mhits+=1
                if(lin>minhits*4):
                    return False
                    break
    except IOError as e:
        print('No puedo abrir el archivo '+archivo+': '+e)