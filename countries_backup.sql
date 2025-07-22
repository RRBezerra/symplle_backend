PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE countries (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	iso_code VARCHAR(2) NOT NULL, 
	iso_code_3 VARCHAR(3), 
	iso_num VARCHAR(3), 
	calling_code VARCHAR(8), 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (iso_code)
);
INSERT INTO countries VALUES(1,'Afghanistan','AF','AFG','004','+93');
INSERT INTO countries VALUES(2,'Albania','AL','ALB','008','+355');
INSERT INTO countries VALUES(3,'Algeria','DZ','DZA','012','+213');
INSERT INTO countries VALUES(4,'Andorra','AD','AND','020','+376');
INSERT INTO countries VALUES(5,'Angola','AO','AGO','024','+244');
INSERT INTO countries VALUES(6,'Argentina','AR','ARG','032','+54');
INSERT INTO countries VALUES(7,'Australia','AU','AUS','036','+61');
INSERT INTO countries VALUES(8,'Austria','AT','AUT','040','+43');
INSERT INTO countries VALUES(9,'Belgium','BE','BEL','056','+32');
INSERT INTO countries VALUES(10,'Brazil','BR','BRA','076','+55');
INSERT INTO countries VALUES(11,'Canada','CA','CAN','124','+1');
INSERT INTO countries VALUES(12,'China','CN','CHN','156','+86');
INSERT INTO countries VALUES(13,'France','FR','FRA','250','+33');
INSERT INTO countries VALUES(14,'Germany','DE','DEU','276','+49');
INSERT INTO countries VALUES(15,'India','IN','IND','356','+91');
INSERT INTO countries VALUES(16,'Italy','IT','ITA','380','+39');
INSERT INTO countries VALUES(17,'Japan','JP','JPN','392','+81');
INSERT INTO countries VALUES(18,'Mexico','MX','MEX','484','+52');
INSERT INTO countries VALUES(19,'Portugal','PT','PRT','620','+351');
INSERT INTO countries VALUES(20,'Russia','RU','RUS','643','+7');
INSERT INTO countries VALUES(21,'Spain','ES','ESP','724','+34');
INSERT INTO countries VALUES(22,'United Kingdom','GB','GBR','826','+44');
INSERT INTO countries VALUES(23,'United States','US','USA','840','+1');
COMMIT;
