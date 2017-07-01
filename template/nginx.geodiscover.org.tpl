server {
    listen 80;
    server_name www.%(proj_name)s;
    rewrite ^(.*) http://%(proj_name)s$1  permanent;
}

server {
    listen 80;
    server_name lk.%(proj_name)s;
    location / {
        root /%(proj_path)s;
        index index.html index.php;
    }
}


server {
    listen 80;
    server_name api.%(proj_name)s;
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://content.sancta.ru;
   }

}



server {
    listen 80;

    server_name %(proj_name)s;

    client_max_body_size 10M;
    keepalive_timeout    15;
    access_log  /var/log/nginx/%(proj_name)s.access.log;
    error_log   /var/log/nginx/%(proj_name)s.error.log;

    location ~* ^.+.(php)$ {
        deny all;
    }

    location ~* ^/wp-content/.*$ {
        deny all;
    }

   location / {
        root /%(proj_path)s;
        index index.html index.php;
    }
}