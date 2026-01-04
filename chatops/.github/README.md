# 🛈 This .github folder is inactive in the monorepo

GitHub Actions, templates, and configs are only picked up from the repository-root `.github/` directory. Because this folder lives under `chatops/.github/`, none of the workflows or templates here will run for `machine-native-ops` unless they are copied or moved into the root `.github/`. Keep this directory for reference only; make changes in the root `.github/` to activate them.
