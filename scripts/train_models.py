#!/usr/bin/env python3
"""Train tiny character-level models for AI security tool-name generation."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "tool_names.txt"
REPORTS_DIR = ROOT / "reports"
ASSETS_DIR = ROOT / "assets"
CHECKPOINTS_DIR = ROOT / "checkpoints"
MPL_CACHE_DIR = ROOT / ".cache" / "matplotlib"

os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

MODELS = {
    "qwen3": {
        "class_name": "TinyQwen",
        "label": "Qwen3 dense",
        "note": "RMSNorm, RoPE, grouped-query attention and SwiGLU blocks.",
    },
    "qwen3_5": {
        "class_name": "TinyQwen35",
        "label": "Qwen3.5 hybrid",
        "note": "Gated DeltaNet linear-attention layers mixed with full attention.",
    },
    "gemma4": {
        "class_name": "TinyGemma",
        "label": "Gemma-style",
        "note": "Sliding-window/global attention pattern, sandwich norms and GeGLU.",
    },
    "deepseek3": {
        "class_name": "TinyDeepSeek",
        "label": "DeepSeek-style sparse",
        "note": "MLA compressed-KV attention and a tiny MoE feed-forward stack.",
    },
}

BATCH_SIZE = 64
BLOCK_SIZE = 24
STEPS = int(os.environ.get("ASTNG_STEPS", "1600"))
LEARNING_RATE = 3e-3
EVAL_EVERY = 100
SEED = 1337
N_SAMPLES = 16
TEMPERATURES = [0.7, 1.0, 1.2]

SECURITY_FRAGMENTS = [
    "agent",
    "ai",
    "context",
    "credential",
    "guard",
    "jailbreak",
    "llm",
    "memory",
    "policy",
    "prompt",
    "redteam",
    "secret",
    "token",
    "tool",
    "trust",
    "vault",
    "zero",
]

ACTION_FRAGMENTS = [
    "armor",
    "audit",
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
    "scan",
    "sentry",
    "shield",
    "trace",
    "watch",
    "warden",
]


def ensure_dataset() -> None:
    if DATA_FILE.exists():
        return
    subprocess.run([sys.executable, str(ROOT / "data" / "build_tool_names.py")], check=True)


def is_well_formed(name: str) -> bool:
    return bool(name) and 5 <= len(name) <= 24 and name.isascii() and name.islower() and name.isalpha()


def has_domain_shape(name: str) -> bool:
    return any(part in name for part in SECURITY_FRAGMENTS) and any(
        part in name for part in ACTION_FRAGMENTS
    )


def clear_local_modules() -> None:
    for module_name in [
        "attention",
        "block",
        "config",
        "gated_deltanet",
        "mla",
        "mlp",
        "model",
        "moe",
        "rms_norm",
        "rotary",
        "tokenizer",
    ]:
        sys.modules.pop(module_name, None)


def run_worker(model_key: str) -> None:
    import torch

    clear_local_modules()
    model_dir = ROOT / "models" / model_key
    sys.path.insert(0, str(model_dir))

    config_mod = importlib.import_module("config")
    model_mod = importlib.import_module("model")
    tokenizer_mod = importlib.import_module("tokenizer")

    ModelConfig = getattr(config_mod, "ModelConfig")
    ModelClass = getattr(model_mod, MODELS[model_key]["class_name"])
    CharTokenizer = getattr(tokenizer_mod, "CharTokenizer")

    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = CharTokenizer.from_file(str(DATA_FILE))
    text = DATA_FILE.read_text(encoding="utf-8")
    data = torch.tensor(tokenizer.encode(text), dtype=torch.long)

    cfg = ModelConfig(vocab_size=tokenizer.vocab_size)
    model = ModelClass(cfg).to(device)
    n_params = sum(parameter.numel() for parameter in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    def get_batch() -> tuple[torch.Tensor, torch.Tensor]:
        ix = torch.randint(len(data) - BLOCK_SIZE - 1, (BATCH_SIZE,))
        x = torch.stack([data[i : i + BLOCK_SIZE] for i in ix])
        y = torch.stack([data[i + 1 : i + 1 + BLOCK_SIZE] for i in ix])
        return x.to(device), y.to(device)

    loss_curve: list[list[float]] = []
    start_time = time.time()
    for step in range(1, STEPS + 1):
        x, y = get_batch()
        _, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step == 1 or step % EVAL_EVERY == 0:
            loss_curve.append([step, round(float(loss.item()), 4)])

    train_time_s = round(time.time() - start_time, 2)

    def sample(temperature: float) -> list[str]:
        model.eval()
        start = torch.full(
            (N_SAMPLES, 1),
            tokenizer.eos_id,
            dtype=torch.long,
            device=device,
        )
        with torch.no_grad():
            out = model.generate(
                start,
                max_new_tokens=cfg.max_seq_len,
                temperature=temperature,
                top_k=None,
                eos_id=tokenizer.eos_id,
            )
        model.train()
        results = []
        for row in out.tolist():
            decoded = tokenizer.decode(row[1:])
            results.append(decoded.split("\n")[0])
        return results

    samples = {str(temp): sample(temp) for temp in TEMPERATURES}
    safe_samples = samples["0.7"]
    well_formed_rate = sum(is_well_formed(item) for item in safe_samples) / len(safe_samples)
    domain_rate = sum(has_domain_shape(item) for item in safe_samples) / len(safe_samples)

    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = CHECKPOINTS_DIR / f"{model_key}.pt"
    torch.save(
        {"model": model.state_dict(), "chars": tokenizer.chars, "cfg": cfg},
        checkpoint_path,
    )

    result = {
        "model_key": model_key,
        "label": MODELS[model_key]["label"],
        "class_name": MODELS[model_key]["class_name"],
        "note": MODELS[model_key]["note"],
        "checkpoint": str(checkpoint_path.relative_to(ROOT)),
        "device": device,
        "vocab_size": tokenizer.vocab_size,
        "chars": tokenizer.chars,
        "n_params": n_params,
        "steps": STEPS,
        "batch_size": BATCH_SIZE,
        "block_size": BLOCK_SIZE,
        "learning_rate": LEARNING_RATE,
        "train_time_s": train_time_s,
        "final_loss": loss_curve[-1][1],
        "baseline_loss": round(math.log(tokenizer.vocab_size), 4),
        "loss_curve": loss_curve,
        "samples": samples,
        "well_formed_rate_t07": round(well_formed_rate, 3),
        "domain_rate_t07": round(domain_rate, 3),
    }
    print("###METRICS###" + json.dumps(result, ensure_ascii=False))


def write_json(results: list[dict]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "task": "AI security tool name generation",
        "dataset": str(DATA_FILE.relative_to(ROOT)),
        "models": results,
    }
    (REPORTS_DIR / "training_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown(results: list[dict]) -> None:
    lines = [
        "# Model Comparison",
        "",
        "All models were trained on the same character-level corpus of fictional AI security tool names.",
        "",
        "| Model | Class | Params | Final loss | Baseline | Time (s) | Well-formed %@0.7 | Domain-shape %@0.7 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['label']} | `{item['class_name']}` | {item['n_params']:,} | "
            f"{item['final_loss']} | {item['baseline_loss']} | {item['train_time_s']} | "
            f"{item['well_formed_rate_t07'] * 100:.0f}% | {item['domain_rate_t07'] * 100:.0f}% |"
        )

    lines.extend(["", "## Samples", ""])
    for item in results:
        lines.append(f"### {item['label']}")
        lines.append("")
        for temp in TEMPERATURES:
            values = ", ".join(item["samples"][str(temp)])
            lines.append(f"- `T={temp}`: {values}")
        lines.append("")

    (REPORTS_DIR / "model_comparison.md").write_text("\n".join(lines), encoding="utf-8")


def create_charts(results: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    labels = [item["label"] for item in results]

    plt.figure(figsize=(10, 5.5))
    for item in results:
        steps = [point[0] for point in item["loss_curve"]]
        losses = [point[1] for point in item["loss_curve"]]
        plt.plot(steps, losses, marker="o", linewidth=2, label=item["label"])
    plt.axhline(results[0]["baseline_loss"], color="#666666", linestyle="--", label="uniform baseline")
    plt.title("Training loss by architecture")
    plt.xlabel("Step")
    plt.ylabel("Cross-entropy loss")
    plt.grid(axis="y", alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "training_loss.png", dpi=180)
    plt.close()

    x = np.arange(len(labels))
    width = 0.35
    well_formed = [item["well_formed_rate_t07"] * 100 for item in results]
    domain = [item["domain_rate_t07"] * 100 for item in results]
    plt.figure(figsize=(10, 5.5))
    plt.bar(x - width / 2, well_formed, width, label="well-formed")
    plt.bar(x + width / 2, domain, width, label="domain-shape")
    plt.xticks(x, labels, rotation=15, ha="right")
    plt.ylim(0, 105)
    plt.ylabel("Rate at T=0.7 (%)")
    plt.title("Generated name quality checks")
    plt.grid(axis="y", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "generation_quality.png", dpi=180)
    plt.close()

    params = [item["n_params"] for item in results]
    final_losses = [item["final_loss"] for item in results]
    plt.figure(figsize=(8, 5.5))
    plt.scatter(params, final_losses, s=90)
    for label, param, loss in zip(labels, params, final_losses):
        plt.annotate(label, (param, loss), xytext=(6, 5), textcoords="offset points", fontsize=8)
    plt.xlabel("Parameters")
    plt.ylabel("Final loss")
    plt.title("Parameter count vs final loss")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "params_vs_loss.png", dpi=180)
    plt.close()


def run_all() -> None:
    ensure_dataset()
    results = []
    for model_key in MODELS:
        print(f"Training {model_key}...")
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", model_key],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            raise RuntimeError(f"{model_key} failed")
        line = next(line for line in proc.stdout.splitlines() if line.startswith("###METRICS###"))
        result = json.loads(line[len("###METRICS###") :])
        results.append(result)
        print(
            f"  {result['label']}: loss={result['final_loss']} "
            f"params={result['n_params']:,} quality={result['well_formed_rate_t07'] * 100:.0f}%"
        )

    write_json(results)
    write_markdown(results)
    create_charts(results)
    print("Reports and charts written.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=sorted(MODELS))
    args = parser.parse_args()
    if args.worker:
        run_worker(args.worker)
    else:
        run_all()


if __name__ == "__main__":
    main()

