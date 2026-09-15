# ============================================================
# VeriNews AI - Duplicate News Story Detector v6.0
# Sentence Embedding Clustering for Wire Service / Syndicate News
# ============================================================

from services.verifier import embedding_model, extract_domain
from sklearn.metrics.pairwise import cosine_similarity

def detect_duplicate_news(articles: list, similarity_threshold: float = 0.90) -> dict:
    """
    Groups wire-service syndications and republished news stories.
    Articles with >= 90% content similarity are merged into a single story group.
    """
    if not articles:
        return {
            "unique_stories_count": 0,
            "duplicate_count": 0,
            "groups": [],
            "message": "No articles retrieved."
        }

    # Extract text representation
    texts = [f"{a.get('title', '')} {a.get('content', '')[:600]}" for a in articles]
    embeddings = embedding_model.encode(texts)
    sim_matrix = cosine_similarity(embeddings)

    n = len(articles)
    visited = [False] * n
    groups = []
    unique_articles = []
    duplicate_cnt = 0

    for i in range(n):
        if visited[i]:
            continue

        visited[i] = True
        canonical_article = articles[i].copy()
        domain_i = extract_domain(canonical_article.get("url", ""))
        publishers = [domain_i or "Source 1"]
        duplicate_urls = []

        for j in range(i + 1, n):
            if not visited[j]:
                score = sim_matrix[i][j]
                if score >= similarity_threshold:
                    visited[j] = True
                    dup_art = articles[j]
                    domain_j = extract_domain(dup_art.get("url", ""))
                    if domain_j and domain_j not in publishers:
                        publishers.append(domain_j)
                    duplicate_urls.append(dup_art.get("url", ""))
                    duplicate_cnt += 1

        canonical_article["republished_count"] = len(publishers)
        canonical_article["syndicated_publishers"] = publishers
        unique_articles.append(canonical_article)

        groups.append({
            "group_id": i + 1,
            "original_title": canonical_article.get("title", "News Story"),
            "primary_publisher": domain_i,
            "publisher_count": len(publishers),
            "all_publishers": publishers,
            "duplicate_urls": duplicate_urls,
            "is_syndicated": len(publishers) > 1
        })

    message = (
        f"Independently verified across {n} articles ({len(groups)} unique story sources)."
        if duplicate_cnt == 0 else
        f"Wire service syndication detected: {duplicate_cnt} duplicate republishing(s) grouped across {len(groups)} unique stories."
    )

    return {
        "unique_stories_count": len(groups),
        "duplicate_count": duplicate_cnt,
        "groups": groups,
        "unique_articles": unique_articles,
        "message": message
    }
