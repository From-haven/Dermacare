# DermaCare Agent — Web Frontend Production Dockerfile
FROM nginx:alpine

# Copy static frontend assets
COPY apps/web /usr/share/nginx/html

# Copy custom Nginx configuration
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /static/ { \
        alias /usr/share/nginx/html/; \
    } \
    location /api/ { \
        proxy_pass http://api:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
    location /health { \
        proxy_pass http://api:8000; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
