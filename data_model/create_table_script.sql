-- Create table Actions if not exists in  manualquarationDB

CREATE TABLE IF NOT EXISTS manualquarationDB.actions_info_details (actionID INT NOT NULL AUTO_INCREMENT ,
 descriptions VARCHAR(30),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(actionID));


-- Create table Roles_INFO_Details

CREATE TABLE IF NOT EXISTS manualquarationDB.role_info_details(roleID INT NOT NULL AUTO_INCREMENT,
    roleType VARCHAR(20),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(RoleID)
    );

-- Create table Users Info Details

CREATE TABLE IF NOT EXISTS manualquarationDB.user_info_details(userID INT NOT NULL AUTO_INCREMENT,
	firstName VARCHAR(30),
	lastName VARCHAR(30),
	userRoleID INT NOT NULL,
    user_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY(userID) );
-- Create Action_History Table

CREATE TABLE IF NOT EXISTS manualquarationDB.action_history_details(historyID INT NOT NULL AUTO_INCREMENT,
	updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	actionID INT,
	userID INT,
	previousValue VARCHAR(50),
	updatedValue VARCHAR(50),
	PRIMARY KEY(historyID)
); 

-- Create Table User_Role_Mapping

 CREATE TABLE IF NOT EXISTS manualquarationDB.user_role_mapping(userID INT NOT NULL,
 	roleID INT NOT NULL,
 	actions ENUM('Owner','Editor','Viewer') DEFAULT NULL
 	);

 -- Create Table DiscoveryBatch

CREATE TABLE IF NOT EXISTS manualquarationDB.discovery_batch_details(
batchID INT NOT NULL AUTO_INCREMENT,
batchName VARCHAR(30),
sourceType VARCHAR(10),
dateUploaded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
percentageAssigned INT,
percentageModerated INT,
percentageQc INT,
priority INT,
PRIMARY KEY(batchID)
--KEY `batchID` (`batchID`,`priority`)
);
-- Create table Moderation Queue View Table
-- CREATE TABLE IF NOT EXISTS manualquarationDB.moderation_queue_view(
-- moderationID INT NOT NULL AUTO_INCREMENT,
-- name varchar(100),
-- source VARCHAR(50),
-- language VARCHAR(5),
-- origin VARCHAR(3),
-- moderator VARCHAR(50),
-- priority INT,
-- status VARCHAR(25),
-- PRIMARY KEY(moderationID)
-- );

-- CREATE INVENTORYPOOL TABLE
CREATE TABLE IF NOT EXISTS manualquarationDB.placement_details(
placementID INT NOT NULL AUTO_INCREMENT,
batchID INT NOT NULL,
priority INT,
publisher VARCHAR(50),
status VARCHAR(50),
moderator VARCHAR(50),
name VARCHAR(150),
id VARCHAR(100),
url VARCHAR(150),
inventoryType INT,
sourceType INT,
source_name VARCHAR(25),
thumbnail VARCHAR(200),
thumbnailForReporting VARCHAR(200),
description VARCHAR(500),
language INT,
otherLanguages  INT,
originSourceCountry INT,
originCountry INT,
marketCountry INT,
SSP INT,
trustTier INT,
subscribers BIGINT,
views BIGINT,
videos BIGINT,
averageView BIGINT,
averageViewOverSixMonths BIGINT,
videoUploadFrequency INT,
downloads BIGINT,
monthlyAvailableImpressions BIGINT,
format INT,
formatDetails INT,
sourceKeywords INT,
storeCategory VARCHAR(50),
storeSubCategory VARCHAR(50),
category INT,
interest INT,
gender INT,
genderFocus INT,
ageGroups INT,
ageFocus INT,
mfk INT,
comment VARCHAR(250),
PRIMARY KEY(placementID)
-- KEY `fk_placement_details_batchID` (`batchID`,`priority`),
-- CONSTRAINT `fk_placement_details_batchID` FOREIGN KEY (`batchID`,`priority`) REFERENCES `discovery_batch_details` (`batchID`, `priority`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS manualquarationDB.country_info_details(
countryID INT NOT NULL AUTO_INCREMENT,
countryName VARCHAR(50) UNIQUE,
countryCode VARCHAR(3),
PRIMARY KEY(countryID)
);

-- Inventory Type Table
CREATE TABLE IF NOT EXISTS manualquarationDB.inventory_info_details(
inventoryID INT NOT NULL AUTO_INCREMENT,
inventoryType VARCHAR(30),
PRIMARY KEY(inventoryID)
);

-- Source Type table
CREATE TABLE IF NOT EXISTS manualquarationDB.sourceType_info_details(
souceTypeID INT NOT NULL AUTO_INCREMENT,
souceType VARCHAR(30),
PRIMARY KEY(souceTypeID)
);