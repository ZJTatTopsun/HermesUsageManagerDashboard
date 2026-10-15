"""Minimal observer registration; usage collection starts in M3."""


def on_pre_llm_call(**kwargs):
    return None


def register(ctx):
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
