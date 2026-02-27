# Communication Analysis Dashboard

A React-based visualization interface for the Communication Analysis Toolkit.

## Overview
This dashboard provides a visual layer over the analysis engine's output (`DATA.json` / `cases.db`). It allows researchers and analysts to:
- **Visualize Timelines:** Interactive heatmaps of communication frequency.
- **Inspect Patterns:** Filterable view of detected behavioral patterns (e.g., "gaslighting", "darvo").
- **Review Evidence:** Read message threads in context with severity highlighting.

## Tech Stack
- **Framework:** React 18 + Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS + ShadcnUI
- **Charts:** Recharts

## Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Architecture
This is a **client-side only** dashboard. It loads data directly from local analysis artifacts. No data is sent to external servers.
