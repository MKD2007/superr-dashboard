# Players under pressure - dashboard

Streamlit dashboard for the SupeRR Selector S2 pressure ratings. It reads precomputed results from `data/` and does not rerun the model.

## Run
    pip install -r requirements.txt
    streamlit run app.py

Opens at http://localhost:8501.

## Pages
Final top 10 (batters / bowlers toggle) | Pressure vs normal scatter | Player explorer | Stability (sensitivity tests) | Method

## Data (`data/`)
- `players.csv` - all 92 eligible batters and 100 bowlers (role, ranks, pressure and normal-play stats, scores, top-10 share). `final_rank` is the submitted top-10 order (tie-break applied); `comp_rank` is the composite-score order. Scores are per ball; the app shows them per 100 balls.
- `sens_bat.csv`, `sens_bwl.csv` - sensitivity tests (names kept out of 10 when one choice changes).
