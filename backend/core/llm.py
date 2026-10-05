import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# 优先尝试这些模型。
# 如果当前不可用，会自动从 OpenRouter 模型列表中寻找其他免费模型。
PREFERRED_FREE_MODELS = [
    "stealth/space-bunny-alpha",
    "nex-agi/nex-n2.5-mini:free",
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "google/gemma-3-4b-it:free",
]

_selected_model = None


def is_free_model(model) -> bool:
    """判断模型是否免费。"""

    data = getattr(model, "model_extra", {}) or {}

    pricing = data.get("pricing", {})

    prompt_price = pricing.get("prompt")
    completion_price = pricing.get("completion")

    return (
        str(prompt_price) in {"0", "0.0", "0.000000"}
        and str(completion_price) in {"0", "0.0", "0.000000"}
    )


def get_free_models() -> list[str]:
    """从 OpenRouter 当前模型列表中获取免费模型。"""

    models = client.models.list().data

    free_models = []

    for model in models:
        if is_free_model(model):
            free_models.append(model.id)

    return free_models


def select_model() -> str:
    """自动选择当前可用的免费模型。"""

    global _selected_model

    if _selected_model:
        return _selected_model

    free_models = get_free_models()

    if not free_models:
        raise RuntimeError(
            "OpenRouter 当前没有找到可用的免费模型。"
        )

    # 优先使用我们指定的模型
    for model in PREFERRED_FREE_MODELS:
        if model in free_models:
            _selected_model = model
            print(f"[LLM] Selected free model: {_selected_model}")
            return _selected_model

    # 如果优先模型都不可用，就使用 API 返回的第一个免费模型
    _selected_model = free_models[0]

    print(f"[LLM] Selected free model: {_selected_model}")

    return _selected_model


def chat(system_prompt: str, user_message: str) -> str:
    """调用 OpenRouter 免费模型。"""

    global _selected_model

    free_models = get_free_models()

    if not free_models:
        raise RuntimeError(
            "OpenRouter 当前没有可用的免费模型。"
        )

    # 当前已经选择过的模型优先
    candidates = []

    if _selected_model and _selected_model in free_models:
        candidates.append(_selected_model)

    # 然后加入优先模型
    for model in PREFERRED_FREE_MODELS:
        if model in free_models and model not in candidates:
            candidates.append(model)

    # 最后加入其他免费模型
    for model in free_models:
        if model not in candidates:
            candidates.append(model)

    last_error = None

    for model in candidates:
        try:
            print(f"[LLM] Trying model: {model}")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                temperature=0.2,
            )

            _selected_model = model

            print(f"[LLM] Success: {model}")

            return response.choices[0].message.content

        except Exception as exc:
            last_error = exc

            print(
                f"[LLM] Model unavailable: {model}"
            )

            continue

    raise RuntimeError(
        "OpenRouter 所有可用免费模型调用均失败。"
        f"最后一个错误: {last_error}"
    )