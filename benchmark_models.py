"""Compare local models on the action format used by the experiment."""

import json
import time

import requests

from environment import Environment

URL = "http://127.0.0.1:11434/api/chat"
MODELS = [
    "llama3.1:8b-instruct-q4_K_M",
    "huihui_ai/llama3.2-abliterate:3b",
    "granite4:3b",
    "phi4-mini:latest",
    "pedrolucas/smollm3:3b-q4_k_m",
    "yi:6b",
    "hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q4_K_M",
    # X tested: structurally valid output, but invented unsupported actions.
    "hf.co/SC117/LFM2.5-VL-3B-Uncensored-GGUF:Q4_K_M",
]
PROMPTS = [
    'Return exactly one JSON action: {"action":"list","start":0,"limit":20}',
    'Return exactly one JSON action sending a private message to Brook saying hello.',
    'Return exactly one JSON action reading lands/index.md from line 0 with limit 40.',
]


def run_case(model: str, prompt: str) -> tuple[bool, float, float]:
    started = time.perf_counter()
    response = requests.post(
        URL,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 180, "temperature": 0.1},
        },
        timeout=120,
    )
    elapsed = time.perf_counter() - started
    body = response.json()
    text = body.get("message", {}).get("content", "")
    action = Environment.parse_action_response(text)
    valid = isinstance(action, dict) and isinstance(action.get("action"), str)
    eval_count = body.get("eval_count", 0)
    eval_duration = body.get("eval_duration", 0)
    tokens_per_second = (
        eval_count / (eval_duration / 1_000_000_000)
        if eval_count and eval_duration
        else 0.0
    )
    return valid, tokens_per_second, elapsed


def main() -> None:
    for model in MODELS:
        valid = 0
        speeds = []
        elapsed = []
        for prompt in PROMPTS:
            try:
                ok, speed, wall_time = run_case(model, prompt)
            except Exception as error:
                print(json.dumps({"model": model, "error": str(error)}))
                break
            valid += int(ok)
            speeds.append(speed)
            elapsed.append(wall_time)
        else:
            print(json.dumps({
                "model": model,
                "valid": f"{valid}/{len(PROMPTS)}",
                "tokens_per_second": round(sum(speeds) / len(speeds), 1),
                "average_seconds": round(sum(elapsed) / len(elapsed), 2),
            }))


if __name__ == "__main__":
    main()
