import re
import requests
import dataclasses
import json
import time
from random import randint
from argparse import ArgumentParser

OUTPUT_FILE = "audiobook_metadata.json"

parser = ArgumentParser(description="Scrape metadata from OverDrive API")
parser.add_argument("languages", nargs="*", default=["de", "en"], help="Languages to include (default: de, en)")
parser.add_argument("--type", "-t", type=str, default="audiobook", help="Media type to scrape (default: audiobook)")
parser.add_argument("--output", "-o", type=str, default=OUTPUT_FILE, help="Output JSON file name")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")

args = parser.parse_args()
OUTPUT_FILE = args.output
LANGUAGES = args.languages
MEDIA_TYPE = args.type
DEBUG = args.debug


def main():
    all_extracted_data = []
    page = 1
    max_retries = 3
    
    print("Starting scraping...", flush=True)
    with open("scraper.log", "w") as log:
        log.write("Starting scraping...\n")
    
    try:
        while True:
            URL = f"https://thunder.api.overdrive.com/v2/libraries/voebb/media?language={','.join(LANGUAGES)}&sortBy=newlyadded&mediaTypes={MEDIA_TYPE}&format={MEDIA_TYPE}-overdrive,{MEDIA_TYPE}-overdrive-provisional&includeFacets=false&perPage=100&page={page}&truncateDescription=false&x-client-id=dewey"
            
            msg = f"Fetching page {page}..."
            print(msg, flush=True)
            with open("scraper.log", "a") as log:
                log.write(msg + "\n")
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(URL)
                    if response.status_code == 200:
                        break
                    else:
                        print(f"  Attempt {attempt + 1} failed with status {response.status_code}", flush=True)
                        time.sleep(2)
                except Exception as e:
                    print(f"  Attempt {attempt + 1} error: {e}", flush=True)
                    time.sleep(2)
            else:
                msg = "  Max retries reached. Stopping."
                print(msg, flush=True)
                with open("scraper.log", "a") as log:
                    log.write(msg + "\n")
                break
    
            try:
                resp_json = response.json()
                items = resp_json.get("items", [])
            except ValueError:
                msg = "  Failed to parse JSON"
                print(msg, flush=True)
                with open("scraper.log", "a") as log:
                    log.write(msg + "\n")
                break
    
            if not items:
                msg = "  No more items found. Finished."
                print(msg, flush=True)
                with open("scraper.log", "a") as log:
                    log.write(msg + "\n")
                break
            
            msg = f"  Found {len(items)} items."
            print(msg, flush=True)
            with open("scraper.log", "a") as log:
                log.write(msg + "\n")

            for item in items:
                if DEBUG:
                    # Append each item as a single JSON object per line (NDJSON)
                    with open("debug_item.json", "a", encoding="utf-8") as debug_file:
                        debug_file.write(json.dumps(item, ensure_ascii=False) + "\n")
                # Extract creators
                creators = item.get("creators", [])
                authors = [c["name"] for c in creators if c.get("role") == "Author"]
                narrators = [c["name"] for c in creators if c.get("role") == "Narrator"]
    
                # Extract genres
                subjects = item.get("subjects", [])
                genres = [s["name"] for s in subjects]
    
                # Extract languages
                languages_data = item.get("languages", [])
                languages = [l["name"] for l in languages_data]

                # Extract description
                description = item.get("description", "")
                if description:
                    description = re.sub(r"<[^>]+>", "", description)

                # Extract series info
                series_info = item.get("detailedSeries", {})
                if series_info:
                    series_id = series_info.get("seriesId")
                    series_name = series_info.get("seriesName")
                    readingOrder = series_info.get("readingOrder")
    
                # Extract duration
                duration = None
                formats = item.get("formats", [])
                for fmt in formats:
                    if fmt.get("id") in ["audiobook-mp3", "audiobook-overdrive", "audiobook-overdrive-provisional"]:
                            if "duration" in fmt:
                                duration = fmt["duration"]
                                break
                
                # Extract cover
                cover = None
                covers = item.get("covers", {})
                if covers:
                    try:
                        cover = covers.get("cover510Wide").get("href")
                    except Exception as e:
                        print(f"Error extracting cover: {e}")
                
                
                metadata = {
                    "title": item.get("title"),
                    "subtitle" : item.get("subtitle"),
                    "authors": authors,
                    "narrators": narrators,
                    "publisher": item.get("publisher", {}).get("name"),
                    "publishDate": item.get("publishDate"),
                    "description": description,
                    "genres": genres,
                    "languages": languages,
                    "ISBN": next((fmt.get("isbn") for fmt in item.get("formats", []) if "isbn" in fmt), None),
                    "duration": duration,
                    "coverURL": cover,
                    "sampleURL": item.get("sample", {}).get("href"),
                    'series' : {
                        "seriesID": series_info.get("seriesId") if series_info else None,
                        "seriesName": series_info.get("seriesName") if series_info else None,
                        "readingOrder": series_info.get("readingOrder") if series_info else None,
                    } if series_info else None,
                }
                for key, value in metadata.items():
                    if isinstance(value, str):
                        metadata[key] = value.strip()
                        metadata[key] = value.replace('--', ' — ')
                        metadata[key] = value.replace(r'\n', ' ')
                all_extracted_data.append(metadata)
            
            page += 1
            
            if page % 5 == 0:
                 with open("audiobook_metadata.json", "w", encoding="utf-8") as f:
                    json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
                 with open("scraper.log", "a") as log:
                    log.write(f"  Saved intermediate results ({len(all_extracted_data)} items).\n")
    
            # Be nice to the API
            sleep_time = randint(1, 10)/2
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopping early...", flush=True)
        with open("scraper.log", "a") as log:
            log.write("\nStopping early...\n")
    
    print(f"Total items extracted: {len(all_extracted_data)}", flush=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
