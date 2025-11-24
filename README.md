# 🛡️ Vibe Check: The Anti-Slop CI/CD Gatekeeper

> **"Your code quality is a vibe. And the vibe is off."**
> 
> Vibe Check is a ruthless, Python-based CI/CD auditor that ranks your repository quality on a scale of 0 to 1000.

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-VibeGuard-blue?logo=github)](https://github.com/marketplace/actions/vibeguard-auditor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 🧐 What is this?

**Vibe Check** isn't just a linter. It's a gamified reputation system for your codebase. It scans your repository for:

1.  **Security Suicide** (committed `.env` files, AWS keys, `777` permissions, hardcoded passwords).
2.  **Stability Nightmares** (empty `catch` blocks, infinite loops, God objects).
3.  **AI Slop** (Literal "As an AI language model" copy-pasted from ChatGPT—**-500 points instantly**).
4.  **Vibecoding Artifacts** (`console.log` leftovers, `TODO` graveyards, "trust me bro" comments).
5.  **React Anti-Patterns** (`useEffect` without deps, `index` as key, inline functions in JSX).
6.  **UI/UX Disasters** (Scroll hijacking, disabled zoom, missing alt text, autoplay videos).
7.  **Git Commit Hygiene** (Lazy "wip" commits, Friday deploys, 3 AM cowboy coding, revert wars).
8.  **Engineering Excellence** (It penalizes bad patterns and rewards SOTA architecture).

If your score drops below the threshold (Default: **800**), **the build fails**. No mercy.

**🔥 Brutal Mode Available**: Double all penalties and fail-fast on critical security violations.

### 🆕 Git History Audit

Vibe Check doesn't just judge your code—it judges **you**. The git history audit analyzes your last 50 commits for:

- **Lazy Messages**: "wip", "fix", "test", "asdasd" (-15 pts each)
- **Revert Wars**: Reverting a revert indicates chaos (-30 pts)
- **Unprofessional Language**: "oops", "lol", "yolo", "hope this works" (-10 pts)
- **Monster Commits**: Single commits touching >50 files (-40 pts)
- **Friday Deploys**: Commits after 4 PM on Friday (-50 pts—read-only Friday rule)
- **3 AM Commits**: Coding during ungodly hours (00:00-05:59) (-20 pts)
- **Missing Ticket IDs**: No `PROJ-123` reference in commit message (-12 pts)

*If you write beautiful code but commit "fix" 10 times at 3 AM on Friday, your vibe score still tanks.*

## 🚀 Usage

### Basic Usage

Add this to your `.github/workflows/main.yml`:

```yaml
name: Quality Gate
on: [push, pull_request]

jobs:
  vibe-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run VibeGuard Auditor
        uses: fabriziosalmi/vibe-check@v1.2.0
        with:
          threshold: 850  # Optional: Default is 800
```

### 🔥 Brutal Mode (Recommended for Main Branch)

Enable **double penalties** and **fail-fast** on critical security issues:

```yaml
      - name: Run VibeGuard (Brutal Mode)
        uses: fabriziosalmi/vibe-check@v1.2.0
        with:
          threshold: 900
          brutal_mode: true  # 💀 No mercy
```

In Brutal Mode:
- All penalties are **doubled** (e.g., `eval()` costs -140 instead of -70)
- Pipeline **terminates immediately** on critical violations (hardcoded secrets, AI slop)
- Perfect for protecting `main` branch from rancid vibes

### ⚙️ Custom Configuration

Create a `.vibeguardrc` file in your repository root:

```json
{
  "ignore": ["NAM03", "SME03"],
  "exclude_files": ["legacy/*", "vendor/*", "*.min.js"]
}
```

See [`.vibeguardrc.example`](./.vibeguardrc.example) for full options.

---

## 📊 The Report Card

Vibe Check doesn't just crash your pipeline; it tells you why. It generates a **Job Summary** directly in your GitHub Actions run:

### Sample Output

| Category | File | Violation | Penalty |
| :---: | :--- | :--- | ---: |
| 🤖 **AI Slop** | `src/ai-code.js` | **"As an AI language model..."** | 🔴 **-500 pts** |
| 🔒 **Security** | `src/config.js` | **Committed .env file** | 🔴 **-100 pts** |
| ⚡ **Stability** | `src/utils.js` | **Empty Catch Block** | 🟠 **-50 pts** |
| 🧹 **Hygiene** | `src/app.ts` | **Console.log leftover** | 🟡 **-5 pts** |
|  | **FINAL SCORE** | **345 / 1000** | ❌ **VIBE: RANCID** |

---

## ⚖️ The Rules

Vibe Check applies **170+ checks** based on modern FAANG-level engineering standards versus "Vibe-based" coding.

### Rule Categories

*   **🤖 AI SLOP (-100 to -500 pts):** Copy-pasted ChatGPT responses, hallucinated comments, Lorem Ipsum
*   **🔒 CRITICAL SECURITY (-60 to -100 pts):** Hardcoded secrets, SQL Injection, `eval()`, chmod 777
*   **⚡ HIGH STABILITY (-25 to -50 pts):** Swallow exceptions, Hardcoded paths, Infinite loops
*   **⚛️ REACT ANTI-PATTERNS (-25 to -60 pts):** useEffect without deps, index as key, setState in render
*   **🌿 GIT HYGIENE (-10 to -50 pts):** Lazy commits, Friday deploys, 3 AM coding, revert wars
*   **🎨 UI/UX DISASTERS (-15 to -40 pts):** Scroll hijacking, disabled zoom, missing alt text
*   **🔧 MAINTAINABILITY (-15 to -40 pts):** Huge files (>2000 lines), God objects, deep nesting
*   **👃 CODE SMELLS (-8 to -35 pts):** `var` usage, Magic numbers, Float for currency
*   **🧹 HYGIENE (-2 to -20 pts):** Debug statements, trailing whitespace, filename with spaces

## 🛠️ Configuration

Currently, Vibe Check runs with an opinionated "Strict" preset. Custom configuration via `.vibeguardrc` is coming in v1.1.

## 🤝 Contributing

Found a new "Vibecoding" pattern I missed? Open a PR. I accept rules that enforce rigor, sanity, and professional engineering.


