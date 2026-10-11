# peer-bounty

Zero-backend peer-to-peer Bitcoin bounty badges and autonomous settlement for GitHub issues.

## The Core Problem

Traditional open-source bounty platforms suffer from fundamental systemic limitations:
1. High Intermediary Fees: Centralized platforms extract between 5 and 15 percent of contributor rewards in fees.
2. Custodial and KYC Barriers: Contributors and maintainers are forced to create third-party accounts, complete identity verification, and link traditional banking or Stripe accounts, excluding international and sovereign contributors.
3. Vendor Lock-In: Bounties live inside external walled gardens rather than natively within GitHub issues and version control history.

## The Solution

`peer-bounty` decentralizes open-source incentives directly into GitHub repositories:
1. Native Markdown Badges: Maintainers and community members attach an interactive SVG badge directly to any GitHub issue description.
2. Direct Lightning Network Pledges: Anyone can pledge satoshis to an issue pool by scanning a Lightning QR code or paying an LNURL invoice. Zero custodial intermediary.
3. Autonomous GitHub Action Settlement: When a pull request resolving the issue (`Closes #42`) is merged into the default branch by a repository maintainer, the `peer-bounty` GitHub Action automatically executes the payment to the contributor's Lightning address (`alice@getalby.com`) and posts the cryptographic payment preimage to the issue thread as public proof of settlement.
4. Tamper-Evident Local Ledger: All bounty states and settlement hashes are cryptographically signed with SHA-256 and committed directly into the repository, ensuring complete auditability and preventing double-settlement.

## Quickstart

### 1. Installation
Install the standalone CLI tool:

```bash
pip install peer-bounty
```

### 2. Initialize in Your Repository
Generate the GitHub Action workflow and local ledger directory:

```bash
peerbounty init
```

This creates `.github/workflows/peer-bounty.yml` and initializes the `.peer-bounty/` ledger directory.

### 3. Generate a Bounty Badge
Generate a self-contained SVG badge and markdown snippet for any issue:

```bash
peerbounty badge --issue 42 --sats 50000 --repo owner/repo --output .peer-bounty/badges/issue-42.svg
```

Markdown snippet to paste into GitHub issue description:
```markdown
[![Bitcoin Bounty: 50,000 sats](https://raw.githubusercontent.com/owner/repo/main/.peer-bounty/badges/issue-42.svg)](https://github.com/owner/repo/issues/42)
```

### 4. Contributing and Claiming
Contributors simply reference the issue and add their Lightning address in the pull request description or commit trailer:

```markdown
Closes #42

Fully implemented feature with unit tests passing.
Lightning-Address: contributor@getalby.com
```

### 5. Settlement Execution
When the maintainer merges the pull request, the GitHub Action verifies the maintainer authorization, dispatches the payment via Nostr Wallet Connect (NWC) or LNURL, records the payment preimage in `.peer-bounty/bounties.json`, and posts a settlement confirmation comment:

```markdown
### Peer-Bounty Settlement Confirmation

Pull request #105 successfully resolved issue #42 and has been merged by a repository maintainer.

1. Settled Amount: 50,000 satoshis
2. Recipient Address: `contributor@getalby.com`
3. Payment Preimage: `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef`
4. Cryptographic Receipt Hash: `f8a1...`
5. Settlement Timestamp: `2026-10-11T19:30:00Z`
```

## CLI Reference

### 1. `peerbounty badge`
Generates SVG badges for issues and outputs markdown links.
Arguments:
1. `--issue <number>`: GitHub issue number.
2. `--sats <amount>`: Bounty reward in satoshis.
3. `--status <open|funded|settled|closed>`: Visual status indicator.
4. `--repo <owner/repo>`: Target repository.
5. `--output <path>`: Local file path to write SVG badge.

### 2. `peerbounty check-pr`
Parses pull request text to detect linked issue numbers and recipient payment targets:

```bash
peerbounty check-pr --title "feat: close #42" --body "Lightning-Address: alice@getalby.com"
```

### 3. `peerbounty settle`
Records and settles a bounty in the local ledger:

```bash
peerbounty settle --issue 42 --pr 105 --recipient alice@getalby.com --sats 50000 --preimage <preimage-hex>
```

### 4. `peerbounty verify-receipt`
Cryptographically verifies that an issue settlement has not been tampered with or altered:

```bash
peerbounty verify-receipt --issue 42 --ledger .peer-bounty/bounties.json
```

## Contributing and License

`peer-bounty` is open-source software licensed under the MIT License. Contributions and feature requests are welcome.

### Sovereign Payout and Sponsorship Coordinates
1. Bitcoin Native SegWit: `bc1qaedjdrkrhjya767yvfz676jeyx5an04kfwzczg`
2. Stacks Protocol: `SP3Q5P9MEREY8KQVBRHH4BBVAB4GTKPDYPT80002V`
