import os

from dotenv import load_dotenv

load_dotenv()
from langchain.llms.base import LLM
from typing import List, Optional, Any
import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from llama_stack_client import LlamaStackClient
from openai import OpenAI


class CustomAPIModel(LLM):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # self.tools = []
        # self.api_url = api_url
        # self.api_key = api_key

    @property
    def _llm_type(self) -> str:
        return "custom_api_model"

    def _call(
            self,
            prompt: str,
            stop: Optional[list[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> str:
        url = "https://router.huggingface.co/v1/chat/completions"

        # Define the JSON payload
        payload = {
            "model": "deepseek-ai/DeepSeek-V3-0324",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # Send POST request
        headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

        response = requests.post(url, json=payload,headers=headers).json()
        return response.get('choices')[0].get("message").get("content")

    # def bind_tools(self, tools: list):
    #     """
    #     Dummy implementation to support LangChain integration.
    #     If the tools are not needed, you can leave this as a placeholder.
    #     """
    #     self.tools = tools
    #     return self


def get_response(prompt):
    url = "http://localhost:8080/v1/chat/completions"

    # Define the JSON payload
    payload = {
        "model": "llama3.1",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    # Send POST request
    response = requests.post(url, json=payload).json()
    return response.get('choices')[0].get("message").get("content")
