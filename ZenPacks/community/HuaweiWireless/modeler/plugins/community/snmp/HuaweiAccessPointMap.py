from Products.DataCollector.plugins.CollectorPlugin import (SnmpPlugin, GetTableMap) 

statusname = { 1 : 'idle', 2 : 'autofind', 3 : 'typeNotMatch', 4 : 'fault', 5 : 'config', 6 : 'configFailed', 7 : 'download', 8  : 'normal', 9: 'commiting', 10 : 'commitFailed', 11 : 'standby', 12: 'vermismatch' }

class HuaweiAccessPointMap(SnmpPlugin): 
    relname = 'huaweiAccessPoints' 
    modname = 'ZenPacks.community.HuaweiWireless.HuaweiAccessPoint' 

    snmpGetTableMaps = ( 
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
        ),
        GetTableMap( 
            'hwApRegionTable', '1.3.6.1.4.1.2011.6.139.2.5.1.1', { 
                '.2': 'hwApRegionName', 
            }
        )
    )

    def process(self, device, results, log): 

        log.info('processing %s for device %s', self.name(), device.id)
        acc_points = results[1].get('hwApObjectsTable', {}) 
        lldp = results[1].get('hwApLldpTable', {}) 
        regions = results[1].get('hwApRegionTable', {})
        
        rm = self.relMap() 
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
		
            rm.append(self.objectMap({ 
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

        return rm 
