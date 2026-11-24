import html
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from recommender import get_recommendations, get_allowed_ratings

PORT = 8000

ALL_GENRES = [
    "Action & Adventure", "Anime Features", "Anime Series", "British TV Shows",
    "Children & Family Movies", "Classic & Cult TV", "Classic Movies", "Comedies",
    "Crime TV Shows", "Cult Movies", "Documentaries", "Docuseries", "Dramas",
    "Faith & Spirituality", "Horror Movies", "Independent Movies", "International Movies",
    "International TV Shows", "Kids' TV", "Korean TV Shows", "LGBTQ Movies", "Movies",
    "Music & Musicals", "Reality TV", "Romantic Movies", "Romantic TV Shows",
    "Sci-Fi & Fantasy", "Science & Nature TV", "Spanish-Language TV Shows",
    "Sports Movies", "Stand-Up Comedy", "Stand-Up Comedy & Talk Shows",
    "TV Action & Adventure", "TV Comedies", "TV Dramas", "TV Horror", "TV Mysteries",
    "TV Sci-Fi & Fantasy", "TV Shows", "TV Thrillers", "Teen TV Shows", "Thrillers"
]


def render_page(tipe="Movie", selected_genres=None, usia=17, top_n=5, results=None, searched=False):
    if selected_genres is None:
        selected_genres = ["Comedies"]

    genre_checkboxes = ""
    for g in ALL_GENRES:
        checked = "checked" if g in selected_genres else ""
        safe_g = html.escape(g)
        genre_checkboxes += f"""
        <label class="genre-item">
            <input type="checkbox" name="genres" value="{safe_g}" {checked}>
            <span>{safe_g}</span>
        </label>
        """

    results_html = ""
    if searched:
        allowed = sorted(list(get_allowed_ratings(usia)))
        results_html += f"""
        <div class="info-banner">
            <strong>Filter Aktif:</strong> Tipe <b>{html.escape(tipe)}</b> | Usia <b>{usia} tahun</b> 
            (Rating diizinkan: <code>{', '.join(allowed)}</code>) | Genre: <b>{html.escape(', '.join(selected_genres))}</b>
        </div>
        """

        if not results:
            results_html += """
            <div class="empty-state">
                <h3>Tidak ada tontonan yang cocok</h3>
                <p>Coba tambah pilihan genre lain atau sesuaikan tipe tontonan dengan usia penonton.</p>
            </div>
            """
        else:
            for idx, item in enumerate(results, start=1):
                results_html += f"""
                <div class="card">
                    <div class="card-header">
                        <span class="rank">#{idx}</span>
                        <h3>{html.escape(item['title'])}</h3>
                        <span class="badge-rating">{html.escape(item['rating'])}</span>
                        <span class="badge-score">Kemiripan: {item['similarity_percent']}%</span>
                    </div>
                    <div class="card-genre"><strong>Genre:</strong> {html.escape(item['listed_in'])}</div>
                    <p class="card-desc">{html.escape(item['description'])}</p>
                </div>
                """

    movie_selected = "selected" if tipe == "Movie" else ""
    tv_selected = "selected" if tipe == "TV Show" else ""

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Rekomendasi Film & Series</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 24px; padding: 20px; background: #1e293b; border-radius: 12px; border-bottom: 4px solid #e50914; }}
        header h1 {{ margin: 0 0 8px 0; color: #ffffff; }}
        header p {{ margin: 0; color: #94a3b8; }}
        .form-box {{ background: #1e293b; padding: 24px; border-radius: 12px; margin-bottom: 24px; }}
        .row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; }}
        .col {{ flex: 1; min-width: 200px; }}
        label.title-lbl {{ display: block; font-weight: 600; margin-bottom: 6px; color: #f8fafc; }}
        select, input[type="number"] {{ width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 15px; box-sizing: border-box; }}
        .genre-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px; max-height: 220px; overflow-y: auto; background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; }}
        .genre-item {{ display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; }}
        button {{ width: 100%; padding: 14px; background: #e50914; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 12px; }}
        button:hover {{ background: #b80710; }}
        .info-banner {{ background: #1e293b; padding: 14px 18px; border-left: 4px solid #38bdf8; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }}
        .card {{ background: #1e293b; padding: 18px 20px; border-radius: 10px; margin-bottom: 14px; border: 1px solid #334155; }}
        .card-header {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }}
        .card-header h3 {{ margin: 0; font-size: 18px; color: #fff; flex: 1; }}
        .rank {{ background: #334155; color: #fff; padding: 3px 9px; border-radius: 6px; font-weight: bold; font-size: 13px; }}
        .badge-rating {{ background: #f59e0b; color: #000; padding: 3px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }}
        .badge-score {{ background: #10b981; color: #000; padding: 3px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }}
        .card-genre {{ font-size: 13px; color: #38bdf8; margin-bottom: 8px; }}
        .card-desc {{ margin: 0; font-size: 14px; color: #cbd5e1; line-height: 1.5; }}
        .empty-state {{ text-align: center; padding: 30px; background: #1e293b; border-radius: 10px; color: #94a3b8; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Sistem Rekomendasi Film & Series</h1>
        <p>Content-Based Filtering (TF-IDF & Cosine Similarity) dengan Filter Batas Usia</p>
    </header>

    <form method="GET" action="/" class="form-box">
        <div class="row">
            <div class="col">
                <label class="title-lbl">Tipe Tontonan</label>
                <select name="tipe">
                    <option value="Movie" {movie_selected}>Movie</option>
                    <option value="TV Show" {tv_selected}>TV Show</option>
                </select>
            </div>
            <div class="col">
                <label class="title-lbl">Usia Penonton (Tahun)</label>
                <input type="number" name="usia" min="1" max="100" value="{usia}" required>
            </div>
            <div class="col">
                <label class="title-lbl">Jumlah Rekomendasi (Top-N)</label>
                <input type="number" name="top_n" min="1" max="20" value="{top_n}" required>
            </div>
        </div>

        <label class="title-lbl">Pilih Genre (Bisa lebih dari satu)</label>
        <div class="genre-grid">
            {genre_checkboxes}
        </div>

        <button type="submit" name="search" value="1">Cari Rekomendasi</button>
    </form>

    {results_html}
</div>
</body>
</html>"""


class RecommenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        tipe = params.get("tipe", ["Movie"])[0]
        selected_genres = params.get("genres", ["Comedies"])
        usia = int(params.get("usia", ["17"])[0])
        top_n = int(params.get("top_n", ["5"])[0])
        searched = "search" in params

        results = None
        if searched:
            results = get_recommendations(tipe, selected_genres, usia, top_n=top_n)

        page = render_page(tipe, selected_genres, usia, top_n, results, searched)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Sembunyikan log request mentah agar terminal tetap bersih


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    print(f"Aplikasi berjalan di: {url}")
    print("Tekan Ctrl+C di terminal untuk menghentikan server.")
    webbrowser.open(url)
    server = HTTPServer(("127.0.0.1", PORT), RecommenderHandler)
    server.serve_forever()
