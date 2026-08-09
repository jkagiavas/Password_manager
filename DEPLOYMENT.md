# Deployment Guide — Password Manager on VPS

This document describes the full deployment process on a Hetzner VPS
with Nginx, systemd, and SSL. Written as both a reference and a learning record.

## 1. Server Provisioning
## 2. Initial Server Setup
## 3. Clone the Project
## 4. Python Environment
## 5. Environment Variables & Keys
## 6. Systemd Service
## 7. Nginx Configuration
## 8. DNS Setup
## 9. SSL Certificate

## 2. Initial Server Setup

# Connect to the server via SSH (using the SSH key added during provisioning)
ssh root@<server-ip>

# Update package lists and upgrade installed packages
apt update && apt upgrade -y

# Install Python, pip, venv, Nginx and git in one go
apt install -y python3 python3-pip python3-venv nginx git

## 3. Clone the Project

# Projects live in /var/www (standard web content location)
cd /var/www

# Clone via SSH (no credentials prompt - server needs an SSH key added to GitHub)
# Note: if the repo has multiple branches, make sure the default branch
# on GitHub is the one with the code (we hit this: main was empty, code was on master)
git clone git@github.com:jkagiavas/Password_manager.git
cd Password_manager

## 4. Python Environment

# Create a virtual environment inside the project folder
python3 -m venv .venv

# Activate it (needed before any pip install or python run)
source .venv/bin/activate

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Note: .venv must NEVER be committed to git (it's in .gitignore)
# We learned this the hard way - a committed .venv broke the first clone
# and had to be removed with: git rm -r --cached .venv

## 5. Environment Variables & Keys

# These files are NOT in git (see .gitignore) and must be created/copied manually:
#   .env          - SECRET_KEY for JWT signing
#   secret.key    - Fernet encryption key (encrypts stored passwords)
#   master.key    - bcrypt hash of the master password
#   passwords.db  - the SQLite database

# Copy existing keys/data from local machine to preserve encrypted data
# (a NEW secret.key would make old encrypted passwords unreadable!)
scp ~/projects/day29_password/secret.key root@<server-ip>:/var/www/Password_manager/
scp ~/projects/day29_password/master.key root@<server-ip>:/var/www/Password_manager/
scp ~/projects/day29_password/passwords.db root@<server-ip>:/var/www/Password_manager/

# Create .env on the server with a strong random key
nano .env
# Content: SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">

## 6. Systemd Service

# Systemd keeps the API running permanently:
# - starts automatically on server boot
# - restarts automatically if it crashes

# Create the service file
nano /etc/systemd/system/passmanager.service

passmanagere.service contents """
[Unit]
Description=Password Manager FastAPI
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/Password_manager
Environment="PATH=/var/www/Password_manager/.venv/bin"
EnvironmentFile=/var/www/Password_manager/.env
ExecStart=/var/www/Password_manager/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

"""

# Reload systemd to see the new service file
systemctl daemon-reload

# Enable = start automatically on boot
systemctl enable passmanager

# Start it now
systemctl start passmanager

# Check it's running
systemctl status passmanager

## 7. Nginx Configuration

# Nginx acts as a reverse proxy:
#   jkayabas.gr/           -> Flask blog (port 5000)
#   jkayabas.gr/passmanager -> FastAPI web frontend (port 8000)
#   jkayabas.gr/api/       -> FastAPI backend (port 8000)

# Create the site config
nano /etc/nginx/sites-available/passmanager

# Enable it by linking into sites-enabled
ln -s /etc/nginx/sites-available/passmanager /etc/nginx/sites-enabled/

# Remove the default site so it doesn't override ours
rm /etc/nginx/sites-enabled/default

# Test the config syntax BEFORE loading (t = test) — saved us from crashing Nginx
nginx -t

# If syntax is OK, reload Nginx to apply
systemctl reload nginx

# --- Content of /etc/nginx/sites-available/passmanager ---


# Nginx is a REVERSE PROXY: it sits in front of everything, listens on
# port 80 (http), looks at the URL path, and forwards each request to the
# right program running internally on the server.

server {
    listen 80;                              # listen for http traffic on port 80
    server_name jkayabas.gr www.jkayabas.gr;  # which domain this config answers for

    # Max upload size (default is 1MB - too small for article images)
    client_max_body_size 10M;

    # 'alias' = serve real files straight from this folder on disk.
    # Faster than going through the Flask app for images/CSS.
    location /static {
        alias /var/www/FlaskBlogApp/src/FlaskBlogApp/static;
    }

    # 'proxy_pass' = forward the request to another program (NOT a folder).
    # 127.0.0.1 means "this same server" (localhost).
    # Path '/' -> Flask blog running internally on port 5000
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;          # pass the real domain to the app
        proxy_set_header X-Real-IP $remote_addr;  # pass the visitor's real IP
    }

    # Path '/passmanager' -> FastAPI web frontend on port 8000
    location /passmanager {
        proxy_pass http://127.0.0.1:8000/app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Path '/api/' -> FastAPI backend on port 8000
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}


## 8. DNS Setup (Papaki)

# Point the domain to the server's IP.
# Changed the A record in the Papaki DNS panel:
#   Type A   | Host: jkayabas.gr      | Value: <server-ip>  (was Render's IP)
#   Type A   | Host: www.jkayabas.gr  | Value: <server-ip>  (replaced old CNAME to Render)
#
# TTL is 1 hour, so propagation can take up to an hour.
# Check propagation from local machine with:
ping jkayabas.gr   # should show the new server IP


## 9. SSL Certificate (Let's Encrypt)

# Install Certbot (system tool, not in the venv)
apt install -y certbot python3-certbot-nginx

# Get and install the certificate. Certbot edits the Nginx config
# automatically to enable https and redirect http -> https.
# IMPORTANT: DNS must already point to this server, or verification fails.
certbot --nginx -d jkayabas.gr -d www.jkayabas.gr

# Certbot auto-renews via a systemd timer. Test renewal with:
certbot renew --dry-run

