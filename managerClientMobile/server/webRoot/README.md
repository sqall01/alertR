alertR Mobile Manager - Server - Web
======

This is the part of the mobile manager that shows the information of the alerting system as a web page. It connects to the MySQL db and displays all gathered information. The mobile device clients connect to this web page and show the user all details.


How to use it?
======

To use this part you have to configure it first. A commented configuration template file is located inside the "config" folder. The web page is written in PHP5 and therefore needs a webserver with PHP and MySQL db installed.

Nevertheless, a short but more detailed example of how to set up the server is given below.


Configuration example
======

```bash
#################### install packets ####################

in this example we use apache as a webserver and assume that you already installed/configured the manager client mobile

---

root@webserver:/home/sqall# apt-get install apache2 php5-mysql


#################### configure web page ####################


sqall@webserver:/var/www/alertR/config$ vim config.conf

<?php

$configMysqlDb = "alertr_mobile_manager";
$configMysqlUsername = "alertr_mobile";
$configMysqlPassword = "<SECRET>";
$configMysqlServer = "localhost";
$configMysqlPort = 3306;
$configUnixSocket = "/home/sqall/alertR/managerClientMobile/config/localsocket";

?>


#################### configure htaccess ####################

sqall@webserver:/var/www/alertR$ vim .htaccess

AuthUserFile /var/www/alertR/.htpasswd
AuthName "alertR mobile manager"
AuthType Basic
Require valid-user

sqall@webserver:/var/www/alertR$ htpasswd -c testfile mobile_user
New password: <SECRET>
Re-type new password: <SECRET>
```