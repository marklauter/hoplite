---
title: Marketplace rename to msl.armory
summary: The plugin's marketplace identity stabilizes as msl.armory; personal fields scrubbed from the manifest so the package shape matches what gets shipped to other users.
document:
  tags: [journal, marketplace, plugin, decision]
  created: 2026-05-16
---

# Marketplace rename to msl.armory

The plugin's marketplace identity stabilizes as `msl.armory`; personal fields scrubbed from the manifest so the package shape matches what gets shipped to other users.

## Intent

Settle the marketplace name. Until now the manifest carried experimentation-grade fields — author defaults, scratch text, working-name placeholders — that work fine for local installs but look wrong in a marketplace listing.

## What landed

- Marketplace renamed to `msl.armory`. The `msl` prefix is the author namespace; `armory` names the package.
- Personal fields scrubbed from the manifest.

## Decisions captured

- Marketplace identity gets locked once and references propagate from there. Naming churn cascades into install URLs, docs, and the README; the cost of a rename later is higher than the cost of picking deliberately now.
- The author-namespace + package-name shape (`msl.armory`) keeps room for sibling packages later without colliding with anyone else's plugins.

## Next

The plugin name survives until late on 2026-05-25, when the repo split temporarily renames the package `hoplite` and then settles back on `armory` for the surviving Claude-repo plugin. See `[[journal/2026-05-25-1934-skill-md-to-component-and-the-repo-split]]`.
