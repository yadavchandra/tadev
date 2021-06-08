use manualquarationDB;
-- TABLE: SourceType Info Details
CREATE TABLE IF NOT EXISTS manualquarationDB.sourcetype_info_details(
sourceTypeID INT NOT NULL AUTO_INCREMENT,
sourceName VARCHAR(30) UNIQUE,
PRIMARY KEY(sourceTypeID)
);

-- TABLE: Language_info_details
CREATE TABLE IF NOT EXISTS manualquarationDB.language_info_details(
languageID INT NOT NULL AUTO_INCREMENT,
languageValue VARCHAR(30) UNIQUE,
languageCode VARCHAR(5),
PRIMARY KEY(languageID)
);

-- TABLE: other_indian_language_info_details

CREATE TABLE IF NOT EXISTS manualquarationDB.other_indian_language_info_details(
othIndianLangID INT NOT NULL AUTO_INCREMENT,
languageValue VARCHAR(30) UNIQUE,
iso6391Code VARCHAR(5),
iso6392B VARCHAR(5),
PRIMARY KEY(othIndianLangID)
);
 
-- TABLE: SSP_info_details
CREATE TABLE IF NOT EXISTS manualquarationDB.SSP_info_details(
sspID INT NOT NULL AUTO_INCREMENT,
sspValue VARCHAR(30) UNIQUE,
PRIMARY KEY(sspID)
);

-- TABLE: tier_info_details
CREATE TABLE IF NOT EXISTS manualquarationDB.tier_info_details(
tierID INT NOT NULL AUTO_INCREMENT,
tierValue INT UNIQUE,
tierDescription VARCHAR(50),
tierComment VARCHAR(100),
PRIMARY KEY(tierID)
);

-- TABLE: AdFormat

CREATE TABLE IF NOT EXISTS manualquarationDB.adformat_info(
adFormatID INT NOT NULL AUTO_INCREMENT,
adFormatValue VARCHAR(15) UNIQUE,
adFormatDescription VARCHAR(75),
PRIMARY KEY(adFormatID)
);
-- Table: Ad Format Details
CREATE TABLE IF NOT EXISTS manualquarationDB.adformat_details_info(
formatDetailID INT NOT NULL AUTO_INCREMENT,
adFormatValue VARCHAR(30) UNIQUE,
adFormatID INT NOT NULL,
formatDetailDescription VARCHAR(75),
inventoryType VARCHAR(20),
PRIMARY KEY(formatDetailID),
FOREIGN KEY (adFormatID) REFERENCES manualquarationDB.adformat_info(adFormatID)
);

-- TABLE: Category Info Details
CREATE TABLE IF NOT EXISTS manualquarationDB.category_details_info(
categoryID INT NOT NULL AUTO_INCREMENT,
categoryType VARCHAR(30) UNIQUE,
PRIMARY KEY(categoryID)
);
-- TABLE: Inventory Status
CREATE TABLE IF NOT EXISTS manualquarationDB.inventory_status_details(
inventoryStatusID INT NOT NULL AUTO_INCREMENT,
inventoryStatusType VARCHAR(30) UNIQUE,
comment VARCHAR(150),
PRIMARY KEY(inventoryStatusID)
);
-- TABLE:moderation status
CREATE TABLE IF NOT EXISTS manualquarationDB.moderation_status_details(
statusID INT NOT NULL AUTO_INCREMENT,
staus VARCHAR(20) UNIQUE,
comment VARCHAR(150),
PRIMARY KEY(statusID)
);

-- TABLE: candidate status
CREATE TABLE IF NOT EXISTS manualquarationDB.candidate_status_details(
candidateStatusID INT NOT NULL AUTO_INCREMENT,
candidateStaus VARCHAR(20) UNIQUE,
candidateComment VARCHAR(150),
PRIMARY KEY(candidateStatusID)
);

-- TABLE: reason details
CREATE TABLE IF NOT EXISTS manualquarationDB.reason_details(
reasonID INT NOT NULL AUTO_INCREMENT,
reasonType VARCHAR(20),
reasonDetail VARCHAR(20),
PRIMARY KEY(reasonID)
);

-- TABLE: Gender Foucs

CREATE TABLE IF NOT EXISTS manualquarationDB.gender_focus_info(
genderFocusID INT NOT NULL AUTO_INCREMENT,
gender VARCHAR(20) UNIQUE,
PRIMARY KEY (genderFocusID)
);

-- TABLE: Gender

CREATE TABLE IF NOT EXISTS manualquarationDB.gender_info(
genderID INT NOT NULL AUTO_INCREMENT,
gender VARCHAR(20) UNIQUE,
PRIMARY KEY (genderID)
);















