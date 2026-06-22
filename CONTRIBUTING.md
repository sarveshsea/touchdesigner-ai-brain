# Contributing

Thanks for helping make AI-assisted TouchDesigner work more practical and less hand-wavy.

Good contributions include:

- TouchDesigner Python builder scripts,
- `.tdn` network examples,
- MCP setup guides,
- component audit notes,
- projection mapping workflows,
- VJ/show-control templates,
- performance and stability findings.

## Guidelines

- Keep examples reproducible.
- Prefer source-readable artifacts over opaque binaries.
- Do not commit secrets, credentials, API keys, or private show assets.
- Treat `.toe` and `.tox` files as executable code and document their source.
- Include TouchDesigner version notes when relevant.
- Include smoke-test notes for third-party components.

## Asset Audit Template

```yaml
id:
name:
source_url:
author:
license:
downloaded:
touchdesigner_version:
uses_python: unknown
uses_network: unknown
uses_compiled_plugin: unknown
external_files: unknown
smoke_test:
decision: keep | sandbox | rewrite | reject
notes:
```

