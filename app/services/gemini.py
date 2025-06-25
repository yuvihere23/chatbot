import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-2.0-flash")

def extract_intent(prompt: str) -> str:
    instruction = (
        "You are an intent classification AI. Given a cloud-related user query, "
        "output the action in this format:\n"
        "action: <ACTION_NAME>\n"
        "optional_parameters: {...}\n\n"
        f"Prompt: {prompt}"
    )
    response = model.generate_content(instruction)
    return response.text.strip()


def generate_final_answer(prompt: str, azure_data: str) -> str:
    instruction = (
        "You are a cloud assistant. Given a user prompt and Azure API response, "
        "respond in a helpful way.\n\n"
        f"User prompt: {prompt}\n\n"
        f"Azure data:\n{azure_data}"
    )
    response = model.generate_content(instruction)
    return response.text.strip()
