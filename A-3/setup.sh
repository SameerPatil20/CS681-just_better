cp dockerStart.php dockerStop.php /var/www/html/
docker build -t server_image:1.0 .
chmod 777 client_script.sh
