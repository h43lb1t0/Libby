from pathlib import Path
from flask import Flask
from flask import render_template
from db import AudioBook, db
import json

app = Flask(__name__)


basedir = Path(__file__).resolve().parent
db_path = basedir / "instance" / "site.db"

# Ensure the instance folder exists
db_path.parent.mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from datetime import datetime

with app.app_context():
    db.create_all()
    
    # Check if database is empty
    if not db.session.execute(db.select(AudioBook)).first():
        print("Seeding database from audiobook_metadata.json...")
        json_path = basedir / "audiobook_metadata.json"
        
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            books = []
            for item in data:
                # Parse publish date
                p_date = None
                if item.get("publishDate"):
                    try:
                        p_date = datetime.fromisoformat(item["publishDate"])
                    except ValueError:
                        pass
                
                # Handle series info
                series_data = item.get("series")
                is_series = bool(series_data)
                series_id = series_data.get("seriesID") if series_data else None
                series_name = series_data.get("seriesName") if series_data else None
                reading_order = series_data.get("readingOrder") if series_data else None
                
                book = AudioBook(
                    title=item.get("title", "Unknown Title"),
                    subtitle=item.get("subtitle"),
                    authors=item.get("authors", []),
                    narrators=item.get("narrators", []),
                    publisher=item.get("publisher"),
                    publish_date=p_date,
                    description=item.get("description"),
                    genres=item.get("genres", []),
                    languages=item.get("languages", []),
                    duration=item.get("duration"),
                    cover_url=item.get("coverURL"),
                    sample_url=item.get("sampleURL"),
                    is_series=is_series,
                    series_id=series_id,
                    series_name=series_name,
                    reading_order=reading_order
                )
                books.append(book)
            
            if books:
                db.session.add_all(books)
                db.session.commit()
                print(f"Seeded {len(books)} audiobooks.")
        else:
            print("audiobook_metadata.json not found. Database initialized empty.")





from flask import request

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(db.select(AudioBook), page=page, per_page=50)
    return render_template('index.html', pagination=pagination)

if __name__ == '__main__':
    app.run(debug=True)