from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
import os
from dotenv import load_dotenv

load_dotenv()


def get_openai_model(model_name: str, **kwargs):
    api_key = kwargs.get("api_key", os.getenv("OPENAI_API_KEY"))
    base_url = kwargs.get(
        "base_url", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )

    provider = OpenAIProvider(
        api_key=api_key,
        base_url=base_url,
    )

    model = OpenAIModel(
        model_name=model_name,
        provider=provider,
    )

    return model
