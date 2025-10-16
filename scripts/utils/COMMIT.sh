#!/bin/bash
# Final commits

git add src/medallion scripts docs data
git commit -m "refactor(core): modularize medallion pipeline into clean architecture

- src/medallion/: orchestrator + activities pattern
- scripts/setup/: data generators
- scripts/utils/: utilities
- docs/guides/: documentation
- data/: organized layers (bronze/silver/gold)"

git commit -m "feat(docs): complete guides for middle-level engineers" 
git commit -m "feat(test): 40 CSV generator for validation"
git commit -m "feat(automation): one-command pipeline execution"
