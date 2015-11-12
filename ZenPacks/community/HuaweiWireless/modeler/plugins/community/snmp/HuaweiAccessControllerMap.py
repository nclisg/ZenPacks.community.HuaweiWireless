from Products.DataCollector.plugins.CollectorPlugin import (SnmpPlugin, GetTableMap, GetMap) 
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap, MultiArgs

#Lookup table for AP Status
statusname = {
    1 : 'idle',
    2 : 'autofind',
    3 : 'typeNotMatch',
    4 : 'fault',
    5 : 'config', 
    6 : 'configFailed', 
    7 : 'download', 
    8  : 'normal', 
    9: 'commiting', 
    10 : 'commitFailed', 
    11 : 'standby', 
    12: 'vermismatch'
    }

#Lookup table for AP Region Deploy modes
deploymodes = {
    1 : 'Discrete',
    2 : 'Normal',
    3 : 'Dense'
    }

class HuaweiAccessControllerMap(SnmpPlugin): 

#Pull SNMP data from controllers

    snmpGetTableMaps = (
        GetTableMap( 
            'hwApRegionTable', '1.3.6.1.4.1.2011.6.139.2.5.1.1', { 
                '.2':'hwApRegionName', 
                '.3':'hwApRegionDeployMode', 
                '.4':'hwApRegionApNumber', 
                } 
            ),  
        GetTableMap( 
            'hwApObjectsTable', '1.3.6.1.4.1.2011.6.139.2.6.1.1', { 
                '.2':'hwApUsedType', 
                '.4':'hwApUsedRegionIndex', 
                '.5':'hwApMac', 
                '.6':'hwApSn', 
                '.7':'hwApSysName', 
                '.8':'hwApRunState', 
                '.9':'hwApSoftwareVersion', 
                '.15':'hwApIpAddress', 
                '.20':'hwApRunTime', 
            } 
        ),
        GetTableMap(
            'hwApLldpTable', '1.3.6.1.4.1.2011.6.139.2.6.14.1', {
                '.6':'hwApLldpRemPortId',
                '.8':'hwApLldpRemSysName',
            }
        )
    )

    snmpGetMap = GetMap({
            '.1.3.6.1.2.1.47.1.1.1.1.11.9':'entPhysicalSerialNum',
            '.1.3.6.1.2.1.47.1.1.1.1.10.3':'entPhysicalSoftwareRev',
            '.1.3.6.1.4.1.2011.6.139.1.2.5.0':'hwWlanAcAccessMaxApNumber',
        })

    def process(self, device, results, log): 

        log.info('processing %s for device %s', self.name(), device.id)
        
        maps = []
	regionmap = []

        regionnames = []

        getdata, tabledata = results;
  
        acc_points = tabledata.get('hwApObjectsTable', {}) 
        lldp = tabledata.get('hwApLldpTable', {}) 
        regions = tabledata.get('hwApRegionTable', {})
      
        #  AP Region Component
        for snmpindex, row in regions.items(): 
            name = row.get('hwApRegionName') 

            if not name: 
                log.warn('Skipping region with no name') 
                continue 
            regionnames.append(name)
            regionmap.append(ObjectMap({ 
                'id': self.prepId(name), 
                'title': name, 
                'snmpindex': snmpindex.strip('.'), 
                'regiondeploymode': deploymodes.get(row.get('hwApRegionDeployMode'), 'Unknown'), 
                'regionapnumber': row.get('hwApRegionApNumber'), 
                })) 



        # Access Point Component

        for region in regionnames:
            apmap = []
            for snmpindex, row in (acc_points.items()): 
           
                neighbour = ""
                neighport = ""

                name = row.get('hwApSysName')
 
                regionrow = regions.get('.' + str(row.get('hwApUsedRegionIndex'))),       
                apregion = regionrow[0].get('hwApRegionName'), 
                
                if not name: 
                    log.warn('Skipping access point with no name') 
                    continue 

                if region == apregion[0]:
                    apneighbour = lldp.get(snmpindex + '.200.1')
                    if apneighbour is not None:
                        neighbour = apneighbour.get('hwApLldpRemSysName'),
                        neighport = apneighbour.get('hwApLldpRemPortId'),
    
                    apmap.append(ObjectMap({ 
                        'id': self.prepId(name), 
                        'title': name, 
                        'snmpindex': snmpindex.strip('.'), 
                        'apip': row.get('hwApIpAddress'), 
                        'apmac': self.asmac(row.get('hwApMac')), 
                        'apserial': row.get('hwApSn'), 
                        'apmodel': row.get('hwApUsedType'), 
                        'apstatus': statusname.get(row.get('hwApRunState'), 'Unknown'), 
                        'apregion': apregion,
                        'apsoftwareversion': row.get('hwApSoftwareVersion'),
                        'apneighbourname' : neighbour,
                        'apneighbourport' : neighport,
                        })) 

            maps.append(RelationshipMap(
                compname = 'huaweiAPRegions/%s' % region,
                relname = 'huaweiAccessPoints',
                modname = 'ZenPacks.community.HuaweiWireless.HuaweiAccessPoint',
                objmaps = apmap))

        # Map main device details
        maps.append(ObjectMap(
            modname = 'ZenPacks.community.HuaweiWireless.HuaweiControllerDevice',
            data = {
                'setHWSerialNumber': getdata.get('entPhysicalSerialNum'),
                'setOSProductKey': MultiArgs(getdata.get('entPhysicalSoftwareRev'), 'HUAWEI Technology Co.,Ltd'),
                'controller_maxap': getdata.get('hwWlanAcAccessMaxApNumber'),
            }))

        # Map AP Region components
        maps.append(RelationshipMap(
            relname = 'huaweiAPRegions',
            modname = 'ZenPacks.community.HuaweiWireless.HuaweiAPRegion',
            objmaps = regionmap))


        return maps
