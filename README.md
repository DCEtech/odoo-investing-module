# Odoo Investing Module

Custom Odoo 19 module for investment portfolio tracking with Yahoo Finance integration.

## Features

- **Company tracking** — track stocks and crypto by ticker symbol with automatic sector and currency detection
- **Portfolio management** — track shares and purchase price per asset with weighted average cost calculation on additional purchases
- **Computed metrics** — current value, profit/loss and ROI (%) updated automatically when prices sync
- **Price history** — full year of daily close price and volume fetched from Yahoo Finance on each sync
- **Automated sync** — daily cron job keeps all company prices up to date
- **Manual sync** — per-company Sync button and global Sync All action from the list view
- **FIFO sales** — sales consume the oldest lots held at the sale date (art. 37.2 LIRPF); overselling is rejected
- **Fiscal year tax estimate** — nets the year's gains and losses, applies the two-month rule, loss carryforward, the 25 % offset against other savings income and the configured tax scale (IRPF common territory or IRNR)
- **Configurable tax scales** — rates per regime and fiscal year as data records (Investing > Configuration > Tax Scales)

## Models

| Model | Description |
|---|---|
| `investing.company` | Tracked asset with ticker, sector, currency and current price |
| `investing.portfolio` | Position per asset with shares, purchase price and computed P&L |
| `investing.price.history` | Daily OHLCV history populated automatically on sync |
| `investing.buy.sell.history` | Buy lots (with remaining shares) and sales with realized profit |
| `investing.tax.scale` | Tax brackets per regime and fiscal year |
| `investing.tax.year` | Tax estimate of a fiscal year, with one line per sale |

## Requirements

- Odoo 19.0
- Python 3.12+
- `yfinance` library

```bash
pip install yfinance
```

## Installation

1. Copy the `investing` folder to your Odoo `custom_addons` directory
2. Add the path to `addons_path` in your `odoo.conf`
3. Install the module from Apps or via CLI:

```bash
python odoo-bin -c odoo.conf --stop-after-init -d <your_db> --init investing
```

## Tax estimate limitations

The estimate is indicative and is **not tax advice**:

- Fees and the conversion to EUR at each operation's exchange rate are not included yet.
- The two-month rule is simplified (deferred loss proportional to homogeneous buys in the
  window; deferred losses are not re-integrated automatically) and it does not
  distinguish listed from unlisted securities.
- Supported regimes: resident in the common territory (IRPF) and non resident without
  permanent establishment (IRNR). Foral territories and companies are not supported.

## Security

Two groups are available:

- **Investing Manager** — full CRUD access
- **Investing User** — read-only access

## Author

Daniel Cejudo Echeverry
