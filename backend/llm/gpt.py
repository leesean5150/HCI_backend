from app import main
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """Dependency that returns the initialized global OpenAI client."""
    if not hasattr(main.app.state, 'openai_client'):
         raise RuntimeError("OpenAI client not initialized during startup.")
         
    return main.app.state.openai_client