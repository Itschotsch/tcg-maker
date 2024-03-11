from io import StringIO
import os

import pandas as pd


class TCGMakerIO:

    pwd: str

    @staticmethod
    def init(pwd):
        TCGMakerIO.pwd = pwd

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)

    @staticmethod
    def ensure_path_exists(path: str):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def write_file(path: str, content: str):
        TCGMakerIO.ensure_path_exists(os.path.dirname(path))
        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(content)

    @staticmethod
    def listdir(path: str):
        TCGMakerIO.ensure_path_exists(path)
        return os.listdir(path)
    
    @staticmethod
    def read_csv_file(csv_file: str) -> pd.DataFrame:
        if not TCGMakerIO.exists(csv_file):
            print(f"File does not exist: {csv_file}")
            return pd.DataFrame()
        return pd.read_csv(csv_file, keep_default_na=False)
    
    @staticmethod
    def read_csv_string(csv_string: str) -> pd.DataFrame:
        if not csv_string or csv_string.isspace() or len(csv_string) == 0:
            print("CSV string is empty.")
            return pd.DataFrame()
        return pd.read_csv(StringIO(csv_string), keep_default_na=False)