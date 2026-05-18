from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def native_hosts(self) -> list[str]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        pass
