from abc import ABC, abstractmethod
from typing import Optional
from .schemas import JobExtraction

class AIProvider(ABC):
    @abstractmethod
    async def extract_job_information(self, text: str) -> JobExtraction:
        """
        Extract structured information and suspicious signals from the job text.
        """
        pass

    @abstractmethod
    async def extract_job_information_from_document(self, file_bytes: bytes, mime_type: str) -> JobExtraction:
        """
        Extract structured information and suspicious signals from an uploaded document (image or PDF).
        """
        pass
