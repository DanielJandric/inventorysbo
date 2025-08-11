# Rapports PDF

## Banques – Rapport exhaustif
- Endpoint: `GET /api/reports/bank/full`
- Moteur par défaut: WeasyPrint
- Option moderne: Puppeteer via `?engine=puppeteer`

### Ajustements (Puppeteer)
- `scale` (ex: `0.94`)
- `margin` (ex: `12mm`)
- `format` (`A4`)
- `landscape` (`true|false`)
- `wait_until` (`networkidle0`)
- `timeout_ms` (ex: `120000`)

Exemple: `/api/reports/bank/full?engine=puppeteer&scale=0.94&margin=12mm`

## Templates
- `templates/bank_report_full.html`
  - Tables des actifs disponibles par classe/segment
  - Annexes en fin de document: un tableau des actifs vendus par page

## Conseils
- Si le contenu dépasse, diminuer `scale` (0.96 → 0.94 → 0.92)
- Augmenter légèrement `margin` (10mm → 12mm)
- Garder `table-layout: fixed` et polices tabulaires pour chiffres






