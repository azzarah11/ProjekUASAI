import csv
import os
import re

RAW_PATH = "netflix_titles.csv"
OUT_PATH = "data/processed/clean_data.csv"

VALID_RATINGS = {
    "G", "PG", "PG-13", "R", "NC-17",
    "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG", "TV-14", "TV-MA",
    "NR", "UR",
}
VALID_TYPES = {"Movie", "TV Show"}


def clean_text(text: str) -> str:
    text = str(text).lower()
    # Hapus tanda baca/karakter non-huruf & non-angka
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Rapikan spasi berlebih
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_netflix_data(raw_path: str = RAW_PATH, out_path: str = OUT_PATH):
    crucial_cols = ["title", "type", "rating", "listed_in", "description"]
    final_cols = ["title", "type", "rating", "listed_in", "description", "combined_features"]

    seen_titles = set()
    clean_rows = []
    unique_ratings = set()
    unique_genres = set()

    # Baca file CSV menggunakan modul bawaan Python
    with open(raw_path, mode="r", encoding="utf-8", errors="replace") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            # 1. Cek missing value pada kolom krusial
            if any(not row.get(col) or not row[col].strip() for col in crucial_cols):
                continue

            title = row["title"].strip()
            show_type = row["type"].strip()
            rating = row["rating"].strip()
            listed_in = row["listed_in"].strip()
            description = row["description"].strip()

            # 2. Hapus duplikat berdasarkan title
            if title in seen_titles:
                continue

            # 3. Validasi type dan rating (cegah nilai aneh seperti '74 min')
            if show_type not in VALID_TYPES or rating not in VALID_RATINGS:
                continue

            seen_titles.add(title)

            # 4. Gabungkan & bersihkan teks untuk combined_features
            raw_combined = f"{listed_in} {rating} {description}"
            combined_features = clean_text(raw_combined)

            clean_rows.append({
                "title": title,
                "type": show_type,
                "rating": rating,
                "listed_in": listed_in,
                "description": description,
                "combined_features": combined_features,
            })

            # Kumpulkan nilai unik rating & genre
            unique_ratings.add(rating)
            for genre in listed_in.split(","):
                g = genre.strip()
                if g:
                    unique_genres.add(g)

    # 5. Simpan hasil bersih ke CSV baru
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=final_cols)
        writer.writeheader()
        writer.writerows(clean_rows)

    sorted_ratings = sorted(unique_ratings)
    sorted_genres = sorted(unique_genres)

    print(f"Berhasil menyimpan {len(clean_rows)} baris ke {out_path}")
    print(f"Rating unik ({len(sorted_ratings)}): {sorted_ratings}")
    print(f"Genre unik ({len(sorted_genres)}): {sorted_genres}")

    return clean_rows


if __name__ == "__main__":
    preprocess_netflix_data()
