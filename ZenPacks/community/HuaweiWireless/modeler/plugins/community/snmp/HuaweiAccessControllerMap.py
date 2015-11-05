from Products.DataCollector.plugins.CollectorPlugin import (SnmpPlugin, GetTableMap) 
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap

statusname = { 1 : 'idle', 2 : 'autofind', 3 : 'typeNotMatch', 4 : 'fault', 5 : 'config', 6 : 'configFailed', 7 : 'download', 8  : 'normal', 9: 'commiting', 10 : 'commitFailed', 11 : 'standby', 12: 'vermismatch' }

deploymodes = { 1 : 'Discrete', 2 : 'Normal', 3 : 'Dense' }

class HuaweiAccessControllerMap(SnmpPlugin): 

    snmpGetTableMaps = (
        GetTableMap( 
            'hwApRegionTable', '1.3.6.1.4.1.2011.6.139.2.5.1.1', { 
                '.2': 'hwApRegionName', 
                '.3': 'hwApRegionDeployMode', 
                '.4': 'hwApRegionApNumber', 
                } 
            ),  
        GetTableMap( 
            'hwApObjectsTable', '1.3.6.1.4.1.2011.6.139.2.6.1.1', { 
                '.2': 'hwApUsedType', 
                '.4': 'hwApUsedRegionIndex', 
                '.5': 'hwApMac', 
                '.6': 'hwApSn', 
                '.7': 'hwApSysName', 
                '.8': 'hwApRunState', 
                '.9': 'hwApSoftwareVersion', 
                '.15': 'hwApIpAddress', 
                '.20': 'hwApRunTime', 
            } 
        ),
        GetTableMap(
            'hwApLldpTable', '1.3.6.1.4.1.2011.6.139.2.6.14.1', {
                '.6': 'hwApLldpRemPortId',
                '.8': 'hwApLldpRemSysName',
            }
        )
    )

    def process(self, device, results, log): 

        log.info('processing %s for device %s', self.name(), device.id)
        
        maps = []
        apmap = []
	regionmap = []


        acc_points = results[1].get('hwApObjectsTable', {}) 
        lldp = results[1].get('hwApLldpTable', {}) 
        regions = results[1].get('hwApRegionTable', {})
      
        #  AP Region Component
        for snmpindex, row in regions.items(): 
            name = row.get('hwApRegionName') 

            if not name: 
                log.warn('Skipping region with no name') 
                continue 

            regionmap.append(ObjectMap({ 
                'id': self.prepId(name), 
                'title': name, 
                'snmpindex': snmpindex.strip('.'), 
                'regiondeploymode': deploymodes.get(row.get('hwApRegionDeployMode'), 'Unknown'), 
                'regionapnumber': row.get('hwApRegionApNumber'), 
                })) 



        # Access Point Component
        for snmpindex, row in (acc_points.items()): 
           
            neighbour = ""
            neighport = ""

            name = row.get('hwApSysName') 
             
            if not name: 
                log.warn('Skipping access point with no name') 
                continue 

            apneighbour = lldp.get(snmpindex + '.200.1')
            if apneighbour is not None:
                neighbour = apneighbour.get('hwApLldpRemSysName'),
                neighport = apneighbour.get('hwApLldpRemPortId'),
    
            regionrow = regions.get('.' + str(row.get('hwApUsedRegionIndex'))),       
		
            apmap.append(ObjectMap({ 
                'id': self.prepId(name), 
                'title': name, 
                'snmpindex': snmpindex.strip('.'), 
                'apip': row.get('hwApIpAddress'), 
                'apmac': self.asmac(row.get('hwApMac')), 
                'apserial': row.get('hwApSn'), 
                'apmodel': row.get('hwApUsedType'), 
                'apstatus': statusname.get(row.get('hwApRunState'), 'Unknown'), 
                'apregion': regionrow[0].get('hwApRegionName'),
                'apsoftwareversion': row.get('hwApSoftwareVersion'),
                'apneighbourname' : neighbour,
                'apneighbourport' : neighport,
                })) 

        maps.append(RelationshipMap(
            relname = 'huaweiAPRegions',
            modname = 'ZenPacks.community.HuaweiWireless.HuaweiAPRegion',
            objmaps = regionmap))
          
        maps.append(RelationshipMap(
            relname = 'huaweiAccessPoints',
            modname = 'ZenPacks.community.HuaweiWireless.HuaweiAccessPoint',
            objmaps = apmap))

        return maps
