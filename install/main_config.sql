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
) ENGINE=MyISAM AUTO_INCREMENT=28 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_config`
--

LOCK TABLES `main_config` WRITE;
/*!40000 ALTER TABLE `main_config` DISABLE KEYS */;
INSERT INTO `main_config` VALUES (1,'google_key','','Google API Key','The Google API key used for Google Search and Google Pagespeed.','password'),(2,'max_keyword_results','20','Keyword Rank Max Results','The maximum number of search results to review when determining keyword rankings.','string'),(3,'max_google_api_calls','1000','Keyword Rank Max API Calls','The maximum number of Google search API calls per day.','string'),(4,'seomoz_access_id','','SEOMoz Access ID','The SEOMoz access ID.','string'),(5,'seomoz_secret_key','','SEOMoz Secret Key','The SEOMoz Secret Key.','password'),(6,'wpt_key','','Webpagetest Key','The Webpagetest API Key','password'),(7,'wpt_attempts','30','Webpagetest Attempts','The number of time to check for completion of a test, before skipping the current test and moving on to the next test.','string'),(8,'wpt_wait','300','Webpagetest Wait Time','The amount of time to wait, after a Webpagetest request has been lodged, to check for completion.','string'),(9,'google_wm_username','','Google Webmaster Username','The Google user account username with access to the Webmaster tools for the sites being monitored by Quinico.','string'),(10,'google_wm_password','','Google Webmaster Password','The Google user account password with access to the Webmaster tools for the sites being monitored by Quinico.','password'),(11,'seomoz_account_type','free','SEOMoz Account Type','The SEOMoz Account Type (free or paid)','string'),(12,'google_se_id','','Keyword Rank Search Engine ID','The Google custom search engine ID for the Quinico application.  ','string'),(13,'smtp_notify_data_start','1','Notify Data Start','Whether or not to notify via email each time a data job starts.','boolean'),(14,'smtp_notify_seomoz_new','1','SEOMoz Notify New','Notify via email if SEOMoz data is new','boolean'),(15,'dashboard_refresh','30','Dashboard Refresh','The dashboard needs to be refreshed periodically.  This is the rate at which it will occur (for anonymous and logged in users).  Enter 0 for never.','string'),(16,'dashboard_slots','2x2','Dashboard Slots','The number of dashboard slots for an anonymous user.','string'),(17,'dashboard_width','475','Dashboard Width','The width of dashboard slots for an anonymous user.','string'),(18,'dashboard_height','250','Dashboard Height','The height of dashboard slots for an anonymous user.','string'),(19,'dashboard_font','14','Dashboard Font','The dashboard font size for an anonymous user.','string'),(20,'dashboard_frequency','120','Dashboard Frequency','The frequency that dashboard charts will be changed for an anonymous user.','string'),(21,'alert','','Visual Alert','Display an alert message to users of Quinico on the homepage.  This field supports HTML tags.','string'),(22,'report_path','/opt/quinico-local/report_downloads','Report Download Location','Location on the local file system where Google Pagespeed and Webpagetest raw reports will be saved.  This location must be writeable by the user that runs Apache.','string'),(23,'pagespeed_locale','en','Pagespeed Locale','The locale that Pagespeed results should be generated in.  The only currently supported Locale is en.','string'),(24,'pagespeed_threads','5','Pagespeed Threads','The number of independent worker threads to spawn during data collection.','string'),(25,'wpt_threads','5','Webpagetest Threads','The number of independent worker threads to spawn during data collection.','string'),(26,'keyword_rank_threads','5','Keyword Rank Threads','The number of independent worker threads to spawn during data collection.','string'),(27,'webmaster_threads','5','Webmaster Threads','The number of independent worker threads to spawn during data collection.','string');
/*!40000 ALTER TABLE `main_config` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
