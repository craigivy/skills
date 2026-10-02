# Skills

A collection of production-ready, modular **Agent Skills** designed for AI coding assistants and autonomous agents (including [Google Antigravity](https://github.com), Claude Code, and other platforms supporting the `SKILL.md` specification).

Each skill provides specialized system instructions, deep-dive technical references, executable examples, and developer utilities that empower AI agents to master complex libraries, domain workflows, and APIs with precision.

---

## Repository Structure

```
skills/
├── README.md
└── schwabdev/                          # Charles Schwab API & Algorithmic Trading Skill
    ├── SKILL.md                        # Core skill instructions & agent cheatsheet
    ├── references/                     # Detailed domain and technical references
    │   ├── authentication.md           # OAuth 2.0 lifecycle & token encryption
    │   ├── orders.md                   # Equity & option order construction
    │   ├── rest_api.md                 # Synchronous & async REST endpoints
    │   ├── streaming.md                # WebSocket streamer services & field maps
    │   ├── trader_context.md           # Unified backtesting & live trading engine
    │   └── troubleshooting.md          # Error code catalog & common fixes
    ├── examples/                       # Tested, ready-to-run Python examples
    │   ├── async_client_demo.py        # High-concurrency async REST client
    │   ├── basic_quotes.py             # Market data & price history queries
    │   ├── encrypted_tokens_setup.py   # Encrypted SQLite token store
    │   ├── live_strategy_demo.py       # Live/paper streaming strategy with RSI
    │   ├── order_placement.py          # Preview, place, & cancel order lifecycle
    │   ├── record_market_data.py       # Automated L1/L2/candle market recorder
    │   ├── sma_backtest_demo.py        # Moving average crossover backtest
    │   └── stream_handler_demo.py      # Real-time WebSocket stream processor
    └── scripts/                        # CLI utilities & automation tools
        ├── auth_callback_server.py     # Local HTTPS OAuth callback listener
        └── check_tokens.py             # Token validity & expiration inspector
```

---

## Available Skills

### [`schwabdev`](./schwabdev/SKILL.md)

A specialized skill for building, debugging, and running algorithmic trading workflows using the Charles Schwab Trader API via the [`schwabdev`](https://github.com/tylerebowers/Schwabdev) Python library (v4.0.0+) and [`schwabdev-context`](https://github.com/tylerebowers/Schwabdev-Context).

#### Key Capabilities Covered:
- **Authentication & Security**: Automated OAuth 2.0 flow, token persistence in SQLite, proactive token renewal (30-min access / 7-day refresh), headless authentication, and Fernet token encryption.
- **Market Data & REST APIs**: Synchronous (`Client`) and native asynchronous (`ClientAsync`) clients for quotes, historical candle bars, option chains, market hours, and account balances/positions.
- **Order Execution Lifecycle**: Construction and validation of equity and multi-leg option orders, order previewing, location header order ID capture, order modification, and cancellation.
- **WebSocket Streaming**: Thread-based (`Stream`) and async (`StreamAsync`) streamer clients supporting 13 Schwab services (Level 1 equities/options/futures, Level 2 order books, charts, and real-time account activity).
- **Trader Context Engine**: Write unified strategy logic once (`strategy(tc, events)`) and execute across:
  1. Historical backtesting on 1-minute cached candles with customizable commission/slippage models (`Costs`).
  2. Live paper trading with real-time streaming WebSocket data.
  3. Live broker order execution with interactive equity curve plotting.
- **Developer Utilities**:
  - `check_tokens.py`: Inspect token DB expiration timestamps and validity from the command line.
  - `auth_callback_server.py`: Local HTTPS redirect server that automatically intercepts and captures OAuth authorization codes.

👉 **View the full skill instructions**: [`schwabdev/SKILL.md`](./schwabdev/SKILL.md)

---

## Installation & Setup

### Using in Antigravity

To make these skills available in your Antigravity environment:

#### Workspace-Level (Project-Specific)
Clone or symlink the skill directory into your project's `.agent/skills/` or `.gemini/skills/` directory:

```bash
mkdir -p .gemini/skills
ln -s /path/to/skills/schwabdev .gemini/skills/schwabdev
```

#### User-Level (Global across projects)
Symlink or copy the skill directory into your global Antigravity skills directory:

```bash
mkdir -p ~/.gemini/antigravity/skills
ln -s /path/to/skills/schwabdev ~/.gemini/antigravity/skills/schwabdev
```

### Using in Claude Code / Other Agent Frameworks

Symlink or copy into your agent's configured skills path (e.g. `~/.claude/skills/` or `<project-root>/.claude/skills/`):

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/skills/schwabdev ~/.claude/skills/schwabdev
```

---

## Skill Architecture & Design Principles

All skills in this repository follow standard agent skill architecture principles:

1. **Progressive Disclosure**:
   - `SKILL.md` stays lean and actionable, providing high-level decision trees, common triggers, workflow checklists, and quick-reference snippets.
   - Detailed specifications, API parameter catalogs, and deep schemas live in `references/` to keep the agent's active context window focused.
2. **Deterministic Frontmatter**:
   - Standard YAML frontmatter (`name`, `description`) with precise trigger phrasing so agents know exactly when to activate the skill.
3. **Executable Examples (`examples/`)**:
   - Fully functional, standalone scripts illustrating real-world use cases.
4. **Developer Tools (`scripts/`)**:
   - Standalone CLI tools designed to be invoked directly by users or agents during setup, validation, or debugging.

---

## Adding New Skills

Contributions of new skills are welcome. When adding a skill, follow this standard layout:

```
<skill-name>/
├── SKILL.md            # Required: YAML frontmatter + core guide
├── references/         # In-depth docs, API tables, schemas
├── examples/           # Working sample code
└── scripts/            # CLI utilities, setup scripts, or diagnostic tools
```

Ensure your `SKILL.md` includes valid YAML frontmatter:
```yaml
---
name: your-skill-name
description: >-
  Concise explanation of when to trigger this skill and what technologies or tasks it covers.
---
```

---

## License

MIT License. See [LICENSE](LICENSE) for details (or individual skill components for external SDK licenses).
