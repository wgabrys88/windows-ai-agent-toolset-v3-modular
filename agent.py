# agent.py
from __future__ import annotations
import os
import time
import base64
import json
import urllib.request
from typing import Any, Dict, List

import winapi


def post_to_lm(payload: Dict[str, Any], endpoint: str, timeout: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def prune_old_screenshots(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pairs = []
    i = 0
    while i < len(messages):
        if (i + 1 < len(messages) and
            messages[i].get("role") == "tool" and
            messages[i].get("name") == "take_screenshot" and
            messages[i + 1].get("role") == "user" and
            isinstance(messages[i + 1].get("content"), list)):
            pairs.append((i, i + 1))
            i += 2
        else:
            i += 1
    if len(pairs) <= 1:
        return messages
    drop = set()
    for tool_idx, user_idx in pairs[:-1]:
        drop.add(tool_idx)
        drop.add(user_idx)
    return [m for i, m in enumerate(messages) if i not in drop]


def run_agent(
    system_prompt: str,
    task_prompt: str,
    tools_schema: List[Dict[str, Any]],
    cfg: Dict[str, Any],
) -> str:
    endpoint = cfg["endpoint"]
    model_id = cfg["model_id"]
    timeout = cfg["timeout"]
    temperature = cfg["temperature"]
    max_tokens = cfg["max_tokens"]
    target_w = cfg["target_w"]
    target_h = cfg["target_h"]
    dump_dir = cfg["dump_dir"]
    dump_prefix = cfg["dump_prefix"]
    dump_start = cfg["dump_start"]
    max_steps = cfg["max_steps"]
    step_delay = cfg["step_delay"]

    os.makedirs(dump_dir, exist_ok=True)

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt},
    ]

    dump_idx = dump_start
    last_screen_w, last_screen_h = winapi.get_screen_size()

    for _ in range(max_steps):
        resp = post_to_lm(
            {
                "model": model_id,
                "messages": messages,
                "tools": tools_schema,
                "tool_choice": "auto",
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            endpoint,
            timeout,
        )

        msg = resp["choices"][0]["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return msg.get("content", "")

        if len(tool_calls) > 1:
            for extra_tc in tool_calls[1:]:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": extra_tc["id"],
                        "name": extra_tc["function"]["name"],
                        "content": "error: only one tool call per response allowed",
                    }
                )
            tool_calls = tool_calls[:1]

        for tc in tool_calls:
            name = tc["function"]["name"]
            arg_str = tc["function"].get("arguments", "{}")
            call_id = tc["id"]
            content = ""

            try:
                if name == "take_screenshot":
                    png_bytes, screen_w, screen_h = winapi.capture_screenshot_png(
                        target_w, target_h
                    )
                    last_screen_w, last_screen_h = screen_w, screen_h

                    fn = os.path.join(
                        dump_dir, f"{dump_prefix}{dump_idx:04d}.png"
                    )
                    with open(fn, "wb") as f:
                        f.write(png_bytes)
                    dump_idx += 1

                    content = "Screenshot captured."
                    b64 = base64.b64encode(png_bytes).decode("ascii")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": name,
                            "content": content,
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Current screen:"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": "data:image/png;base64," + b64
                                    },
                                },
                            ],
                        }
                    )
                    messages = prune_old_screenshots(messages)

                elif name == "move_mouse":
                    args = json.loads(arg_str)
                    xn = float(args["x"])
                    yn = float(args["y"])
                    xn = max(0.0, min(1000.0, xn))
                    yn = max(0.0, min(1000.0, yn))
                    winapi.move_mouse_norm(xn, yn)
                    time.sleep(0.06)
                    content = f"Cursor moved to ({xn:.0f}, {yn:.0f})."

                elif name == "click_mouse":
                    winapi.click_mouse()
                    time.sleep(0.06)
                    content = "Mouse clicked."

                elif name == "type_text":
                    args = json.loads(arg_str)
                    text = str(args["text"])
                    winapi.type_text(text)
                    time.sleep(0.06)
                    content = f"Typed: {text}"

                elif name == "scroll_down":
                    winapi.scroll_down()
                    time.sleep(0.06)
                    content = "Scrolled down."

                else:
                    content = "error: unknown_tool"

            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                content = f"error: {str(e)}"

            if name != "take_screenshot":
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": content,
                    }
                )

        time.sleep(step_delay)

    return ""
