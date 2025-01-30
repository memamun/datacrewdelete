import pandas as pd
from typing import Iterator, Dict
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class CSVDataHandler:
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or os.getenv('CSV_PATH', 'data/users.csv')
        self.df = pd.read_csv(self.csv_path)
        self.current_index = 0
        
    def get_next_user(self) -> Dict:
        if self.current_index >= len(self.df):
            return None
            
        row = self.df.iloc[self.current_index].to_dict()
        self.current_index += 1
        return row
        
    def mark_processed(self, index: int, status: str):
        self.df.at[index, 'status'] = status
        self.df.to_csv(self.csv_path, index=False)