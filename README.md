# mini-RAG

## Developer setup

After cloning, enable the shared pre-commit hook in each checkout:

```bash
git config core.hooksPath .githooks
```

The hook requires Bash, Git, and grep (available in Git Bash on Windows).
It rejects staged whitespace errors and added lines containing private keys,
AWS access keys, GitHub or Slack tokens, or quoted credential assignments.
Diagnostics redact secret values. Review and fix the staged changes before retrying.

`git commit --no-verify` bypasses the hook, so CI must repeat both checks on
the pull request diff when CI is introduced. This repository currently has no
CI configuration. The hook scans added text lines; it is not a full secret audit.
