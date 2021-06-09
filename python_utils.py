import constants
'''Purpose of this python script to keep all validation method implementataions

Method to validate 
Name - Any value (250 chars in any language)
Id - YouTube: Check if the last part of the URL is the same as the Id
URL - Must be a valid URL - YouTube channel must start with [https://www.youtube.com/channel/]
Inventory Type: One of (YouTube, App, Site); include lower case writings
Grouping - Any value [this will result in a "link" between the uploaded placements with the same group]
{
    errorCode: XXXX
    message: "Invalid uploaded batch data",
    details: [
        { row: 1, error: "Invalid URL format" },
        { row: 1, error: "ID is required" },
        { row: 12, error: "Invalid URL format"}
    ]
}'''

def validateData(placementList):
    details = []
    inventoryType = ['youtube','app','site']
    for item in placementList:
        rowNumber = item['row']
        isIDPresent = True
        if 'name' not in item or not item['name']:
            collectErrorDetail(details,rowNumber,constants.NAME_REQUIRED)
        if 'name' in item and len(item['name']) > 250:
            collectErrorDetail(details,rowNumber,constants.MAX_LENGTH_EXCEEDED)
        if 'id' not in item or not item['id']:
            collectErrorDetail(details,rowNumber,constants.ID_REQUIRED)
            isIDPresent = False
        if 'inventoryType' not in item:
            collectErrorDetail(details,rowNumber,constants.INVENTORY_TYPE_REQUIRED)
        elif  inventoryType.count(item['inventoryType'].casefold()) == 0:
            collectErrorDetail(details,rowNumber,constants.INVALID_INVENTORY_TYPE)
        if  item['url']:
            urlId = item['url'].split("/")[4]
            if not item['url'].startswith(constants.URLPREFIX):
                collectErrorDetail(details,rowNumber,constants.INVALID_URL)
            elif isIDPresent:
                if not item['id'] == urlId:
                    collectErrorDetail(details,rowNumber,constants.URL_ID_MISMATCHED)
        else:
            collectErrorDetail(details,rowNumber,constants.URL_REQUIRED)
    
    # Prepeare error details for provide batch upload
    errorDetails = {}
    if len(details)>=1:
        errorDetails['errorCode'] = 'XXXX'
        errorDetails['message']= constants.MESSAGE
        errorDetails['details']= details

    return errorDetails
# Method to collect error details per row
def collectErrorDetail(details, rowNumber, errorInfo):
    errordetails ={}
    errordetails['row'] = rowNumber
    errordetails['error'] = errorInfo
    details.append(errordetails)

# Method to get list of duplicate placementList per batch
def getDuplicatePlacements(placementList,listOfIds):
     duplicatePlacements = []
     newPlacements = []
     newPlacementIds = []
     listOfUniqueId =[]
     for result in listOfIds:
         listOfUniqueId.append(result['id'])

     for item in placementList:
         if item['id'] in listOfUniqueId:
             duplicatePlacements.append(item['id'])
         else:
             newPlacements.append(item)
             newPlacementIds.append(item['id'])

     batchResult ={}
     batchResult['duplicateCount']= len(duplicatePlacements)
     batchResult['duplicatePlacements']= duplicatePlacements
     batchResult['newPlacements'] = newPlacements
     batchResult['newPlacementIds'] = newPlacementIds

     return batchResult

# Method to insert records in batch_dupes_details table

def insertInToBatchDupesDetails(batchID,cursor,duplicatePlacementIds, newPlacementIds):
        
        if len(duplicatePlacementIds) >0:
            for id in duplicatePlacementIds:
                cursor.execute(""" INSERT INTO manualquarationDB.batch_dupes_details(batchID,id,status) VALUES(%s, %s, %s)""",(batchID,id,2))
        
        if len(newPlacementIds) >0:
            for id in newPlacementIds:
                cursor.execute(""" INSERT INTO manualquarationDB.batch_dupes_details(batchID,id,status) VALUES(%s, %s, %s)""",(batchID,id,1))








