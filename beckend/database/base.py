import sqlite3
import os
from typing import Union, List, Any, Dict, Optional, Iterable

class BaseDB:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(os.path.dirname(base_dir), 'tracker.db')

    def execute(self, query: str, params: tuple = (), 
                fetchall: bool = False, 
                fetchone: bool = False, 
                commit: bool = False) -> Any:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Оставляем Row для удобства работы внутри метода
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if commit:
                    conn.commit()

                if fetchone:
                    res = cursor.fetchone()
                    # Конвертируем Row в обычный dict, чтобы скобки ['id'] работали всегда
                    return dict(res) if res else None
                
                if fetchall:
                    res = cursor.fetchall()
                    # Конвертируем список Row в список dict
                    return [dict(row) for row in res] if res else []

                return cursor.rowcount 
        except Exception as e:
            print(f"❌ Database Error: {e} | Query: {query}")
            return [] if fetchall else None