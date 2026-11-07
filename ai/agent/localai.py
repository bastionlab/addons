"""Local AI on the host: Ollama + Open WebUI (+ SearXNG, subgen) in the `ai` CT. Registers its containers for the
core's service_restart / service_uptime and the two model actions the Ask bar and Metrics offer."""
import re

from dash_sdk import action, ct, services

services({"ollama": ("ai", "systemd", "ollama"), "open-webui": ("ai", "systemd", "open-webui"),
          "searxng": ("ai", "docker", "searxng"), "subgen": ("ai", "docker", "subgen")})

MODEL_RE = re.compile(r"^[a-zA-Z0-9][\w.:/-]{0,80}$")


def _model(args):
    model = str(args.get("model", ""))
    if not MODEL_RE.match(model):
        raise ValueError("invalid model name")
    if not ct("ai"):
        raise ValueError("this box has no `ai` CT in config.json")
    return model


@action("ollama_pull")
def a_ollama_pull(args):
    model = _model(args)
    return f"download the Ollama model {model} (can take a while)", ["pct", "exec", str(ct("ai")), "--", "ollama", "pull", model], 4 * 3600


@action("ollama_stop")
def a_ollama_stop(args):
    model = _model(args)
    return f"unload {model} from VRAM (the model stays on disk)", ["pct", "exec", str(ct("ai")), "--", "ollama", "stop", model], 120


@action("ollama_delete")
def a_ollama_delete(args):
    model = _model(args)
    return f"delete the Ollama model {model} from disk (it can be pulled again)", ["pct", "exec", str(ct("ai")), "--", "ollama", "rm", model], 120
