from typing import Dict, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

class DomainDatabase:
    def __init__(self):
        self.db_file = "data/domain_data.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error loading domain cache from {self.db_file}")
                return {}
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_domain_data(self, domain: str) -> Optional[Dict]:
        return self.cache.get(domain)

    def save_domain_data(self, domain: str, data: Dict):
        self.cache[domain] = data
        self._save_cache() 