import pandas as pd
from typing import Iterator, Dict, Optional
import logging
import os
from dotenv import load_dotenv
import csv

load_dotenv()

logger = logging.getLogger(__name__)

class CSVDataHandler:
    def __init__(self):
        self.csv_path = os.getenv('CSV_PATH', 'data/users.csv')
        self.instructions_path = 'data/domain_instructions.csv'
        self.df = self._load_data()
        self.instructions = self._load_instructions()
        self.current_index = 0
        
    def _load_instructions(self) -> Dict[str, Dict]:
        if not os.path.exists(self.instructions_path):
            # Create instructions file with headers if it doesn't exist
            with open(self.instructions_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['domain', 'url', 'instructions'])
            return {}
            
        instructions = {}
        df = pd.read_csv(self.instructions_path)
        for _, row in df.iterrows():
            instructions[row['domain']] = {
                'url': row['url'],
                'instructions': row['instructions']
            }
        return instructions
    
    def get_domain_instructions(self, domain: str) -> Optional[Dict]:
        return self.instructions.get(domain)
        
    def get_next_user(self) -> Dict:
        if self.current_index >= len(self.df):
            return None
            
        row = self.df.iloc[self.current_index].to_dict()
        self.current_index += 1
        return row
        
    def mark_processed(self, index: int, status: str):
        self.df.at[index, 'status'] = status
        self.df.to_csv(self.csv_path, index=False)