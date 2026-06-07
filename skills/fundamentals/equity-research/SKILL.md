---
name: equity-research
description: >
  Comprehensive equity research pipeline for Indian listed companies (NSE/BSE).
  Covers the full research lifecycle: Gather -> Analyse -> Model -> Report.
  Scripts produce structured JSON/MD output that the agent interprets and acts on.
  Designed to work as a private tracker, researcher, backtester, and quant engine.
---

# Equity Research Skill

## Overview

Four-phase research pipeline. Scripts are thin data-gatherers — the agent (Claude / OpenCode)
is the analyst. Scripts dump structured output; the agent reads, interprets, and decides next steps.

| GATHER | ANALYSE | MODEL | REPORT |
|---|---|---|---|
| screener | fundamentals | financial model | summary MD |
| concalls | technicals | DCF | tracker |
| drhp | sentiment | backtesting | alerts |
| annual reports | peer compare | quant signals | predictions |

---

## Architecture

At the core of the gather phase is a **PDF/PPT -> Markdown pipeline**:

```
PDF / PPT
  └── pdf_to_md.py          # base transformer: PDF -> clean Markdown (text + tables)
        └── concall_reader.py     # concall-specific: transcript -> structured MD
        └── drhp_reader.py        # DRHP-specific: full doc -> structured MD
        └── annual_report_reader.py  # AR-specific: financials + MD&A -> structured MD
```

Every reader:
1. Downloads the source (PDF or HTML)
2. Converts to Markdown via the base transformer
3. Applies document-specific structuring logic
4. Saves output as `.md` + `.json` (agent reads MD, JSON for programmatic use)

---

## Prerequisites

### 1. Install dependencies
```bash
uv pip install playwright pdfplumber requests
uv run python -m playwright install chromium
```

### 2. Login to screener.in (one-time)
Scripts that access authenticated screener.in data need a saved session.

**Ask the user:** "Which browser do you use? (chromium / firefox / webkit)"

Then run:
```bash
uv run python equity-research/scripts/screener_login.py --browser <chromium|firefox|webkit>
```

- If `SCREENER_TOKEN` exists in `.env.dev`, session is saved automatically — no browser needed.
- Session saved to `~/.screener_session.json` and reused by all scripts.
- Re-run if you get 403 or login errors.

---

## Phase 1 — GATHER

All scripts in `equity-research/scripts/`. Output saved to `output/<symbol>/`.

### Step 1: Search and discover
```bash
uv run python equity-research/scripts/screener_reader.py \
  --search "Jubilant Foodworks" --section all \
  --output output/JUBLFOOD/screener.json

# or direct symbol
uv run python equity-research/scripts/screener_reader.py \
  --symbol JUBLFOOD --section all \
  --output output/JUBLFOOD/screener.json
```

Output `screener.json` — commentary text + full documents index (annual reports, concalls, DRHP URLs).
**This is the input for all subsequent steps.**

---

### Step 2: Concall transcripts
Priority cascade (`concall_reader` does this automatically via `--from-docs`):
**Transcript PDF → AI Summary → PPT → Recording.** Note: BSE transcript PDFs on the `AttachHis`
archive host are **Akamai-gated** (no transport trick beats them) — the reader auto-falls back to
the screener **AI summary** (cleaner key points anyway). PPT decks parse as PDF or `.pptx`.

**Always fetch the last 3 available concalls.** Check `screener.json` documents for available dates, pick the 3 most recent that have a transcript or AI summary.

```bash
# Get available dates first
python -c "
import json
d = json.load(open('output/JUBLFOOD/screener.json'))
for c in d['documents']['concalls'][:6]:
    has = [k for k in ['transcript','ai_summary','ppt'] if c.get(k)]
    print(c['date'], '->', has)
"

# Then fetch last 3 (example for JUBLFOOD as of May 2026)
uv run python equity-research/scripts/concall_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --date "Feb 2026" \
  --output output/JUBLFOOD/concall_feb2026.json

uv run python equity-research/scripts/concall_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --date "Nov 2025" \
  --output output/JUBLFOOD/concall_nov2025.json

uv run python equity-research/scripts/concall_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --date "Aug 2025" \
  --output output/JUBLFOOD/concall_aug2025.json
```

Output: Markdown transcript per concall. Agent reads across quarters for tone shifts, guidance accuracy, key metric evolution.

#### Step 2b: Concall recording → STT (only if a recording is the ONLY source; opt-in, `.[stt]`)
When a concall has just a **recording** (audio/video link, no transcript/AI-summary/PPT), YOU (the
agent) orchestrate transcription — download + convert + **split into 3-min chunks with 30s overlap**
with `yt-dlp`/`ffmpeg`, transcribe each chunk with the thin primitive, then stitch (keep each
chunk's non-overlap region only, so no duplication). The code does NOT auto-do this; it's a
multi-step agent task. Needs system `ffmpeg` + `uv pip install -e '.[stt]'`.

```bash
# 1) download audio
yt-dlp -x --audio-format mp3 -o /tmp/rec.mp3 "<recording_url>"
# 2) duration, then split into 180s windows stepping 150s (=> 30s overlap)
dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 /tmp/rec.mp3)
i=0; start=0
while [ "$(echo "$start < $dur" | bc)" -eq 1 ]; do
  ffmpeg -y -ss $start -t 180 -i /tmp/rec.mp3 /tmp/chunk_$i.mp3 -loglevel error
  uv run --extra stt python equity-research/scripts/concall_reader.py \
     --audio /tmp/chunk_$i.mp3 --model base.en --output /tmp/chunk_$i.txt
  start=$((start+150)); i=$((i+1))
done
# 3) stitch: emit each chunk's first 150s only (the 30s tail is re-covered by the next chunk),
#    except the LAST chunk (emit fully). Then read the stitched transcript for key points.
```
Use a **larger model** (`base.en`/`small.en`) for accuracy; `tiny.en` slips proper nouns (e.g.
"Canara"→"Chandra"). Tested working end-to-end on a real concall recording.

---

### Step 3: DRHP
```bash
uv run python equity-research/scripts/drhp_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --output output/JUBLFOOD/drhp.json

# fallback: Google search if not on screener
uv run python equity-research/scripts/drhp_reader.py \
  --name "Jubilant Foodworks" \
  --output output/JUBLFOOD/drhp.json
```

Output: full DRHP as Markdown. Agent reads to identify risk factors, IPO objects, business model at listing time.

---

### Step 4: Annual reports
**Always fetch the last 3 available years.** Check `screener.json` for available years.

```bash
# See available years
python -c "
import json
d = json.load(open('output/JUBLFOOD/screener.json'))
for r in d['documents']['annual_reports']:
    print(r['label'], '->', r['url'])
"

# Fetch last 3 (example for JUBLFOOD)
uv run python equity-research/scripts/annual_report_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --year 2025 \
  --output output/JUBLFOOD/annual_report_2025.json

uv run python equity-research/scripts/annual_report_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --year 2024 \
  --output output/JUBLFOOD/annual_report_2024.json

uv run python equity-research/scripts/annual_report_reader.py \
  --from-docs output/JUBLFOOD/screener.json \
  --year 2023 \
  --output output/JUBLFOOD/annual_report_2023.json
```

Output: full annual report as Markdown + tables. Agent extracts MD&A, P&L, balance sheet, cash flow, auditor notes across years for trend analysis.

---

## Phase 2 — ANALYSE *(planned)*

Agent-driven analysis on gathered data:
- **Fundamentals** — revenue CAGR, margin trends, ROCE, debt from annual reports
- **Concall sentiment** — tone shifts, guidance accuracy across quarters
- **Peer comparison** — run screener_reader on peers, compare key metrics
- **Pre/post COVID** — DRHP risk language vs recent annual report language
- **Technicals** — `chart-scout` skill for chart screenshots + visual analysis

---

## Phase 3 — MODEL *(planned)*

- **DCF** — from annual report financials
- **Backtesting** — `backtesting` skill + price data from `yfinance`
- **Quant signals** — momentum, RSI, mean reversion via `quant-models` skill

---

## Phase 4 — REPORT *(planned)*

Save to `output/<symbol>/REPORT.md`:
- Company overview (commentary)
- Key risks (DRHP + annual reports)
- Concall theme summary per quarter
- Financial snapshot table
- Buy/Hold/Watch recommendation with rationale

Store findings in memory after each analysis:
```bash
uv run python memory/scripts/memory_store.py insert observations \
  '{"content": "...", "tags": "equity,JUBLFOOD", "source": "concall_feb2026", "confidence": "high"}'
```

---

## Output Convention

```
output/
  <SYMBOL>/
    screener.json
    concall_<date>.json
    drhp.json
    annual_report_<year>.json
    REPORT.md
```

---

## Notes for Agents

- **Always run screener_reader first** — produces the documents index consumed by all other scripts via `--from-docs`.
- **Scripts dump raw data** — you decide what sections matter and how to interpret them.
- **BSE PDFs** need specific headers (baked into scripts) — never use plain `requests.get()` for BSE URLs.
- **Screener authenticated endpoints** (commentary, AI summary) require `~/.screener_session.json`.
- **Store findings in memory** after analysis so future sessions build on prior work.
