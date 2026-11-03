# CS5-6 — English submission message

Replace the bracketed placeholders with the actual attachments/links before posting. This is a draft for the team; it has not been sent to the client. The video is recorded separately by the team.

---

Hi Burak and team,

Please find our final **CS5-6 — Model-Based Stock Strategies** delivery for Portfolio Neo / Strategy Lab:

- **Demonstration video:** [attach the recorded video or insert its accessible link]
- **Complete source ZIP:** `SafeCapital-Source-1.4.0-20261103-language-switch.zip`
- **Prebuilt Dashboard package:** `SafeCapital-Web-1.4.0-20261103-language-switch.zip`
- **Repository:** https://github.com/wz13814990585-sudo/CS5-6
- **Final source commit / published version:** [insert the commit from DELIVERY_SUMMARY.json and its GitHub link after publication]
- **Setup guide:** `START_HERE.md` inside either ZIP. The final validation report and SHA-256 checksums accompany the packages.

**Setup:** The prebuilt Web package needs 64-bit Python 3.12 only. After extraction, run `python3.12 verify_delivery.py`, `python3.12 install.py`, then `.venv-dashboard/bin/python dashboard/start.py --config config.toml`. Open `http://127.0.0.1:8000/?lang=en#watchlist`. Windows commands and source-package instructions are in the setup guide. The source-package Dashboard additionally requires Node.js/npm and a frontend build. Docker is not required.

**API keys:** No API key or credentials are required for the delivered Dashboard or the supplied-data frozen replay. No actual API keys or credentials are included. Dependency installation needs internet access; the installed Dashboard reads local historical data. The optional Swagger documentation UI uses an external CDN, with an offline OpenAPI JSON supplied.

**Features:** English/Chinese interface, separate English/Chinese README and installation pages with reciprocal language links, stock watchlists, historical factor inputs and model rankings, actual strategy stocks and weights, performance and drawdown charts, and CSV/JSON exports. Selecting followed stocks changes the displayed view; it does not recalculate the original strategy portfolio or returns.

**Integration:** The module supports an independent iframe or read-only APIs under `/api/cs5_6_equity/v1`. OpenAPI and executable examples are included. The client team can add an entry in Strategy Lab while keeping our module and research engine separate from other modules and the page-wide single-asset selector.

**Scope:** These are historical simulations using the supplied research data, not live trading or future-return guarantees. Customer hosting, final allowed origins, authentication/SSO, and staging verification remain to be agreed with the core team. The local embedding demonstration is included; we do not claim deployment on the client's production site.

Thank you.
