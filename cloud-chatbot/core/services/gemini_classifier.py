import json
import google.generativeai as genai
from functools import lru_cache
from typing import Dict, Any
from core.utils.prompt_templates import classification_prompt

class GeminiClassifier:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    @lru_cache(maxsize=500)
    def classify(self, query_text: str) -> Dict[str, Any]:
        """Classify query using Gemini with caching"""
        try:
            prompt = classification_prompt.format(query=query_text)
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            return {
                "query_type": "complex",
                "intent": "classification_failed",
                "parameters": {}
            }