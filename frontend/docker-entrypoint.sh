#!/bin/sh
echo "API: $(grep -o 'https\?://[^"]*odiga-server[^"]*' /usr/share/nginx/html/assets/index-*.js | head -1)"
exec nginx -g "daemon off;"
