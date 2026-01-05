# Run with: python main.py scenarios.json <scenario_number>
# Example: python main.py scenarios.json 1

# main.py
from __future__ import annotations
import os
import sys
import json

import winapi
from agent import run_agent


def main() -> None:
    if os.name != "nt":
        sys.exit("Windows required")

    winapi.init_dpi()

    if len(sys.argv) < 3:
        sys.exit("Usage: python main.py <scenario_file> <scenario_num>")

    scenario_file = sys.argv[1]
    scenario_num = int(sys.argv[2])

    with open(scenario_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    system_prompt = data["shared_system_prompt"]
    scenarios = data["scenarios"]

    if scenario_num < 1 or scenario_num > len(scenarios):
        sys.exit("Invalid scenario number")

    task_prompt = scenarios[scenario_num - 1]["task_prompt"]

    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "take_screenshot",
                "description": "Capture screen and return current view with cursor visible.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "move_mouse",
                "description": "Move mouse using normalized coordinates 0..1000 relative to the screenshot.",
                "parameters": {
                    "type": "object",
                    "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                    "required": ["x", "y"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click_mouse",
                "description": "Left click at current cursor position.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "type_text",
                "description": "Type text into the focused control.",
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scroll_down",
                "description": "Scroll down by one notch.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]

    cfg = {
        "endpoint": "http://localhost:1234/v1/chat/completions",
        "model_id": "qwen/qwen3-vl-2b-instruct",
        "timeout": 240,
        "temperature": 0.2,
        "max_tokens": 2048,
        "target_w": 1344,
        "target_h": 756,
        "dump_dir": "dumps",
        "dump_prefix": "screen_",
        "dump_start": 1,
        "keep_last_screenshots": 1,
        "max_steps": 50,
        "step_delay": 0.4,
    }

    final_response = run_agent(system_prompt, task_prompt, tools_schema, cfg)
    print(final_response)


if __name__ == "__main__":
    main()