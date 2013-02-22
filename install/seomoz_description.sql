/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `seomoz_description`
--

DROP TABLE IF EXISTS `seomoz_description`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `seomoz_description` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `metric` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `column_description` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `full_description` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `represent` varchar(7) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `metric` (`metric`,`column_description`,`full_description`)
) ENGINE=MyISAM AUTO_INCREMENT=26 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seomoz_description`
--

LOCK TABLES `seomoz_description` WRITE;
/*!40000 ALTER TABLE `seomoz_description` DISABLE KEYS */;
INSERT INTO `seomoz_description` VALUES (1,'ueid','External Links','The number of juice-passing external links to the URL','integer'),(2,'feid','Subdomain External Links','The number of juice-passing external links to the subdomain of the URL','integer'),(3,'uid','Links','The number of links (juice-passing or not, internal or external) to the URL','integer'),(4,'fmrp','Subdomain MozRank','The mozRank of the subdomain of the URL (the pretty 10-point score)','decimal'),(5,'umrp','MozRank','The mozRank of the URL (the pretty 10-point score)','decimal'),(6,'upa','Page Authority','A score out of 100 points representing the likelihood of a page to rank well, regardless of content','integer'),(7,'pda','Domain Authority','A score out of 100 points representing the likelihood of a domain to rank well, regardless of content','integer'),(8,'peid','Root Domain External Links','The number of juice-passing external links to the root domain of the URL','integer'),(9,'ujid','Juice-Passing Links','The number of juice-passing links (internal or external) to the URL','integer'),(10,'uifq','Subdomains Linking','The number of subdomains with any pages linking to the URL','integer'),(11,'uipl','Root Domains Linking','The number of root domains with any pages linking to the URL','integer'),(12,'fid','Subdomain Subdomains Link','The number of subdomains with any pages linking to the subdomain of the URL','integer'),(13,'pid','Root Domain Root Domains Linking','The number of root domains with any pages linking to the root domain of the URL','integer'),(14,'fuid','Links to Subdomain','Total links (including internal and nofollow links) to the subdomain of the URL','integer'),(15,'puid','Links to Root Domain','Total links (including internal and nofollow links) to the root domain of the URL','integer'),(16,'fipl','Root Domains linking to Subdomain','The number of root domains with at least one link to the subdomain of the URL','integer'),(17,'pmrp','Root Domain MozRank','The mozRank of the Root Domain of the URL (the pretty 10-point score)','decimal'),(18,'utrp','MozTrust','The mozTrust of the URL (the pretty 10-point score)','decimal'),(19,'ftrp','Subdomain MozTrust','The mozTrust of the subdomain of the URL (the pretty 10-point score)','decimal'),(20,'ptrp','Root Domain MozTrust','The mozTrust of the root domain of the URL (the pretty 10-point score)','decimal'),(21,'uemrp','External MozRank','The portion of the URL\'s mozRank coming from external links (the pretty 10-point score)','decimal'),(22,'pejp','Root Domain External Domain juice','The portion of the mozRank of all pages on the root domain coming from external links (the pretty 10-digit score)','decimal'),(23,'fjp','Subdomain Domain Juice','The mozRank of all pages on the subdomain combined (the pretty 10-point score)','decimal'),(24,'pjp','Root Domain Domain Juice','The mozRank of all pages on the root domain combined (the pretty 10-point score)','decimal'),(25,'fejp','Subdomain External Domain Linking Juice','The portion of the URL\'s mozRank coming from external links (the pretty 10-digit score)','decimal');
/*!40000 ALTER TABLE `seomoz_description` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
