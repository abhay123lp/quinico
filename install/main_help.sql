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
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `main_help`
--

LOCK TABLES `main_help` WRITE;
/*!40000 ALTER TABLE `main_help` DISABLE KEYS */;
INSERT INTO `main_help` VALUES (5,'/pagespeed/report','<b>Score</b>\r\n<br>\r\n(0-100) indicates how much faster a page could be. A high score indicates little room for improvement, while a low score indicates more room for improvement.\r\n\r\n<br>\r\n<br>\r\n\r\n<b>Impact</b>\r\n<br>\r\nEach PageSpeed rule generates an impact number (an unbounded floating point value) that indicates the importance or priority of implementing the rule-result suggestions for the rule, relative to other rules. For instance, if enabling compression would save 1MB, while optimizing images would save 500kB, the Enable Compression rule would have an impact value that is twice that of the Optimize Images rule. An impact of zero indicates that there are no suggestions for improvement for that rule.\r\n\r\n<br>\r\n<br>\r\n\r\n<b>Key</b>\r\n<table class=\"tiny_no_border_l\">\r\n <tr>\r\n  <td bgcolor=\"#F62217\" width=\"10\">High Priority</td>\r\n  <td>These suggestions represent the largest potential performance wins for the least development effort. You should address these items first.</td>\r\n </tr>\r\n <tr>\r\n  <td bgcolor=\"#FF9900\">Medium Priority</td>\r\n  <td>These suggestions may represent smaller wins or much more work to implement. You should address these items next.</td>\r\n </tr>\r\n <tr>\r\n  <td bgcolor=\"#6699FF\">Low Priority</td>\r\n  <td>These suggestions represent the smallest wins. You should only be concerned with these items after you\'ve handled the higher-priority ones. </td>\r\n </tr>\r\n</table>');
/*!40000 ALTER TABLE `main_help` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
