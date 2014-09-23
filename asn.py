# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
import json
import os
import urllib2
import asnutils

__author__="aweher"
__date__ ="$31/08/2014 20:26:02$"

class ASN():
    """ Nos permite trabajar con ASN's """
    RDAP404 = set()
    asnumber = 0
    def __init__(self,number):
        self.number = number

        self.asn_whois()

    def asn_whois(self):
        """ Obtiene informacion acerca del ASN en formato JSON """
        asnumber = self.number
        if(is_asn32(asnumber)):
            asnumber = convert_to_asplain(self.number)
        else:
            asnumber = self.number
            
        rir = find_rir_by_asn(asnumber) # por ahora devuelve LACNIC
        dirwhois = './WHOIS/'
        
        RDAPurl = dict()
        RDAPurl['LACNIC'] = 'http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/'
        RDAPurl['RIPE'] = 'http://rest.db.ripe.net/search.json?query-string=as'
        RDAPurl['ARIN'] = 'http://whois.arin.net/rest/asn/AS'
        RDAPurl['AFRINIC'] = 'http://rest.db.ripe.net/search.json?query-string=as' #el de ripe parece que sirve
        RDAPurl['APNIC'] = '' # Todavia no esta implementada la busqueda de ASN, solo IPs: http://www.apnic.net/apnic-info/whois_search/about/rdap
        
        # Si no encuentro el directorio para guardar los archivos lo creo
        try: 
            estado = os.stat(dirwhois) 
        except OSError as e:
            os.mkdir(dirwhois)
            
        if ( not RDAPurl[rir] ):
            print ("No hay info de WHOIS para ",rir)
            return
        
        url=RDAPurl[rir]+str(self.number)
        archivo = dirwhois+str(self.number)+'.json'
        
        # A ver si lo encontramos...
        try:
            estado = os.stat(archivo)
            if (estado.st_size>1000):
                archivojson=open(archivo,"r")
                try:
                  datosjson=json.loads(archivojson.read())
                except ValueError, e:
                    print ('Problemas con el archivo: '+str(archivo)+' '+e)
                    #continue
        except OSError as e:
            print ('Problemas: '+e)
        
        opener = urllib2.build_opener()
        
        try:
            request = urllib2.Request(url, headers={'Accept': 'application/json'})
            httprequest = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            print e.code
            print e.read()
            RDAP404.add(self.number)
        else:
            archivojson=open(file,"w")
            try:
                archivojson.write(httprequest.read())
            except OSError as e:
                print ('Problemas: '+e)
            httprequest.close()
            archivojson.close()
        return datosjson

#myas = ASN('4.1','asd','AR','Pepito inc')
#if (myas.is_32() == True):
#    print("El ASN "+str(myas.number)+" es de 32 bits")
#    print(myas.convert_to_asplain())
#else:
#    print("El ASN "+str(myas.number)+" es de 16 bits")