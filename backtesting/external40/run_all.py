"""Reproduce both prediction audits, integer backtests, metrics and figures."""
from pathlib import Path
import subprocess,sys
HERE=Path(__file__).resolve().parent
for script in ['prepare_comparison.py','replay_old50.py','integer_backtest.py','verify_integer.py','evaluate_comparison.py']:
    subprocess.run([sys.executable,str(HERE/script)],cwd=HERE,check=True)
subprocess.run(['Rscript',str(HERE/'plot_results.R'),str(HERE)],cwd=HERE,check=True)
subprocess.run([sys.executable,str(HERE/'build_report.py')],cwd=HERE,check=True)
extension=HERE/'ensemble_extension'
if extension.exists():
    for script in ['complete_ensemble.py','verify_extension.py','evaluate_extension.py']:
        subprocess.run([sys.executable,str(extension/script)],cwd=HERE,check=True)
    subprocess.run(['Rscript',str(extension/'plot_extension.R'),str(extension)],cwd=HERE,check=True)
    subprocess.run([sys.executable,str(extension/'extend_report.py')],cwd=HERE,check=True)
if (HERE/'report_app/src/data.json').exists():
    subprocess.run([sys.executable,str(HERE/'sync_report_app.py')],cwd=HERE,check=True)
print('Numerical results, figures and Markdown are complete. To rebuild the optional interactive app, use the Data plugin build command documented in README.md.')
