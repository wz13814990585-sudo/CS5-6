# Build the final source and Web deliveries

This is a maintainer guide, not a client installation step. Clients should start with the root `START_HERE.md`.

Dashboard version remains **1.4.0**; **2026-11-03-en** identifies the English-first delivery revision. No research data or model behavior is changed. Use a clean Git checkout with Python 3.12 Dashboard dependencies and Node.js/npm installed. The source ZIP intentionally has no `.git`; building a Web package requires a checkout, while running the source Dashboard does not.

## Prepare the source

Update documentation, refresh hashes for intentional changes in `RELEASE_MANIFEST.json`, and commit the complete delivery revision. Preserve its original `source_archive` provenance; it is not the SHA-256 of the newly generated ZIP. Verify the source inventory:

```bash
python3.12 tools/check_release.py
git status --short
```

The working tree must be clean for the final build. Record the full commit SHA with `git rev-parse HEAD`. Use a fixed commit/tag when publishing; do not describe an unpublished commit as already on GitHub.

## Build the Web package

```bash
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
.venv-dashboard/bin/python dashboard/tools/build_delivery.py --result FINAL_OUTPUTS/01_saved_model_replay/verified_replay --output deliveries/SafeCapital-Web-1.4.0-20261103-en.zip
```

The explicit `--result` selects the tracked delivered replay rather than a developer's newer local `runs/` folder. The package manifest records the clean source commit. Build into a new output filename if one already exists; the tool refuses to overwrite archives. The Web package includes the root English `START_HERE.md`, the latest presentation script, examples, locked dependencies, verified result bytes, matched inputs, and prebuilt frontend.

## Export the complete source ZIP

```bash
git archive --format=zip --prefix=SafeCapital-Source-1.4.0-20261103-en/ --output=deliveries/SafeCapital-Source-1.4.0-20261103-en.zip HEAD
```

This exports committed files, including datasets, saved models, and reports, without local environments, ignored files, or Git history. The source commit is also stored in the ZIP comment by Git. Use the same commit for both packages. Record SHA-256 and byte size for both archives in companion files.

This command exports locally from the Git repository. After the commit is pushed, the GitHub source archive for that exact commit is another distribution option. GitHub's generated ZIP may have a different top-level folder or compression hash; verify its contents and regenerate checksum records if distributing that file. Uploading to GitHub or posting to the client is a separate publication action.

## Accept the exact archives

1. Extract each ZIP outside the development checkout into a separate empty folder.
2. Follow the matching instructions in `START_HERE.md`; create a fresh Python virtual environment in each extraction. Do not reuse the developer environment. Run `pip check` after installation. For source, use `npm ci` in the extracted frontend and build it there.
3. Start the two services on unused local ports, leaving the existing presentation service untouched.
4. Run the package-specific smoke check against each service, with `--expected-dir` pointing at that package's delivered replay. Run `verify-watchlist.mjs` for successful, invalid-input, and no-data examples. Check English/Chinese pages, module assets, API schema, iframe page, CSV/JSON exports, and real result values.
5. Inspect the two ZIP inventories for unintended credential files, virtual environments, local configs, and temporary logs. Validate file hashes. Do not print potential secret values in validation logs.
6. Record platform, runtime versions, commands/results, source commit, ZIP sizes/hashes, and remaining platform/client-site limits in companion `FINAL_DELIVERY_VALIDATION.md` and `DELIVERY_SUMMARY.json`. Stop temporary servers.

The source and Web services must report the same delivered data and research metrics. This is installation/serving validation, not a rerun of model training. Include the actual logs alongside the final report; do not claim Windows/Linux, Docker, SSO, or production integration from a local macOS check.

The video is recorded separately by the team, using `dashboard/docs/PRESENTATION_SCRIPT_EN.md` as the speaking guide. Do not send the submission template with placeholders still present.
