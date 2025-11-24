# 🛡️ Vibe Check

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-VibeGuard-purple.svg?style=for-the-badge&logo=github)](https://github.com/marketplace/actions/vibeguard-auditor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Vibes: Immaculate](https://img.shields.io/badge/Vibes-Immaculate-pink.svg?style=for-the-badge)](https://github.com/marketplace/actions/vibeguard-auditor)

> **Are you Engineering or just Vibecoding?**
> Vibe Check is a ruthless, Python-based CI/CD auditor that ranks your repository quality on a scale of 0 to 1000.

---

## 🧐 What is this?

**Vibe Check** isn't just a linter. It's a gamified reputation system for your codebase. It scans your repository for:

1.  **Security Suicide** (committed `.env` files, AWS keys, `777` permissions).
2.  **Stability Nightmares** (empty `catch` blocks, infinite loops, God objects).
3.  **Vibecoding Artifacts** (`console.log` leftovers, `TODO` graveyards, "trust me bro" comments).
4.  **Engineering Excellence** (It penalizes bad patterns and rewards SOTA architecture).

If your score drops below the threshold (Default: **800**), **the build fails**. No mercy.

## 🚀 Usage

Add this to your `.github/workflows/main.yml`:

```yaml
name: Quality Gate
on: [push, pull_request]

jobs:
  vibe-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Run VibeGuard Auditor
        uses: tuousername/vibeguard-auditor@v1
        with:
          # Optional: Set your own quality bar (Default: 800)
          threshold: 850
```

## 📊 The Report Card

Vibe Check doesn't just crash your pipeline; it tells you why. It generates a **Job Summary** directly in your GitHub Actions run:

| File | Violation | Penalty |
| :--- | :--- | :--- |
| `src/config.js` | **Committed .env file** | 🔴 **-100 pts** |
| `src/utils.js` | **Empty Catch Block** | 🟠 **-50 pts** |
| `src/app.ts` | **Console.log leftover** | 🟡 **-5 pts** |
| **FINAL SCORE** | **845 / 1000** | ✅ **PASS** |

## ⚖️ The Rules (A Teaser)

Vibe Check applies 100+ checks based on modern FAANG-level engineering standards versus "Vibe-based" coding.

*   **CRITICAL (-100 pts):** Secrets in code, `node_modules` in git, SQL Injection patterns.
*   **HIGH (-50 pts):** Swallow exceptions, Hardcoded paths, Huge files (>2000 lines).
*   **MEDIUM (-20 pts):** `var` usage, Magic numbers, Circular dependencies.
*   **LOW (-5 pts):** Dead code, `TODO`s older than the project, Typos in function names.

## 🛠️ Configuration

Currently, Vibe Check runs with an opinionated "Strict" preset. Custom configuration via `.vibeguardrc` is coming in v1.1.

## 🤝 Contributing

Found a new "Vibecoding" pattern I missed? Open a PR. I accept rules that enforce rigor, sanity, and professional engineering.


