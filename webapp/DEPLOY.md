# Deploy — CPT Su Tool (container) op de Hetzner-server

De tool draait als **één geïsoleerde Docker-container**. Hij raakt niets anders op de
server aan: alleen deze container + de gekozen poort.

Server: `178.104.119.117`

## Vereisten op de server (eenmalig)
- Docker + Docker Compose plugin. Check:
  ```bash
  docker --version && docker compose version
  ```
  Niet aanwezig? Installeer (Ubuntu/Debian):
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```

## 1. Code naar de server
Optie A — via git (aanrader):
```bash
ssh <gebruiker>@178.104.119.117
git clone https://github.com/Bader914/CPT-Tool.git
cd CPT-Tool/webapp
```
Optie B — map kopiëren met scp:
```bash
scp -r webapp <gebruiker>@178.104.119.117:~/cpt-tool
ssh <gebruiker>@178.104.119.117
cd ~/cpt-tool
```

## 2. Bouwen en starten
```bash
docker compose up -d --build
```
De tool draait nu op poort **8080** van de server:
`http://178.104.119.117:8080`

## 3. Beheer
```bash
docker compose ps          # status
docker compose logs -f     # logs
docker compose restart     # herstarten
docker compose down        # stoppen (verwijdert alleen deze container)
```

## 4. Updaten naar een nieuwe versie
```bash
git pull            # of nieuwe webapp-map kopiëren
docker compose up -d --build
```

## Poort aanpassen
Bezet 8080 al iets? Wijzig in `docker-compose.yml` de regel
`- "8080:8000"` naar bijv. `- "9090:8000"` en draai opnieuw `docker compose up -d`.

## Optioneel — HTTPS / mooie URL
Zet er een reverse proxy (Caddy/Nginx) of Cloudflare voor. De container blijft
intern op poort 8000; de proxy regelt 443/TLS. Aparte container, raakt de rest niet.

## Firewall
Zorg dat de gekozen hostpoort openstaat:
```bash
sudo ufw allow 8080/tcp   # alleen als ufw actief is
```
