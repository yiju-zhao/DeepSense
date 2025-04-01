from abc import ABC, abstractmethod
from typing import Dict, Any

from pydantic import BaseModel


class ApiArgs(BaseModel):
    class Config:
        extra = "allow"
        
class BaseCrawler(ABC):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_page_content(self, url: str) -> Dict[str, Any]:
        pass
    
    def get_api_response(self, url: str, args: ApiArgs) -> Dict[str, Any]:
        pass
