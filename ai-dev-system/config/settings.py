from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    deepseek_model: str = Field(default="deepseek-r1:7b", alias="DEEPSEEK_MODEL")
    qwen_model: str = Field(default="qwen2.5-coder:7b", alias="QWEN_MODEL")
    mcp_server_host: str = Field(default="127.0.0.1", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8765, alias="MCP_SERVER_PORT")
    workspace_root: str = Field(default=".", alias="WORKSPACE_ROOT")
    max_agent_loops: int = Field(default=8, alias="MAX_AGENT_LOOPS")
    request_timeout_seconds: int = Field(default=180, alias="REQUEST_TIMEOUT_SECONDS")
    enable_rich_logs: bool = Field(default=True, alias="ENABLE_RICH_LOGS")
    chroma_persist_dir: str = Field(default=".ai_learning_memory", alias="CHROMA_PERSIST_DIR")
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
