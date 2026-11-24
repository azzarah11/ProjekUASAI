import csv
import math
import re
from collections import Counter

DATA_PATH = "data/processed/clean_data.csv"

# 1. Mapping Usia ke 14 Rating Unik Dataset
def get_allowed_ratings(age: int) -> set:
    if age < 7:
        # Balita / Anak kecil
        return {"G", "TV-Y", "TV-G"}
    elif age < 13:
        # Anak-anak (7 - 12 tahun)
        return {"G", "PG", "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG"}
    elif age < 17:
        # Remaja (13 - 16 tahun)
        return {"G", "PG", "PG-13", "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG", "TV-14"}
    elif age < 18:
        # Remaja akhir (17 tahun - boleh R tapi belum NC-17/TV-MA)
        return {"G", "PG", "PG-13", "R", "TV-Y", "TV-Y7", "TV-Y7-FV", "TV-G", "TV-PG", "TV-14"}
    else:
        # Dewasa (18+ tahun - semua rating termasuk NR/UR)
        return {
            "G", "NC-17", "NR", "PG", "PG-13", "R",
            "TV-14", "TV-G", "TV-MA", "TV-PG", "TV-Y", "TV-Y7", "TV-Y7-FV", "UR"
        }


def clean_query(text: str) -> list:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if len(w) > 1]


def load_data(path: str = DATA_PATH) -> list:
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 2. Mesin Rekomendasi TF-IDF + Cosine Similarity (Tanpa Library Eksternal)
def get_recommendations(tipe_tontonan: str, genre_list: list, usia: int, top_n: int = 5) -> list:
    data = load_data()
    allowed_ratings = get_allowed_ratings(usia)

    # Filter tahap 1: Tipe tontonan (Movie/TV Show) & Batas Usia
    filtered_items = [
        row for row in data
        if row["type"] == tipe_tontonan and row["rating"] in allowed_ratings
    ]

    if not filtered_items:
        return []

    # Siapkan korpus dokumen & query pengguna
    docs_tokens = [clean_query(row["combined_features"]) for row in filtered_items]
    query_text = " ".join(genre_list)
    query_tokens = clean_query(query_text)

    if not query_tokens:
        return []

    # Hitung Document Frequency (DF) & Inverse Document Frequency (IDF)
    num_docs = len(docs_tokens)
    df_counts = Counter()
    for tokens in docs_tokens:
        for token in set(tokens):
            df_counts[token] += 1

    idf = {
        term: math.log((num_docs + 1) / (df + 1)) + 1.0
        for term, df in df_counts.items()
    }

    # Fungsi pembentuk vektor TF-IDF ternormalisasi L2
    def compute_tfidf_vector(tokens: list) -> dict:
        tf_counts = Counter(tokens)
        total_terms = len(tokens) if tokens else 1
        vec = {}
        norm_sq = 0.0
        for term, count in tf_counts.items():
            if term in idf:
                weight = (count / total_terms) * idf[term]
                vec[term] = weight
                norm_sq += weight * weight
        norm = math.sqrt(norm_sq)
        if norm > 0:
            for term in vec:
                vec[term] /= norm
        return vec

    query_vec = compute_tfidf_vector(query_tokens)

    # Hitung Cosine Similarity antara query dan setiap tontonan
    scored_results = []
    for idx, row in enumerate(filtered_items):
        doc_vec = compute_tfidf_vector(docs_tokens[idx])
        # Dot product dari dua vektor yang sudah ternormalisasi L2 = Cosine Similarity
        score = sum(query_vec[t] * doc_vec[t] for t in query_vec if t in doc_vec)

        if score > 0:
            scored_results.append({
                "title": row["title"],
                "type": row["type"],
                "rating": row["rating"],
                "listed_in": row["listed_in"],
                "description": row["description"],
                "similarity_score": round(score, 4),
                "similarity_percent": round(score * 100, 2)
            })

    # Urutkan dari skor kemiripan tertinggi dan ambil Top-N
    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_results[:top_n]


# 3. Fungsi Pengujian & Evaluasi (Precision@K & Age Compliance)
def evaluate_scenario(tipe: str, genres: list, usia: int, k: int = 5):
    results = get_recommendations(tipe, genres, usia, top_n=k)
    allowed = get_allowed_ratings(usia)

    print(f"\n=== SKENARIO UJI: Tipe={tipe} | Genre={genres} | Usia={usia} tahun (Top-{k}) ===")
    if not results:
        print("Tidak ada rekomendasi ditemukan.")
        return

    genre_hits = 0
    age_hits = 0
    target_genres = {g.lower() for g in genres}

    for rank, item in enumerate(results, start=1):
        item_genres = {g.strip().lower() for g in item["listed_in"].split(",")}
        is_genre_match = len(target_genres.intersection(item_genres)) > 0
        is_age_safe = item["rating"] in allowed

        if is_genre_match:
            genre_hits += 1
        if is_age_safe:
            age_hits += 1

        print(f"{rank}. {item['title']} [{item['rating']}] - Skor: {item['similarity_percent']}% | Genre: {item['listed_in']}")

    precision_at_k = (genre_hits / len(results)) * 100
    age_accuracy = (age_hits / len(results)) * 100
    print(f"--> Precision@{k} (Kecocokan Genre): {precision_at_k:.1f}% ({genre_hits}/{len(results)})")
    print(f"--> Kesesuaian Batas Usia: {age_accuracy:.1f}% ({age_hits}/{len(results)})")


if __name__ == "__main__":
    # Jalankan 3 skenario pengujian untuk bahan laporan UAS
    evaluate_scenario("Movie", ["Children & Family Movies", "Comedies"], usia=9, k=5)
    evaluate_scenario("TV Show", ["Anime Series", "TV Action & Adventure"], usia=15, k=5)
    evaluate_scenario("Movie", ["Horror Movies", "Thrillers"], usia=22, k=5)
