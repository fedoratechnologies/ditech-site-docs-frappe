# Ditech Site Docs (Frappe app)

Custom DocTypes for storing MSP “Site Docs” inside ERPNext/Frappe, replacing ad-hoc spreadsheets:

- **MSP Site** — client/site master record
- **MSP Site Device** — equipment inventory (serial/MAC/IPs/notes)
- **MSP Site Account** — credentials + vendor accounts (restricted role)
- **MSP Google Workspace** — per-site Google Admin config (credential stored in Password field)
- **MSP Site User** — Google Workspace user inventory
- **MSP Insurance Policy** + **MSP Insurance Transaction** — annual insurance coverage + audited deductions ledger
- **MSP Device Event** — device lifecycle history (status/assignment/repairs)

## Install (bench)

From a bench instance:

```bash
cd ~/frappe-bench
bench get-app /path/to/site-docs-frappe
bench --site ditech.fedoratechnologies.net install-app ditech_site_docs
bench --site ditech.fedoratechnologies.net migrate
```

## Roles + permissions

On install, the app creates roles and sets DocType permissions:

- `Ditech Site Docs User` — read Site + Device
- `Ditech Site Docs Manager` — create/write Site + Device
- `Ditech Credentials Admin` — access MSP Site Account (password fields)
- `Ditech Insurance Admin` — manage insurance policies + submit transactions

`System Manager` keeps full access.
