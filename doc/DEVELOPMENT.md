# Development

Decktation has a TypeScript/React Decky panel and a Python backend. The backend records audio, runs faster-whisper with CPU int8 inference, parses game-channel prefixes, and starts a controller listener. The packaged plugin includes its runtime dependencies and keyboard helper.

## Build the frontend

Install the Node dependencies and build the panel:

```bash
npm install
npm run build
```

The build writes the compiled panel to `dist/index.js`. Use `npm run watch` while editing the frontend.

## Run the Python tests

Install the test dependencies in a virtual environment, then run the unit tests:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest sentry-sdk==2.66.0
.venv/bin/pytest tests/ -v
```

The CI workflow also runs the Cloudflare worker tests, Python compile checks, and the Decky package build. See [`.github/workflows/build.yml`](../.github/workflows/build.yml) for the current commands and artifact validation.

## Build an installable package

The GitHub Actions workflow builds the installable `decktation.zip` with the Decky CLI and validates that the bundled Python runtime, speech-recognition dependencies, configuration, and keyboard helper are present. To install a development build, download the ZIP artifact from the workflow run and use Decky’s **Install Plugin from ZIP** option. For public branch URLs and artifact notes, see the [installation guide](INSTALLATION.md).
