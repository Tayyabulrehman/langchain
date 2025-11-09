import os

import openai
from dotenv import load_dotenv

load_dotenv()
from langchain.llms.base import LLM
from typing import List, Optional, Any
import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from llama_stack_client import LlamaStackClient



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



class ChatGPTModel(LLM):
    def __init__(self, model_name: str = "gpt-4-turbo", temperature: float = 0.7, **kwargs):
        super().__init__(**kwargs)
     # Make sure your key is in env

    @property
    def _llm_type(self) -> str:
        return "chatgpt"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call OpenAI ChatCompletion API
        """
        model_name = os.getenv("OPENAI_MODEL_NAME","gpt-4-turbo")
        temperature =os.getenv("OPENAI_MODEL_TEMPERATURE",0.7)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            stop=stop,
            **kwargs
        )

        return response.choices[0].message.content