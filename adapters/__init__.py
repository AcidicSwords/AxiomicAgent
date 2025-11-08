# Import adapter streams so they self-register with the registry.
from adapters.conversation_brainstorm import stream as _cb_stream  # noqa: F401
from adapters.research_learning import stream as _rl_stream  # noqa: F401
from adapters.creation_blueprint import stream as _bp_stream  # noqa: F401
from adapters.curriculum import stream as _curriculum  # noqa: F401
