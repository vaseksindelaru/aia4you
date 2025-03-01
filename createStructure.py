import os

def create_project_structure():
    structure = {
        "aia4you_project": [
            "streamlit_app/app.py",
            "streamlit_app/show.py",
            "models/template.py",
            "apis/gb.py",
            "apis/cluster.py",
            "apis/detect_candle.py",
            "apis/detect_rebound.py",
            "apis/llm/tot.py",
            "external_apis/db_api.py",
            "external_apis/binance_api.py",
            "external_apis/chat_gpt.py",
            "data/raw/",
            "data/processed/",
            "data/database.db",
            "tests/test_models.py",
            "tests/test_apis.py",
            "README.md"
        ]
    }
    
    for root, files in structure.items():
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith("/"):
                os.makedirs(file_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write("# " + file.split("/")[-1])
    
    print("Estructura del proyecto creada con éxito.")

if __name__ == "__main__":
    create_project_structure()