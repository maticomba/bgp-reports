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
    from netaddr import IPNetwork, IPAddress
    

# Por el bug del sistema Restful de LACNIC
    RDAP404=set()

# Configuracion
    CONFIG=dict()
    CONFIG['feed_dir']='feeds/'
    CONFIG['feed_ttl']=3600*24*7 #Cada cuantos segundos vuelvo a bajar los feeds
    CONFIG['json_folder']='cache/'
    CONFIG['rpt_folder']='reportes/'
    CONFIG['tmp_folder']='workdir/'
    CONFIG['htmli_folder']='htmlincludes/'
    #CONFIG['tabla_mundial']='bgp-global'
    #CONFIG['tabla_mundial']='rutas-level3.txt'
    CONFIG['tabla_mundial']='full-routing-cisco.txt'
    CONFIG['tabla_asn_iana']=CONFIG['feed_dir']+'asn-rir.csv'
    CONFIG['tabla_asn_json']=CONFIG['json_folder']+'asn-rir.json'
    CONFIG['RIR']="lacnic"
    CONFIG['tabla_rir_pais']=CONFIG['feed_dir']+'pais-rir.html'
    CONFIG['deleg_arin']=CONFIG['feed_dir']+'delegated-arin-latest'
    CONFIG['deleg_apnic']=CONFIG['feed_dir']+'delegated-apnic-latest'
    CONFIG['deleg_ripencc']=CONFIG['feed_dir']+'delegated-ripencc-latest'
    CONFIG['deleg_lacnic']=CONFIG['feed_dir']+'delegated-lacnic-latest'
    CONFIG['deleg_afrinic']=CONFIG['feed_dir']+'delegated-afrinic-latest'
    CONFIG['deleg_arin_url']='http://localhost/delegated-arin-latest'
    CONFIG['deleg_apnic_url']='http://localhost/delegated-apnic-latest'
    CONFIG['deleg_ripencc_url']='http://localhost/delegated-ripencc-latest'
    CONFIG['deleg_lacnic_url']='http://localhost/delegated-lacnic-latest'
    CONFIG['deleg_afrinic_url']='http://localhost/delegated-afrinic-latest'
#    CONFIG['deleg_arin_url']='ftp://ftp.apnic.net/pub/stats/arin/delegated-arin-extended-latest'
#    CONFIG['deleg_apnic_url']='ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest'
#    CONFIG['deleg_ripencc_url']='ftp://ftp.ripe.net/ripe/stats/delegated-ripencc-latest'
#    CONFIG['deleg_lacnic_url']='ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest'
#    CONFIG['deleg_afrinic_url']='ftp://ftp.apnic.net/pub/stats/afrinic/delegated-afrinic-latest'
    CONFIG['main_feed']=CONFIG['json_folder']+'main_feed.json'
    #
    #CONFIG['tablaixp']['AR'] = CONFIG['feed_dir']
    
    RecursosRIR = dict()
    RecursosRIR['LACNIC']=CONFIG['feed_dir']+'delegated-lacnic-latest'
    RecursosRIR['APNIC']=CONFIG['feed_dir']+'delegated-apnic-latest'
    RecursosRIR['RIPE']=CONFIG['feed_dir']+'delegated-ripencc-latest'

    asnutils.actualizar_feeds(CONFIG)
    asnutils.parse_asn_rir(CONFIG)
    
    asnutils.generar_reporte_global(CONFIG)
    
    for PAIS in ['AR']:
        asnutils.generar_reporte_ixp(CONFIG,PAIS,RecursosRIR)
        asnutils.generar_reporte_pais(CONFIG,PAIS)
        asnutils.generar_faltantes(CONFIG,PAIS)
        
    print"\nHave a nice day"
    exit