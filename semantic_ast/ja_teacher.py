"""Run every primitive prompt against the teacher model and save the result
as an expression dictionary (task_list.md: "意味ASTに基づいてQwen3系モデル
で日本語表現を生成").

One request per expression-dictionary key -- 26 of them, the rows of
THIRD_PARTY.md's substitution table (see ja_prompts.py's docstring on why
the document's prose says 27).

Everything about *how* the model is called is fixed by THIRD_PARTY.md
"### 呼び出し方法（vLLM 0.29.0）": non-thinking mode via
``chat_template_kwargs={"enable_thinking": False}`` (never ``/no_think`` in
the prompt text), and JSON-only output enforced with vLLM's structured
outputs rather than by asking nicely and parsing prose.

Two files come out of a run:

* ``expressions/candidates.json`` -- the expression dictionary itself
  (ja_dictionary.py's format), ready for the human approval step.
* ``expressions/generation_log.jsonl`` -- one record per primitive holding
  every field homework.md requires to be recorded (model name / revision /
  quantization / inference library + version / system prompt / sampling
  settings / seed / timestamp / prompt hash), plus the raw model output, so
  a dictionary entry can always be traced back to the exact request that
  produced it.

The raw output is logged before parsing and the dictionary is written even
when some entries come back malformed: this stage records what the model
said, it does not judge or repair it (that is the human reviewer's job).

Usage:
    python semantic_ast/ja_teacher.py                  # every primitive
    python semantic_ast/ja_teacher.py --keys filter:ge_k map:add_k
    python semantic_ast/ja_teacher.py --dry-run        # prompts + log only, no GPU
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ja_dictionary import CANDIDATES_PATH, DEFAULT_DIR, ExpressionDictionary, merge
from ja_prompts import PRIMITIVES, SYSTEM_PROMPT, PrimitiveSpec, build_messages, json_schema, prompt_record

MODEL = "Qwen/Qwen3-4B-AWQ"
QUANTIZATION = "awq"
LOG_PATH = DEFAULT_DIR / "generation_log.jsonl"

# Defaults for THIRD_PARTY.md's "TBD（実行時に確定・記録する）" rows. They are
# recorded verbatim in every log record, so changing them here changes what
# the log says, never what the log means.
DEFAULT_TEMPERATURE = 0.8
DEFAULT_TOP_P = 0.95
DEFAULT_SEED = 0
DEFAULT_MAX_TOKENS = 2048
DEFAULT_MAX_MODEL_LEN = 4096
DEFAULT_GPU_MEMORY_UTILIZATION = 0.85

# vLLM's default top-k/top-p path is FlashInfer's sampling kernel, which is
# JIT-compiled with nvcc at first use and therefore needs a full CUDA
# toolkit -- not just the driver. On a machine without one the engine dies
# during warm-up ("Could not find nvcc"), so we default to vLLM's native
# torch sampler and record the choice in the generation log (it is part of
# how the samples were drawn). ``--flashinfer-sampler`` turns it back on
# where the toolkit exists; an explicit env var always wins.
FLASHINFER_SAMPLER_ENV = "VLLM_USE_FLASHINFER_SAMPLER"


@dataclass(frozen=True)
class SamplingConfig:
    """The sampling settings homework.md wants fixed and recorded."""

    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    seed: int = DEFAULT_SEED
    max_tokens: int = DEFAULT_MAX_TOKENS


def resolve_revision(model: str = MODEL) -> Optional[str]:
    """The model revision actually used (THIRD_PARTY.md's
    "モデルのrevision/コミットID" row).

    Read from the local Hugging Face cache first so an offline run still
    records a real commit id; falls back to the Hub, then to ``None`` (which
    the log stores explicitly rather than silently omitting).
    """
    try:
        from huggingface_hub import snapshot_download

        return Path(snapshot_download(model, local_files_only=True)).name
    except Exception:
        pass
    try:
        from huggingface_hub import HfApi

        return HfApi().model_info(model).sha
    except Exception:
        return None


def vllm_version() -> Optional[str]:
    try:
        import vllm

        return vllm.__version__
    except Exception:
        return None


def run_metadata(model: str, sampling: SamplingConfig, dry_run: bool) -> dict:
    """The per-run half of homework.md's 記録項目, shared by every record."""
    return {
        "model": model,
        "revision": resolve_revision(model),
        "quantization": QUANTIZATION,
        "inference_library": "vllm",
        "inference_library_version": vllm_version(),
        "thinking_mode": "disabled (chat_template_kwargs={'enable_thinking': False})",
        "sampling": asdict(sampling),
        "sampler_backend": "flashinfer" if os.environ.get(FLASHINFER_SAMPLER_ENV) != "0" else "vllm native (torch)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_prompt": SYSTEM_PROMPT,
        "dry_run": dry_run,
    }


def parse_response(spec: PrimitiveSpec, text: str) -> tuple[list, Optional[str]]:
    """Pull the ``expressions`` array out of one model response.

    Returns ``(expressions, error)``; on any problem the expressions list is
    empty and ``error`` describes what was wrong, for the log. The raw text
    is saved by the caller either way.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], f"response is not valid JSON: {exc}"
    if not isinstance(payload, dict) or "expressions" not in payload:
        return [], "response JSON has no 'expressions' key"
    expressions = payload["expressions"]
    if not isinstance(expressions, list):
        return [], f"'expressions' is {type(expressions).__name__}, expected list"
    return expressions, None


def _specs_for(keys: Optional[list[str]]) -> list[PrimitiveSpec]:
    if not keys:
        return list(PRIMITIVES.values())
    unknown = [k for k in keys if k not in PRIMITIVES]
    if unknown:
        raise SystemExit(f"unknown expression-dictionary key(s): {', '.join(unknown)}")
    return [PRIMITIVES[k] for k in keys]


def generate(
    specs: list[PrimitiveSpec],
    sampling: SamplingConfig,
    model: str = MODEL,
    max_model_len: int = DEFAULT_MAX_MODEL_LEN,
    gpu_memory_utilization: float = DEFAULT_GPU_MEMORY_UTILIZATION,
) -> list[str]:
    """Send one chat request per primitive; return the raw response texts.

    One ``SamplingParams`` per prompt, because each primitive carries its own
    JSON schema (the 生成件数目安 bounds differ per row).
    """
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams

    llm = LLM(
        model=model,
        quantization=QUANTIZATION,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        seed=sampling.seed,
    )

    conversations = [build_messages(spec) for spec in specs]
    params = [
        SamplingParams(
            temperature=sampling.temperature,
            top_p=sampling.top_p,
            seed=sampling.seed,
            max_tokens=sampling.max_tokens,
            structured_outputs=StructuredOutputsParams(json=json_schema(spec)),
        )
        for spec in specs
    ]

    outputs = llm.chat(
        conversations,
        sampling_params=params,
        chat_template_kwargs={"enable_thinking": False},
    )
    return [output.outputs[0].text for output in outputs]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keys", nargs="*", help="only these expression-dictionary keys (default: every key)")
    parser.add_argument("--dry-run", action="store_true", help="build prompts and write the log, but never load the model")
    parser.add_argument("--out", type=Path, default=CANDIDATES_PATH, help=f"dictionary output (default: {CANDIDATES_PATH})")
    parser.add_argument("--log", type=Path, default=LOG_PATH, help=f"generation log output (default: {LOG_PATH})")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--top-p", type=float, default=DEFAULT_TOP_P)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--max-model-len", type=int, default=DEFAULT_MAX_MODEL_LEN)
    parser.add_argument("--gpu-memory-utilization", type=float, default=DEFAULT_GPU_MEMORY_UTILIZATION)
    parser.add_argument(
        "--flashinfer-sampler",
        action="store_true",
        help=f"use FlashInfer's sampling kernels (needs nvcc; default: {FLASHINFER_SAMPLER_ENV}=0)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="merge into the existing dictionary at --out instead of replacing it",
    )
    args = parser.parse_args(argv)

    if not args.flashinfer_sampler:
        os.environ.setdefault(FLASHINFER_SAMPLER_ENV, "0")

    specs = _specs_for(args.keys)
    sampling = SamplingConfig(
        temperature=args.temperature, top_p=args.top_p, seed=args.seed, max_tokens=args.max_tokens
    )
    meta = run_metadata(args.model, sampling, dry_run=args.dry_run)
    print(f"{len(specs)} prompt(s); model={meta['model']} revision={meta['revision']} vllm={meta['inference_library_version']}")

    if args.dry_run:
        texts = ["" for _ in specs]
    else:
        texts = generate(
            specs,
            sampling,
            model=args.model,
            max_model_len=args.max_model_len,
            gpu_memory_utilization=args.gpu_memory_utilization,
        )

    expressions_by_key: dict[str, list] = {}
    records: list[dict] = []
    for spec, text in zip(specs, texts):
        expressions, error = ([], "dry run: model not called") if args.dry_run else parse_response(spec, text)
        expressions_by_key[spec.key] = expressions
        records.append(
            {
                "run": meta,
                "prompt": prompt_record(spec),
                "raw_response": text,
                "num_expressions": len(expressions),
                "parse_error": error,
            }
        )
        status = error or f"{len(expressions)} expressions"
        print(f"  {spec.key:<24} {status}")

    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"generation log -> {args.log}")

    if args.dry_run:
        # every entry would be empty; writing them would wipe a real
        # dictionary sitting at --out
        print(f"dry run: expression dictionary at {args.out} left untouched")
        return 0

    dictionary = ExpressionDictionary.from_expressions(expressions_by_key)
    if args.merge and args.out.exists():
        dictionary = merge([ExpressionDictionary.load(args.out, strict=False), dictionary])
    dictionary.save(args.out)
    print(f"expression dictionary -> {args.out} ({len(dictionary)} keys, missing {len(dictionary.missing_keys())})")

    problems = dictionary.validate()
    if problems:
        print(f"\n{len(problems)} structural problem(s) -- left in the file as-is for human review:")
        for problem in problems:
            print(f"  - {problem}")
    duplicates = dictionary.duplicate_report()
    if duplicates:
        print(f"\nduplicate expressions in {len(duplicates)} key(s): {', '.join(duplicates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
