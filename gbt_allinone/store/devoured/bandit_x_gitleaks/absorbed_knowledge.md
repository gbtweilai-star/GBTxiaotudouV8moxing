# 杂交: bandit x gitleaks

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

# gitleaks/gitleaks 吞噬记录 — devour_tentacle
> 吞噬日期: 2026-09-11T10:50:35 | 来源: https://github.com/gitleaks/gitleaks
> Stars: 29223 | 语言: Go | 许可: MIT

## 项目概览
- 描述: Find secrets with Gitleaks 🔑
- 主题: ai-powered, ci-cd, cicd, cli, data-loss-prevention, devsecops, dlp, git, gitleaks, go
- 分支: master | 最近推送: 2026-09-09

## README 摘要
# Gitleaks

```
┌─○───┐
│ │╲  │
│ │ ○ │
│ ○ ░ │
└─░───┘
```

> [!WARNING]
> Gitleaks is feature complete. I'm not merging new features into Gitleaks. Future releases will be security patches only. I'm shifting my focus to [Betterleaks](https://github.com/betterleaks/betterleaks)

[license]: ./LICENSE
[badge-license]: https://img.shields.io/github/license/gitleaks/gitleaks.svg
[go-docs-badge]: https://pkg.go.dev/badge/github.com/gitleaks/gitleaks/v8?status
[go-docs]: https://pkg.go.dev/github.com/zricethezav/gitleaks/v8
[badge-build]: https://github.com/gitleaks/gitleaks/actions/workflows/test.yml/badge.svg
[build]: https://github.com/gitleaks/gitleaks/actions/workflows/test.yml
[go-report-card-badge]: https://goreportcard.com/badge/github.com/gitleaks/gitleaks/v8
[go-report-card]: https://goreportcard.com/report/github.com/gitleaks/gitleaks/v8
[dockerhub]: https://hub.docker.com/r/zricethezav/gitleaks
[dockerhub-badge]: https://img.shields.io/docker/pulls/zricethezav/gitleaks.svg
[gitleaks-action]: https://github.com/gitleaks/gitleaks-action
[gitleaks-badge]: https://img.shields.io/badge/protected%20by-gitleaks-blue


[![GitHub Action Test][badge-build]][build]
[![Docker Hub][dockerhub-badge]][dockerhub]
[![Gitleaks Action][gitleaks-badge]][gitleaks-action]
[![GoDoc][go-docs-badge]][go-docs]
[![GoReportCard][go-report-card-badge]][go-report-card]
[![License][badge-license]][license]

Gitleaks is a tool for **detecting** secrets like passwords, API keys, and tokens in git repos, files, and whatever else you wanna throw at it via `stdin`. If you wanna learn more about how the detection engine works check out this blog: [Regex is (almost) all you need](https://lookingatcomputer.substack.com/p/regex-is-almost-all-you-need).

```
➜  ~/code(master) gitleaks git -v

    ○
    │╲
    │ ○
    ○ ░
    ░    gitleaks


Finding:     "export BUNDLE_ENTERPRISE__CONTRIBSYS__COM=cafebabe:deadbeef",
Secret:      cafebabe:deadbeef
RuleID:      sidekiq-secret
Entropy:     2.609850
File:        cmd/generate/config/rules/sidekiq.go
Line:        23
Commit:      cd5226711335c68be1e720b318b7bc3135a30eb2
Author:      John
Email:       john@users.noreply.github.com
Date:        2022-08-03T12:31:40Z
Fingerprint: cd5226711335c68be1e720b318b7bc3135a30eb2:cmd/generate/config/rules/sidekiq.go:sidekiq-secret:23
```


## Getting Started

Gitleaks can be installed using Homebrew, Docker, or Go. Gitleaks is also available in binary form for many popular platforms and OS types on the [releases page](https://github.com/gitleaks/gitleaks/releases). In addition, Gitleaks can be implemented as a pre-commit hook directly in your repo or as a GitHub action using [Gitleaks-Action](https://github.com/gitleaks/gitleaks-action).

### Installing

```bash
# MacOS
brew install gitleaks

# Docker (DockerHub)
docker pull zricethezav/gitleaks:latest
docker run -v ${path_to_host_folder_to_scan}:/path zricethezav/gitleaks:latest [COMMAND] [OPTIONS] [SOURCE_PATH]

# Docker (ghcr.io)
docker pull ghcr.io/gitleaks/gitleaks:latest
docker run -v ${path_to_host_folder_to_scan}:/path ghcr.io/gitleaks/gitleaks:latest [COMMAND] [OPTIONS] [SOURCE_PATH]

# From Source (make sure `go` is installed)
git clone https://github.com/gitleaks/gitleaks.git
cd gitleaks
make build
```

### Pre-Commit

1. Install pre-commit from https://pre-commit.com/#install
2. Create a `.pre-commit-config.yaml` file at the root of your repository with the following content:

   ```
   repos:
     - repo: https://github.com/gitleaks/gitleaks
       rev: v8.24.2
       hooks:
         - id: gitleaks
   ```

   for a [native execution of gitleaks](https://github.com/gitleaks/gitleaks/releases) or use the [`gitleaks-docker` pre-commit ID](https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml) for executing gitleaks using the [official Docker images](#docker)

3. Auto-update the config to the latest repos' versions by executing `pre-commit autoupdate`
4. Install with `pre-commit install`
5. Now you're all set!

```
➜ git commit -m "this commit contains a secret"
Detect hardcoded secrets.................................................Failed
```

Note: to disable the gitleaks pre-commit hook you can prepend `SKIP=gitleaks` to the commit command
and it will skip running gitleaks

```
➜ SKIP=gitleaks git commit -m "skip gitleaks check"
Detect hardcoded secrets................................................Skipped
```

## Usage

```
Gitleaks scans code, past or present, for secrets

Usage:
  gitleaks [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  dir         scan directories or files for secrets
  git         scan git repositories for secrets
  help        Help about any command
  stdin       detect secrets from stdin
  version     display gitleaks version

Flags:
  -b, --baseline-path string          path to baseline with issues that can be ignored
  -c, --config string                 config file path
                                      order of precedence:
                                      1. --config/-c
                                      2. env var GITLEAKS_CONFIG
                                      3. env var GITLEAKS_CONFIG_TOML with the file content
                                      4. (target path)/.gitleaks.toml
                                      If none of the four options are used, then gitleaks will use the default config
      --diagnostics string            enable diagnostics (http OR comma-separated list: cpu,mem,trace). cpu=CPU prof, mem=memory prof, trace=exec tracing, http=serve via net/http/pprof
      --diagnostics-dir string        directory to store diagnostics output files when not using http mode (defaults to current directory)
      --enable-rule strings           only enable specific rules by id
      --exit-code int                 exit code when leaks have been encountered (default 1)
  -i, --gitleaks-ignore-path string   path to .gitleaksignore file or folder conta

## 对 GBT 的启示
- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
