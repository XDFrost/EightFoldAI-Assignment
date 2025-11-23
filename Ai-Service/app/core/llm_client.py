from langchain_google_genai import ChatGoogleGenerativeAI
from app.Config.dataConfig import Config

settings = Config.Config.from_env()

class LLMClient:
    def __init__(self) -> None:
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llmModel,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.llmTemperature
        )

    def get_llm(self):
        return self.llm
