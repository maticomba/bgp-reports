#! /usr/bin/python

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="a.weher"
__date__ ="$Sep 1, 2014 11:38:27 AM$"

def cidrsOverlap(cidr0, cidr1):
    """ Determina si un prefijo es componente de otro"""
    return cidr0.first <= cidr1.last and cidr1.first <= cidr0.last

if __name__ == "__main__":
    import asn
    import asnutils
#    from netaddr import IPNetwork, IPAddress
    
# Main configuration
    CONFIG=dict()
    CONFIG['feed_dir']='feeds/'
    CONFIG['feed_ttl']=3600*24*7 #Cada cuantos segundos vuelvo a bajar los feeds
    CONFIG['json_dir']='cache/'
    CONFIG['rpt_dir']='reportes/'
    CONFIG['tmp_dir']='workdir/'
    CONFIG['htmli_dir']='htmlincludes/'
    
    # BGP Global table file
    CONFIG['tabla_mundial']='full-routing-cisco.txt'
    #CONFIG['tabla_mundial']='full-routing-mrt.txt'
    
    CONFIG['RIR']="lacnic"
    CONFIG['tabla_rir_pais']=CONFIG['feed_dir']+'pais-rir.html'
    
    # List of resources delegated by RIR
    CONFIG['deleg_arin_url']='ftp://ftp.apnic.net/pub/stats/arin/delegated-arin-extended-latest'
    CONFIG['deleg_apnic_url']='ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest'
    CONFIG['deleg_ripencc_url']='ftp://ftp.ripe.net/ripe/stats/delegated-ripencc-latest'
    CONFIG['deleg_lacnic_url']='ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest'
    CONFIG['deleg_afrinic_url']='ftp://ftp.apnic.net/pub/stats/afrinic/delegated-afrinic-latest'
    CONFIG['deleg_arin']=CONFIG['feed_dir']+'delegated-arin-latest'
    CONFIG['deleg_apnic']=CONFIG['feed_dir']+'delegated-apnic-latest'
    CONFIG['deleg_ripencc']=CONFIG['feed_dir']+'delegated-ripencc-latest'
    CONFIG['deleg_lacnic']=CONFIG['feed_dir']+'delegated-lacnic-latest'
    CONFIG['deleg_afrinic']=CONFIG['feed_dir']+'delegated-afrinic-latest'
    
    # IANA ASN's List
    CONFIG['tabla_asn_iana']=CONFIG['feed_dir']+'asn-rir.csv'
    CONFIG['tabla_asn_json']=CONFIG['json_dir']+'asn-rir.json'
    CONFIG['url_deleg_iana_asn16']='http://www.iana.org/assignments/as-numbers/as-numbers-1.csv'
    CONFIG['url_deleg_iana_asn32']='http://www.iana.org/assignments/as-numbers/as-numbers-2.csv'
    CONFIG['main_feed']=CONFIG['json_dir']+'main_feed.json'
    
    # RDAP URL's
    CONFIG['rdap_ARIN']='http://whois.arin.net/rest/asn/AS'
    CONFIG['rdap_RIPENCC']='http://rest.db.ripe.net/search.json?query-string=as'
    CONFIG['rdap_APNIC']=CONFIG['rdap_RIPENCC'] # Todavia no esta implementada la busqueda de ASN, solo IPs: http://www.apnic.net/apnic-info/whois_search/about/rdap
    CONFIG['rdap_LACNIC']='http://rdap.labs.lacnic.net/rdap/autnum/'
    #CONFIG['rdap_LACNIC'] = 'http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/'
    CONFIG['rdap_AFRINIC']=CONFIG['rdap_RIPENCC'] #aun no desarrollado, parece que sirve el de ripe igual 

# Main
    asnutils.foldercheck(CONFIG)
    asnutils.update_feeds(CONFIG)
    asnutils.parse_asn_rir(CONFIG)
    asnutils.generar_reporte_global(CONFIG)
    
    for PAIS in ['AR','CL']:
        asnutils.generar_reporte_ixp(CONFIG,PAIS)
        asnutils.generar_reporte_pais(CONFIG,PAIS)
        asnutils.generar_faltantes(CONFIG,PAIS)
        
    print"\nHave a nice day"
    exit