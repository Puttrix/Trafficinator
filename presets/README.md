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
