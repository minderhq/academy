# SSL/TLS Certificate Setup for PROJECT-OMEGA

## Overview
Secure all PROJECT-OMEGA services with SSL/TLS certificates using Let's Encrypt and self-signed certificates for internal services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSL/TLS Configuration                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  External Services:          Internal Services:                  │
│  ┌──────────────────┐        ┌──────────────────┐               │
│  │  Let's Encrypt   │        │  Self-Signed     │               │
│  │  (omega.local)   │        │  Certificates    │               │
│  └──────────────────┘        └──────────────────┘               │
│           │                          │                          │
│           ▼                          ▼                          │
│  ┌──────────────────────────────────────────────────┐           │
│  │              Nginx Reverse Proxy                 │           │
│  │  - SSL Termination                               │           │
│  │  - Certificate Auto-Renewal                      │           │
│  │  - OCSP Stapling                                 │           │
│  └──────────────────────────────────────────────────┘           │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────┐           │
│  │          Internal Services (HTTPS)               │           │
│  │  - Grafana, Prometheus, Loki                     │           │
│  │  - Qdrant, Neo4j                                 │           │
│  │  - vLLM, TGI, ReAct Agent                        │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start: Let's Encrypt

### 1. Install Certbot

```bash
# On Synology NAS
sudo apt-get update
sudo apt-get install certbot

# Or use Docker
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot:latest
```

### 2. Generate Certificate (HTTP-01 Challenge)

```bash
# Stop nginx temporarily
docker-compose -f docker-compose-complete.yml stop nginx

# Generate certificate
certbot certonly --standalone \
  -d omega.local \
  -d grafana.omega.local \
  -d prometheus.omega.local \
  --email admin@omega.local \
  --agree-tos \
  --non-interactive

# Start nginx
docker-compose -f docker-compose-complete.yml start nginx
```

### 3. Configure Nginx with SSL

```nginx
# /etc/nginx/nginx.conf

http {
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_trusted_certificate /etc/nginx/ssl/chain.pem;

    # Modern SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # SSL Session Cache
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    server {
        listen 443 ssl http2;
        server_name omega.local;

        location / {
            proxy_pass http://grafana;
            # ... proxy configuration
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name omega.local;
        return 301 https://$server_name$request_uri;
    }
}
```

### 4. Auto-Renewal with Cron

```bash
# Add to crontab
crontab -e

# Renew certificates twice daily
0 */12 * * * certbot renew --quiet --post-hook "docker-compose -f /path/to/docker-compose-complete.yml restart nginx"
```

## Self-Signed Certificates for Internal Services

### Generate CA and Certificates

```bash
#!/bin/bash
# generate-certs.sh

# Create CA
openssl genrsa -out ca-key.pem 4096
openssl req -x509 -new -nodes -sha512 \
  -key ca-key.pem \
  -days 3650 \
  -out ca.pem \
  -subj "/C=US/ST=State/L=City/O=PROJECT-OMEGA/CN=PROJECT-OMEGA-CA"

# Generate server certificate
openssl genrsa -out server-key.pem 4096
openssl req -sha512 -new \
  -key server-key.pem \
  -out server.csr \
  -subj "/C=US/ST=State/L=City/O=PROJECT-OMEGA/CN=*.omega.local"

# Sign with CA
openssl x509 -req -sha512 \
  -in server.csr \
  -CA ca.pem \
  -CAkey ca-key.pem \
  -CAcreateserial \
  -out server-cert.pem \
  -days 365 \
  -extfile <(printf "subjectAltName=DNS:*.omega.local,DNS:omega.local")

# Create fullchain
cat server-cert.pem ca.pem > fullchain.pem
```

### Use in Docker Compose

```yaml
services:
  grafana:
    volumes:
      - ./certs/fullchain.pem:/etc/grafana/tls.crt:ro
      - ./certs/server-key.pem:/etc/grafana/tls.key:ro
    environment:
      - GF_SERVER_PROTOCOL=https
      - GF_SERVER_CERT_FILE=/etc/grafana/tls.crt
      - GF_SERVER_CERT_KEY=/etc/grafana/tls.key

  prometheus:
    volumes:
      - ./certs/fullchain.pem:/etc/prometheus/tls.crt:ro
      - ./certs/server-key.pem:/etc/prometheus/tls.key:ro
    command:
      - '--tls.config'
      - '/etc/prometheus/tls.yml'
```

## Service-Specific Configuration

### Qdrant SSL

```yaml
qdrant:
  environment:
    - QDRANT__SERVICE__TLS_CERT=/etc/qdrant/tls.crt
    - QDRANT__SERVICE__TLS_KEY=/etc/qdrant/tls.key
    - QDRANT__SERVICE__ENABLE_TLS=true
  volumes:
    - ./certs:/etc/qdrant:ro
```

### Neo4j SSL

```yaml
neo4j:
  environment:
    - NEO4J_dbms_ssl_policy_bolt_enabled=true
    - NEO4J_dbms_ssl_policy_bolt_base_directory=certificates/bolt
    - NEO4J_dbms_ssl_policy_bolt_private_key=private.key
    - NEO4J_dbms_ssl_policy_bolt_public_certificate=public.crt
    - NEO4J_dbms_ssl_policy_bolt_client_auth=NONE
  volumes:
    - ./certs/neo4j:/var/lib/neo4j/certificates:ro
```

### Grafana SSL

```yaml
grafana:
  environment:
    - GF_SERVER_PROTOCOL=https
    - GF_SERVER_CERT_FILE=/etc/grafana/tls.crt
    - GF_SERVER_CERT_KEY=/etc/grafana/tls.key
  volumes:
    - ./certs:/etc/grafana:ro
```

## Certificate Automation

### Auto-Renewal Script

```bash
#!/bin/bash
# /opt/scripts/renew-certs.sh

LOG_FILE="/var/log/cert-renewal.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check certificate expiration
check_cert_expiry() {
    local cert_file="$1"
    local days_valid=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2 | \
        awk '{print $1}' | xargs -I {} date -d {} +%s | \
        awk '{print ($1 - systime()) / 86400}')
    echo "$days_valid"
}

# Renew certificate if expiring soon
renew_if_needed() {
    local cert_file="$1"
    local days_before=30

    days_valid=$(check_cert_expiry "$cert_file")
    log "Certificate $cert_file is valid for $days_valid days"

    if (( $(echo "$days_valid < $days_before" | bc -l) )); then
        log "Renewing certificate $cert_file"
        certbot renew --force-renewal
        docker-compose restart nginx
    else
        log "Certificate does not need renewal"
    fi
}

# Main
renew_if_needed "/etc/letsencrypt/live/omega.local/fullchain.pem"
```

## Certificate Monitoring

### Prometheus Exporter

```go
// cert-exporter.go
package main

import (
    "crypto/x509"
    "encoding/pem"
    "io/ioutil"
    "time"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    "net/http"
)

var certExpiry = prometheus.NewGaugeVec(
    prometheus.GaugeOpts{
        Name: "certificate_expiry_days",
        Help: "Days until certificate expires",
    },
    []string{"domain"},
)

func checkCert(path string) error {
    data, err := ioutil.ReadFile(path)
    if err != nil {
        return err
    }

    block, _ := pem.Decode(data)
    if block == nil {
        return fmt.Errorf("failed to decode certificate")
    }

    cert, err := x509.ParseCertificate(block.Bytes)
    if err != nil {
        return err
    }

    daysUntilExpiry := time.Until(cert.NotAfter).Hours() / 24
    certExpiry.WithLabelValues(path).Set(daysUntilExpiry)

    return nil
}

func main() {
    prometheus.MustRegister(certExpiry)

    http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
        checkCert("/etc/letsencrypt/live/omega.local/fullchain.pem")
        promhttp.Handler().ServeHTTP(w, r)
    })

    http.ListenAndServe(":9101", nil)
}
```

## Troubleshooting

### Check Certificate Validity

```bash
# Check certificate details
openssl x509 -in fullchain.pem -text -noout

# Check certificate expiration
openssl x509 -in fullchain.pem -noout -enddate

# Test SSL connection
openssl s_client -connect omega.local:443 -servername omega.local
```

### Verify SSL Configuration

```bash
# Test SSL with curl
curl -I https://omega.local

# Check SSL Labs rating
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=omega.local

# Check certificate chain
openssl s_client -connect omega.local:443 -showcerts
```

### Common Issues

1. **Certificate Mismatch**
   ```bash
   # Verify SAN includes all domains
   openssl x509 -in fullchain.pem -noout -text | grep -A1 "Subject Alternative Name"
   ```

2. **OCSP Stapling Issues**
   ```bash
   # Test OCSP
   openssl s_client -connect omega.local:443 -status | grep -A 10 "OCSP response"
   ```

3. **Mixed Content Warnings**
   ```nginx
   # Ensure all resources use HTTPS
   add_header Content-Security-Policy "upgrade-insecure-requests" always;
   ```

## Related Documentation

- [1501: Monitoring and Observability](../../docs/1000-Infrastructure-Fabric/1500-Monitoring/1501-Monitoring-and-Observability.md)
- [nginx/nginx.conf](../nginx/nginx.conf)
- [ci-cd/.github/workflows/deploy.yml](../ci-cd/.github/workflows/deploy.yml)
