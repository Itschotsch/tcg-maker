import os


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