# Package Structure & Domain Clustering

## Top Directive: Modularize

Configurations are never written monolithically into root files. Split them into thematic packages under `/config/packages/`.

## Package Layout

```
abstraction/   # Abstraction layers (energy_power.yaml)
bsm/           # Battery/storage management
car/           # Vehicle charging / APIs
fitness/       # Fitness & health tracking
grid/          # Grid / spot prices
heating/       # Heating control
home/          # Core: climate, window_monitoring, air_quality
home_appliances/ # Household appliances
location/      # Presence, GPS, zones
mining/        # Crypto mining
report/        # Reporting & statistics
solar/         # Solar: dtu, solarforecast, solarmanager
weather/       # Weather
```

## Principles

- One package = one domain; one file = one sub-topic
- Root files stay empty or use `!include_dir_merge_list packages/`
- Every package is self-contained

## Mandatory File Header

```yaml
# ==============================================================================
# PACKAGE: [Domain] - [Sub-Topic]
# Description: [1-2 sentences]
# Dependencies: [integrations]
# ==============================================================================
# Input Helpers → Template Sensors → Automations → Scripts → Scenes
```

## When to Split?

- New file: new sub-topic, file >500 lines, or sub-topic has 5+ entities
- New package: new top-level domain, expect 2–3 YAML files, independent from others

## Naming

- Domain: `[domain].yaml` (e.g. `climate.yaml`)
- Hardware: `[hardware].yaml` (e.g. `dtu.yaml`)
- Function: `[fn]_[obj].yaml` (e.g. `window_monitoring.yaml`)

## Troubleshooting

- Package not loaded → `Developer Tools → Check Configuration`
- Duplicate entities → empty the root file
- Reload not enough → full restart (new domain added)
