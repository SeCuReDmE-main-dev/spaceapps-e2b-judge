# Building & Using the Pre-Baked E2B Sandbox Template (`spaceapps-judge-v3`)

I designed `spaceapps-e2b-judge` so that it works **out of the box** on any standard E2B account (automatically installing `playwright`, `pypdf`, `python-pptx`, `langdetect`, and `@google/gemini-cli` if they are not already present in the sandbox).

If you want **instant `< 2s` MicroVM cold starts** without waiting ~60s for `playwright` and `npm` setup on each run, you can build the pre-baked template from this directory:

## 1. Install the E2B CLI & Authenticate

```bash
npm install -g @e2b/cli
e2b auth login
```

## 2. Build the Template

```bash
cd e2b_template
e2b template build --name spaceapps-judge-v3
```

## 3. Publish or Use Your Template ID

Once built, `e2b template build` outputs a `template_id`. Pass it via `--template` or set `E2B_JUDGE_TEMPLATE` in your `.env`:

```bash
spaceapps-judge examples/sample_submission --template spaceapps-judge-v3
```
