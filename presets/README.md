# Trafficinator Load Presets

Preset environment files make it easy to start Trafficinator with opinionated configurations:

| Preset | Visits / Day | Concurrency | Typical Use |
|--------|--------------|-------------|-------------|
| `.env.light`   | ~1,000  | 10   | Local development, smoke tests |
| `.env.medium`  | ~10,000 | 50   | Production-simulated workload |
| `.env.heavy`   | ~50,000 | 150  | Stress and capacity testing |
| `.env.extreme` | ~100,000| 300  | Maximum stress / enterprise scale |

## Usage

1. Copy the template that best matches your scenario:
   ```bash
   cp presets/.env.medium .env
   # Edit MATOMO_URL, MATOMO_SITE_ID, MATOMO_TOKEN_AUTH as needed
   ```

2. Launch the generator:
   ```bash
   docker compose --env-file .env up -d
   # or include -f docker-compose.webui.yml for the Control UI stack
   ```

You can also reference the presets directly:

```bash
docker compose --env-file presets/.env.light up --build
docker compose -f docker-compose.webui.yml --env-file presets/.env.heavy up -d
```

Each preset mirrors the values shown in the Control UI’s Presets tab. Feel free to duplicate and customise them for additional tiers.

### Backfill (optional)

Backfill is off by default. To enable historical replay, add these env vars to your `.env` (or set via the Control UI):

- `BACKFILL_ENABLED=true`
- One of:
  - `BACKFILL_START_DATE=2024-10-01` and `BACKFILL_END_DATE=2024-10-31`
  - `BACKFILL_DAYS_BACK=30` and `BACKFILL_DURATION_DAYS=30`
- Caps: `BACKFILL_MAX_VISITS_PER_DAY=2000` (max 10000), `BACKFILL_MAX_VISITS_TOTAL=200000` (0 to disable)
- Optional: `BACKFILL_RPS_LIMIT=25`, `BACKFILL_SEED=42`

Guards: windows must end on/before today, max 180 days; total cap must be ≥ per-day cap.
