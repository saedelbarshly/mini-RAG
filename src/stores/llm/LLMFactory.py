from .LLMEnums import LLMEnum
from .providers import CoHereProvider, OpenAIProvider

class LLMFactory:
    def __init__(self, config):
        self.config = config
        
    def create(self, provider: str):
        if provider == LLMEnum.OPENAI.value:
            return OpenAIProvider(
                api_key=self.config.OPEN_AI_KEY,
                api_url=self.config.OPEND_AI_URL,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        if provider == LLMEnum.COHERE.value:
            return CoHereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                default_generation_max_output_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DEFAULT_TEMPERATURE
            )
        
        return None
