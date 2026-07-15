"""Build a deterministic corpus of fictional AI security tool names.

The tiny language models in this project use single-character tokens. A compact
domain corpus with repeated fragments helps the models learn useful local
patterns such as "prompt", "agent", "guard", "scan", "vault", and "shield".
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "tool_names.txt"

PREFIXES = [
    "agent",
    "ai",
    "autonomy",
    "context",
    "credential",
    "guard",
    "identity",
    "jailbreak",
    "llm",
    "memory",
    "policy",
    "prompt",
    "redteam",
    "secret",
    "session",
    "token",
    "tool",
    "trust",
    "vault",
    "zero",
]

CORES = [
    "armor",
    "audit",
    "barrier",
    "beacon",
    "check",
    "defense",
    "filter",
    "firewall",
    "gate",
    "guard",
    "lens",
    "lock",
    "monitor",
    "radar",
    "scanner",
    "sentry",
    "shield",
    "trace",
    "watch",
    "warden",
]

SUFFIXES = [
    "ai",
    "base",
    "cloud",
    "hub",
    "kit",
    "lab",
    "ops",
    "pilot",
    "scan",
    "stack",
    "suite",
    "watch",
]

CURATED_NAMES = [
    "agentguard",
    "agentshield",
    "agentvault",
    "aiguard",
    "aisentry",
    "contextlock",
    "contextshield",
    "credentialscan",
    "guardrailscan",
    "jailbreakwatch",
    "llmfirewall",
    "llmguard",
    "memorysentry",
    "policyguard",
    "promptarmor",
    "promptfirewall",
    "promptguard",
    "promptshield",
    "redteamlens",
    "secretscanner",
    "secretsentinel",
    "sessionwarden",
    "tokensentry",
    "toolshield",
    "trustfilter",
    "vaultguard",
    "zerotrustguard",
]


def build_names() -> list[str]:
    names: set[str] = set(CURATED_NAMES)

    for prefix in PREFIXES:
        for core in CORES:
            candidate = f"{prefix}{core}"
            if 6 <= len(candidate) <= 24:
                names.add(candidate)

    for prefix in PREFIXES:
        for suffix in SUFFIXES:
            candidate = f"{prefix}{suffix}"
            if 6 <= len(candidate) <= 24:
                names.add(candidate)

    return sorted(names)


def main() -> None:
    names = build_names()
    OUTPUT_PATH.write_text("\n".join(names) + "\n", encoding="utf-8")
    print(f"Wrote {len(names)} names to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
