import DBConnector
import pdb
import sys
import datetime


class DBInfo:
    host = 'vmvisiondb'
    user = 'vmsuser'
    pwd = 'irrelev@nt'


insertSql = '''
REPLACE INTO
    eco_img_repo.vmproj_id_to_cam_views
VALUES
    <values>
'''


insertVmprojIdSql = '''
REPLACE INTO
    eco_data.vmproj_id_to_region_info
VALUES
    <values>
'''



getNodeId = '''
SELECT 
    database_id
FROM
    c_safeway_phase2categories.node
WHERE
    name = '<name>'
AND
    id 
LIKE
    '%<storeId>%'
'''




    
getCamViewIdSql = '''
SELECT
    cam_view_id
FROM
    eco_img_repo.cam_store
WHERE
        store_id = <storeId>
    AND
        cam_name = '<camName>'
    AND
        cam_view_end_dt = '9999-12-31'
    AND
        cam_view_dsc = 'overview'
'''
  

if __name__ == "__main__":
    storeId = sys.argv[1]
    mapFile = sys.argv[2]
    startDate = datetime.date(int(sys.argv[3][0:4]),int(sys.argv[3][4:6]),int(sys.argv[3][6:]))
    endDate = datetime.date(int(sys.argv[4][0:4]),int(sys.argv[4][4:6]),int(sys.argv[4][6:]))

    try:
        assert endDate >= startDate
    except:
        raise Exception,"End date HAS to be atleast the same as the start date if not greater"
        
    
    db = DBConnector.DBConnector(DBInfo.host,DBInfo.user,DBInfo.pwd)
    
    
    
    fp = open(mapFile,'rb')
    for line in fp:
        values = ''
        
        name,location,camList,points = line.split(':')
        location = location.split("-")[1]
        vmprojId = "%s_%s_%s" % (storeId, name, location)
        nodeSql = getNodeId.replace('<name>',name)
        nodeSql = nodeSql.replace('<storeId>',storeId)
        nodeId = db.execSelectSql(nodeSql)
        try:
            nodeId = nodeId[0][0]
        except:
            print "\nCategory %s has NO node_id. Assigning 0"%(name)
            nodeId = 0
        
        camList = camList.split(',')
        for cam in camList:
            sql = getCamViewIdSql.replace('<storeId>',storeId)
            sql = sql.replace('<camName>',cam)
            # print sql
            retval = db.execSelectSql(sql)
            try:
                assert len(retval) != 0
            except:
                print "\nCam: %s does NOT have an associated cam view Id. skipping.....\n"%(cam)
                continue
            camViewId = retval[0][0]
            values = "(" + "'"+vmprojId+"'," + "'"+camViewId+"'," + "'"+startDate.strftime("%Y-%m-%d")+"'," + "'"+endDate.strftime("%Y-%m-%d")+"'" +")"
            # pdb.set_trace()        
            sql = insertSql.replace("<values>",values)
            db.execInsertSql(sql)
            
            vmprojValues = "(%s, '%s', '%s', '%s', %d, '%s', '%s', '%s')" % (storeId, vmprojId, name, location, nodeId, startDate.strftime("%Y-%m-%d"), endDate.strftime("%Y-%m-%d"), points)
            sql = insertVmprojIdSql.replace("<values>", vmprojValues)
            db.execInsertSql(sql)
            
    
    # print sql
    # pdb.set_trace()
    
    
