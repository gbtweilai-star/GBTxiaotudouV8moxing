# 杂交: bandit x bandit_x_semgrep

# PyCQA/bandit 吞噬记录 — devour_tentacle
> 吞噬日期: 2026-09-11T10:50:33 | 来源: https://github.com/PyCQA/bandit
> Stars: 8257 | 语言: Python | 许可: Apache-2.0

## 项目概览
- 描述: Bandit is a tool designed to find common security issues in Python code.
- 主题: bandit, linter, python, security, security-scanner, security-tools, static-code-analysis
- 分支: main | 最近推送: 2026-08-29

## README 摘要
(仓库无 README.md)

## 对 GBT 的启示
- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

# 杂交: bandit x semgrep

# PyCQA/bandit 吞噬记录 — devour_tentacle
> 吞噬日期: 2026-09-11T10:50:33 | 来源: https://github.com/PyCQA/bandit
> Stars: 8257 | 语言: Python | 许可: Apache-2.0

## 项目概览
- 描述: Bandit is a tool designed to find common security issues in Python code.
- 主题: bandit, linter, python, security, security-scanner, security-tools, static-code-analysis
- 分支: main | 最近推送: 2026-08-29

## README 摘要
(仓库无 README.md)

## 对 GBT 的启示
- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

# returntocorp/semgrep 吞噬记录 — devour_tentacle
> 吞噬日期: 2026-09-11T10:50:34 | 来源: https://github.com/semgrep/semgrep
> Stars: 16583 | 语言: C | 许可: LGPL-2.1

## 项目概览
- 描述: Lightweight static analysis for many languages. Find bug variants with patterns that look like source code.
- 主题: c, go, java, javascript, python, r2c, ruby, sast, semgrep, static-analysis
- 分支: develop | 最近推送: 2026-09-11

## README 摘要
<br />
<p align="center">
  <a href="https://semgrep.dev">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="images/semgrep-logo-light.svg">
      <source media="(prefers-color-scheme: dark)" srcset="images/semgrep-logo-dark.svg">
      <img src="https://raw.githubusercontent.com/semgrep/semgrep/develop/images/semgrep-logo-light.svg" height="100" alt="Semgrep logo"/>
    </picture>
  </a>
</p>
<h2 align="center">
  Code scanning at ludicrous speed.
</h2>
<p align="center">
  <a href="https://formulae.brew.sh/formula/semgrep">
    <img src="https://img.shields.io/homebrew/v/semgrep?style=flat-square" alt="Homebrew" />
  </a>
  <a href="https://pypi.org/project/semgrep/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/semgrep?style=flat-square&color=blue">
  </a>
  <a href="https://semgrep.dev/docs/">
      <img src="https://img.shields.io/badge/docs-semgrep.dev-purple?style=flat-square" alt="Documentation" />
  </a>
  <a href="https://go.semgrep.dev/slack">
    <img src="https://img.shields.io/badge/slack-3.5k%20members-green?style=flat-square" alt="Join Semgrep community Slack" />
  </a>
  <a href="https://github.com/semgrep/semgrep/issues/new/choose">
    <img src="https://img.shields.io/badge/issues-welcome-green?style=flat-square" alt="Issues welcome!" />
  </a>
  <a href="https://github.com/semgrep/semgrep#readme">
    <img src="https://img.shields.io/github/stars/semgrep/semgrep?label=GitHub%20Stars&style=flat-square" alt="Star Semgrep on GitHub" />
  </a>
  <a href="https://hub.docker.com/r/semgrep/semgrep">
    <img src="https://img.shields.io/docker/pulls/semgrep/semgrep.svg?style=flat-square" alt="Docker Pulls" />
  </a>
  <a href="https://hub.docker.com/r/semgrep/semgrep">
    <img src="https://img.shields.io/docker/pulls/semgrep/semgrep.svg?style=flat-square" alt="Docker Pulls (Old)" />
  </a>
  <a href="https://twitter.com/intent/follow?screen_name=semgrep">
    <img src="https://img.shields.io/twitter/follow/semgrep?label=Follow%20semgrep&style=social&color=blue" alt="Follow @semgrep on Twitter" />
  </a>
</p>
</br>

Semgrep is a fast, open-source, static analysis tool that searches code, finds bugs, and enforces secure guardrails and coding standards. Semgrep [supports 30+ languages](#language-support) and can run in an IDE, as a pre-commit check, and as part of CI/CD workflows.

Semgrep is semantic grep for code. While running `grep "2"` would only match the exact string _2_, Semgrep would [match `x = 1; y = x + 1` when searching for _2_](https://semgrep.dev/playground/s/5rKgj). Semgrep rules look like the code you already write; no abstract syntax trees, regex wrestling, or painful DSLs.

Note that in security contexts, Semgrep Community Edition will miss many true positives as it can only analyze code within the boundaries of a single function or file. If you want to use Semgrep for security purposes (**SAST**, **SCA**, or **secrets scanning**), the Semgrep AppSec Platform is strongly recommended since it adds the following critical capabilities:

1. Improved core analysis capabilities (cross-file, cross-function, data-flow reachability) that greatly reduce false positives by 25% and increase detected true positives by 250%
2. Contextual post-processing of findings with Semgrep Assistant (AI) to further reduce noise by [~20%](https://a.storyblok.com/f/151984/x/2d12dc0223/whitepaper_-ai-powered-appsec-engineer-automate.pdf?cv=1728584410408).  In addition, Assistant enriches findings with tailored, step-by-step remediation guidance that humans find actionable >80% of the time.
3. Customizable policies and seamless integration into developer workflows, giving security teams granular control over where, when, and how different findings are presented to developers (IDE, PR comment, etc.)

The Semgrep AppSec Platform works out-of-the-box with 20000+ proprietary rules across SAST, SCA, and secrets. Pro rules are written and maintained by the Semgrep security research team and are highly accurate, meaning AppSec teams can feel confident bringing findings directly to developers without slowing them down.

Semgrep analyzes code locally on your computer or in your build environment: **by default, code is never uploaded**. [Get started →.](#getting-started-)

<a href="#option-1-getting-started-from-the-cli">
<img src="https://raw.githubusercontent.com/semgrep/semgrep/develop/images/semgrep-scan-cli.jpg" alt="Semgrep CLI image"/></a>

### Language support

**Semgrep Code** supports 30+ languages, including:

Apex · Bash · C · C++ · C# · Clojure · Dart · Dockerfile · Elixir · HTML · Go · Java · JavaScript · JSX · JSON · Julia · Jsonnet · Kotlin · Lisp · Lua · OCaml · PHP · Python · R · Ruby · Rust · Scala · Scheme · Solidity · Swift · Terraform · TypeScript · TSX · YAML · XML · Generic (ERB, Jinja, etc.)

**Semgrep Supply Chain** supports 12 languages across 15 package managers, including:

C# (NuGet) · Dart (Pub) · Go (Go modules, `go mod`) · Java (Gradle, Maven) · Javascript/Typescript (npm, Yarn, Yarn 2, Yarn 3, pnpm) · Kotlin (Gradle, Maven) · PHP (Composer) · Python (pip, pip-tool, Pipenv, Poetry) · Ruby (RubyGems) · Rust (Cargo) · Scala (Maven) · Swift (SwiftPM)

For more information, see [Supported languages](https://semgrep.dev/docs/supported-languages/).

### Getting started 🚀

1. [From the Semgrep AppSec Platform](#option-1-getting-started-from-the-semgrep-appsec-platform-recommended)
2. [From the CLI](#option-2-getting-started-from-the-cli)

For new users, we recommend starting with the [Semgrep AppSec Platform](#option-1-getting-started-from-the-semgrep-appsec-platform-recommended) because it provides a visual interface, a demo project, result triaging and exploration workflows, and makes setup in CI/CD fast. Scans are still local and code isn't uploaded. Alternatively, you can also start with the CLI and navigate the terminal output to run one-off searches.

### Option 1: Getting started from the Semgrep Appsec Platform (Recommended)

<a hr

## 对 GBT 的启示
- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
