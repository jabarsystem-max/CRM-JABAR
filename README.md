# 🏥 ZenVit CRM System

Et komplett Customer Relationship Management (CRM) system for ZenVit - et vitamin- og kosttilskuddselskap.

## 🚀 Funksjoner

### ✅ Autentisering
- JWT-basert innlogging med e-post og passord
- Sikker brukerregistrering
- Automatisk token-håndtering

### 📊 Dashboard
- Live KPI-kort for dagens salg, profit og lagerverdi
- Lagerstatus-oversikt med produkt-detaljer
- Månedlige statistikker og bestselgere
- Sanntids-oppdateringer

### 💊 Produktadministrasjon
- Opprett og administrer produkter
- SKU-håndtering
- Salgspris og innkjøpspris
- Kategorier (vitamin, supplement, mineral)

### 📦 Lagerstyring
- Sanntids lagerbeholdning
- Min-nivå varsler for lavt lager
- Lagerverdi-beregninger
- Enkel justering av beholdning

### 👥 Kundeadministrasjon
- Komplett kunderegister
- Kontaktinformasjon
- Bestillingshistorikk

### 🛒 Ordrehåndtering
- Opprett salgsordrer
- Automatisk lager-dekrementering
- Ordre-status og sporbar historikk
- Multi-produkt ordrer

### 🤝 Leverandørstyring
- Leverandør-database
- Kontaktpersoner og detaljer
- Produkt-tilknytning

### 📥 Innkjøp
- Opprett innkjøpsordrer
- Motta varer og oppdater lager automatisk
- Status-sporing (venter/mottatt)

### 💸 Kostnadsstyring
- Registrer faste og variable kostnader
- Kategorier (markedsføring, frakt, software, etc.)
- Total kostnadsanalyse

## 🛠 Teknologi Stack

### Backend
- **FastAPI** - Moderne Python web framework
- **MongoDB** - NoSQL database med Motor (async driver)
- **JWT** - Sikker autentisering
- **Passlib + Bcrypt** - Passord hashing
- **Pydantic** - Data validering

### Frontend
- **React 19** - UI framework
- **React Router** - Navigasjon
- **Axios** - HTTP requests
- **Context API** - State management
- **Custom CSS** - ZenVit-branding med gradients

## 🚦 Kom i gang

### 1. Opprett Admin-bruker
Systemet har allerede en admin-bruker opprettet:
- **E-post:** admin@zenvit.no
- **Passord:** admin123

### 2. Test-data
Systemet har allerede test-data generert:
- 4 ZenVit produkter (D3+K2, Omega-3, Magnesium, C-vitamin+Sink)
- 3 test-kunder
- 2 leverandører
- 18 salgsordrer (dagens salg)
- Lagerbeholdning
- Kostnader

### 3. Logg inn
Gå til applikasjonen og logg inn med admin-brukeren.

## 🔐 Viktige API Endepunkter

### Autentisering
```
POST   /api/auth/register    - Registrer ny bruker
POST   /api/auth/login       - Logg inn (få JWT token)
GET    /api/auth/me          - Hent innlogget bruker
```

### Dashboard
```
GET    /api/dashboard/stats   - Dagens KPI-er og lagerinfo
GET    /api/dashboard/monthly - Månedstall og bestselgere
```

### Produkter, Lager, Kunder, Ordrer, Leverandører, Innkjøp, Kostnader
- Se fullstendig API-dokumentasjon på `/docs` (FastAPI Swagger UI)

## 📊 Dashboard Metrics

### Dagens KPI-er
- **Ordrer:** Antall fullførte ordrer i dag
- **Omsetning:** Total revenue i dag
- **Profit:** Dagens profit (omsetning - varekost)
- **Lagerverdi:** Total verdi av all beholdning
- **Lavt lager:** Antall produkter under min-nivå

### Månedstall
- Omsetning
- Varekost (COGS)
- Andre kostnader
- Netto profit
- Bestselgende produkter

## 🎨 Design

Systemet bruker ZenVit sitt visuelle identitet:
- **ZenVit Base:** #aec7d2 (Blå-grå)
- **D3 + K2:** #f2b98e (Oransje)
- **Omega-3:** #c8dcec (Lys blå)
- **Magnesium:** #9bbca7 (Grønn)
- **C-vitamin + Sink:** #f7db83 (Gul)

## 📝 Brukseksempler

### Opprette ny ordre
1. Gå til **Ordrer**-siden
2. Klikk **+ Ny ordre**
3. Velg kunde
4. Legg til produkter med antall
5. Klikk **Opprett ordre**

### Motta innkjøp
1. Gå til **Innkjøp**-siden
2. Finn innkjøpsordre med status "Venter"
3. Klikk **Motta**

### Sjekke lavt lager
Dashboard viser antall produkter med lavt lager.

## 🔄 Services

Services administreres via Supervisor:
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart all
```

---

**Bygget med ❤️ for ZenVit**
