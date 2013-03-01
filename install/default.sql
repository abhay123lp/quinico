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
-- Table structure for table `main_config`
--

DROP TABLE IF EXISTS `main_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `config_name` varchar(50) CHARACTER SET latin1 NOT NULL,
  `config_value` varchar(500) CHARACTER SET latin1 NOT NULL,
  `friendly_name` varchar(50) NOT NULL,
  `description` varchar(200) NOT NULL,
  `display` varchar(8) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=33 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_config`
--

LOCK TABLES `main_config` WRITE;
/*!40000 ALTER TABLE `main_config` DISABLE KEYS */;
INSERT INTO `main_config` VALUES (1,'google_key','','Google API Key','The Google API key used for Google Search and Google Pagespeed.','password'),(2,'max_keyword_results','20','Keyword Rank Max Results','The maximum number of search results to review when determining keyword rankings.','string'),(3,'max_google_api_calls','1000','Keyword Rank Max API Calls','The maximum number of Google search API calls that Quinico is permitted to make each day.  Google provides 100 free API calls to the Search API per day, beyond which you must setup billing.  If you ar','string'),(4,'seomoz_access_id','','SEOMoz Access ID','The SEOMoz access ID.','string'),(5,'seomoz_secret_key','','SEOMoz Secret Key','The SEOMoz Secret Key.','password'),(6,'wpt_key','','Webpagetest Key','The Webpagetest API Key','password'),(7,'wpt_attempts','30','Webpagetest Attempts','The number of time to check for completion of a test, before skipping the current test and moving on to the next test.','string'),(8,'wpt_wait','120','Webpagetest Wait Time','The amount of time to wait, after a Webpagetest request has been lodged, to check for completion.','string'),(9,'google_wm_username','','Google Webmaster Username','The Google user account username with access to the Webmaster tools for the sites being monitored by Quinico.','string'),(10,'google_wm_password','','Google Webmaster Password','The Google user account password with access to the Webmaster tools for the sites being monitored by Quinico.','password'),(11,'seomoz_account_type','','SEOMoz Account Type','The SEOMoz Account Type (free or paid)','string'),(12,'google_se_id','','Keyword Rank Search Engine ID','The Google custom search engine ID for the Quinico application.  ','string'),(13,'smtp_notify_data_start','0','Notify Data Start','Whether or not to notify via email each time a data job starts.','boolean'),(14,'smtp_notify_seomoz_new','1','SEOMoz Notify New','Notify via email if SEOMoz data is new','boolean'),(15,'dashboard_refresh','30','Dashboard Refresh','The dashboard needs to be refreshed periodically (for example, to pick up new charts that may have been added).  This is the rate at which the browser refresh will occur (for anonymous and logged in u','string'),(16,'dashboard_slots','2x2','Dashboard Slots','The number of dashboard slots for an anonymous user when running the dashboard application.','string'),(17,'dashboard_width','475','Dashboard Width','The width of dashboard slots for an anonymous user when running the dashboard application.','string'),(18,'dashboard_height','250','Dashboard Height','The height of dashboard slots for an anonymous user when running the dashboard application.','string'),(19,'dashboard_font','14','Dashboard Font','The dashboard font size for an anonymous user.  Dashboard fonts control chart and graph font sizes in the dashboard application.','string'),(20,'dashboard_frequency','120','Dashboard Frequency','The frequency that dashboard charts will be changed for an anonymous user when running the dashboard application.','string'),(21,'alert','','Visual Alert','Display an alert message to users of Quinico on the homepage.  This field supports HTML tags.','string'),(22,'report_path','/opt/quinico-local/report_downloads','Report Download Location','Location on the local file system where Google Pagespeed and Webpagetest raw reports will be saved.  This location must be writeable by the user that runs Apache.','string'),(23,'pagespeed_locale','en','Pagespeed Locale','The locale that results should be generated in.  The only currently supported Locale is en.','string'),(24,'pagespeed_threads','5','Pagespeed Threads','The number of independent worker threads to spawn during data collection.','string'),(25,'wpt_threads','5','Webpagetest Threads','The number of independent worker threads to spawn during data collection.','string'),(26,'keyword_rank_threads','5','Keyword Rank Threads','The number of independent worker threads to spawn during data collection.  ','string'),(27,'webmaster_threads','5','Webmaster Threads','The number of independent worker threads to spawn during data collection.','string'),(28,'disable_pagespeed_reports','0','Disable Pagespeed Reports','Whether or not to display the Pagespeed report interfaces.  Setting this to true hides the report interfaces but data jobs, if enabled, will still run.','boolean'),(29,'disable_keyword_rank_reports','0','Disable Keyword Rank Reports','Whether or not to display the Keyword Rank report interfaces.  Setting this to true hides the report interfaces but data jobs, if enabled, will still run.','boolean'),(30,'disable_webmaster_reports','0','Disable Webmaster Reports','Whether or not to disable the Webmaster report interfaces.  Setting this to true hides the report interfaces but data jobs, if enabled, will still run.','boolean'),(31,'disable_seomoz_reports','0','Disable Seomoz Reports','Whether or not to display the Seomoz report interfaces.  Setting this to true hides the report interfaces but data jobs, if enabled, will still run.','boolean'),(32,'disable_webpagetest_reports','0','Disable Webpagetest Reports','Whether or not to disable the Webpagetest report interfaces.  Setting this to true hides the report interfaces but data jobs, if enabled, will still run.','boolean');
/*!40000 ALTER TABLE `main_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_data_job`
--

DROP TABLE IF EXISTS `main_data_job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_data_job` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_name` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
  `job_status` tinyint(1) NOT NULL,
  `job_hour` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
  `job_minute` varchar(25) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_name` (`job_name`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_data_job`
--

LOCK TABLES `main_data_job` WRITE;
/*!40000 ALTER TABLE `main_data_job` DISABLE KEYS */;
INSERT INTO `main_data_job` VALUES (1,'pagespeed',0,'',''),(2,'keyword_rank',0,'',''),(3,'',0,'',''),(4,'seomoz',0,'',''),(5,'webpagetest',0,'','');
/*!40000 ALTER TABLE `main_data_job` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `main_help`
--

DROP TABLE IF EXISTS `main_help`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `main_help` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `help_name` varchar(100) NOT NULL,
  `help_value` varchar(1500) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_help`
--

LOCK TABLES `main_help` WRITE;
/*!40000 ALTER TABLE `main_help` DISABLE KEYS */;
INSERT INTO `main_help` VALUES (1,'/pagespeed/report','<b>Score</b>\r\n<br>\r\n(0-100) indicates how much faster a page could be. A high score indicates little room for improvement, while a low score indicates more room for improvement.\r\n\r\n<br>\r\n<br>\r\n\r\n<b>Impact</b>\r\n<br>\r\nEach PageSpeed rule generates an impact number (an unbounded floating point value) that indicates the importance or priority of implementing the rule-result suggestions for the rule, relative to other rules. For instance, if enabling compression would save 1MB, while optimizing images would save 500kB, the Enable Compression rule would have an impact value that is twice that of the Optimize Images rule. An impact of zero indicates that there are no suggestions for improvement for that rule.\r\n\r\n<br>\r\n<br>\r\n\r\n<b>Key</b>\r\n<table class=\"tiny_no_border_l\">\r\n <tr>\r\n  <td bgcolor=\"#F62217\" width=\"10\">High Priority</td>\r\n  <td>These suggestions represent the largest potential performance wins for the least development effort. You should address these items first.</td>\r\n </tr>\r\n <tr>\r\n  <td bgcolor=\"#FF9900\">Medium Priority</td>\r\n  <td>These suggestions may represent smaller wins or much more work to implement. You should address these items next.</td>\r\n </tr>\r\n <tr>\r\n  <td bgcolor=\"#6699FF\">Low Priority</td>\r\n  <td>These suggestions represent the smallest wins. You should only be concerned with these items after you\'ve handled the higher-priority ones. </td>\r\n </tr>\r\n</table>');
/*!40000 ALTER TABLE `main_help` ENABLE KEYS */;
UNLOCK TABLES;

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
