from Products.DataCollector.plugins.CollectorPlugin import (SnmpPlugin, GetTableMap) 

deploymodes = { 1 : 'Discrete', 2 : 'Normal', 3 : 'Dense' }


class HuaweiAPRegionMap(SnmpPlugin): 
    relname = 'huaweiAPRegions' 
    modname = 'ZenPacks.community.HuaweiWireless.HuaweiAPRegion' 


    snmpGetTableMaps = ( 
        GetTableMap( 
            'hwApRegionTable', '1.3.6.1.4.1.2011.6.139.2.5.1.1', { 
                '.2': 'hwApRegionName', 
                '.3': 'hwApRegionDeployMode', 
                '.4': 'hwApRegionApNumber', 
                } 
            ), 
        ) 

    def process(self, device, results, log): 
        log.info('processing %s for device %s', self.name(), device.id)
        regions = results[1].get('hwApRegionTable', {}) 

        rm = self.relMap() 
        for snmpindex, row in regions.items(): 
            name = row.get('hwApRegionName') 

            if not name: 
                log.warn('Skipping region with no name') 
                continue 

            rm.append(self.objectMap({ 
                'id': self.prepId(name), 
                'title': name, 
                'snmpindex': snmpindex.strip('.'), 
                'regiondeploymode': deploymodes.get(row.get('hwApRegionDeployMode'), 'Unknown'), 
                'regionapnumber': row.get('hwApRegionApNumber'), 
                })) 

        return rm 
