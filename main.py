import importlib

extract  = importlib.import_module("src.01_extract")

if __name__ == "__main__":
    extract.get_ibge_data()