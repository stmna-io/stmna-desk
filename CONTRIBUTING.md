# Contributing

<!-- TODO: Expand with full contribution guidelines before public launch -->

Thank you for your interest in contributing to STMNA Desk!

## What We're Looking For

- **Benchmark data** on different AMD hardware (Strix Halo variants, APUs, dGPUs)
- **Documentation improvements**  -- corrections, clarifications, translations
- **Compose snippets** for additional services that fit the sovereign stack
- **Bug reports**  -- especially hardware-specific issues on non-Framework AMD systems

## How to Contribute

1. Fork this repository
2. Create a branch: `git checkout -b feature/your-contribution`
3. Make your changes
4. Submit a pull request with a clear description

## Code Style

- Shell scripts: bash, 2-space indent, `shellcheck`-clean
- YAML: 2-space indent
- Markdown: GitHub-flavored, line wrap at 120

## Reporting Issues

Open an issue with:
- Your hardware (CPU model, RAM, GPU)
- OS version (`uname -r`, `ubuntu-release`)
- Podman version (`podman --version`)
- Steps to reproduce

## License

By contributing, you agree your contributions are licensed under Apache 2.0.
