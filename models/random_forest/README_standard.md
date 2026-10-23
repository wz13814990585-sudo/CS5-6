# Random Forest Standard Experiment

This version aligns Random Forest with the common experiment protocol used for the current Standard XGBoost comparison.

## Configuration

- Model: `RandomForestRegressor` predicting the continuous forward-aligned weekly `target` log return.
- Factor sets: 5 factors, 7 factors, 7 factors plus 4 macro factors (11 total), and all 45 factors.
- Training history: trailing six calendar years.
- Refit schedule: every 26 calendar weeks.
- Development: all RF candidates are evaluated using Development predictions only. Candidates must satisfy Mean Rank IC > 0, Rank ICIR >= 0.05 and positive Rank IC weeks >= 50%; the passing candidate with the highest Development Top-5 excess annualised return is selected.
- Validation and Final Test: the selected parameters are frozen. Models may refit chronologically every 26 weeks, but no later stage is used to retune parameters.
- Stage labels: each prediction row is assigned from its own signal date, including when a 26-week refit block crosses a stage boundary.
- Preprocessing: median imputation and 1%/99% winsorisation are fitted on each training window only.

## Files

- `random_forest_standard_6y_26w.py`: training and evaluation script.
- `test_45_factors_weekly.csv`: 66-stock weekly input panel.
- `README_standard.md`: this guide.

The script writes the main result CSV and a Development candidate-detail CSV when it runs. The old three-factor result file from the supplied archive is not a result for this four-factor-set protocol and should not be used as the final comparison output.

## Run

```powershell
python -m pip install numpy pandas scikit-learn
python random_forest_standard_6y_26w.py --feature-set all
```

To run one factor set first:

```powershell
python random_forest_standard_6y_26w.py --feature-set 5
```

The factor set names are `5`, `7`, `7_macro`, and `45`.
