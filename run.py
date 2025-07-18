# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Permet de lancer avec `python run.py` pour le développement local
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
