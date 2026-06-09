import importlib

extract    = importlib.import_module("src.01_extract")
transform  = importlib.import_module("src.02_transform")

if __name__ == "__main__":
    extract.get_ibge_data()
    transform.transform()