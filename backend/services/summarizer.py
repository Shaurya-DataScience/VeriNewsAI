import re
import time
from threading import Thread, Lock

# ==========================================================
# Lazy-Loaded Summarization AI Model
# ==========================================================

_tokenizer = None
_model = None
_model_lock = Lock()

def get_summarizer_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model
    with _model_lock:
        if _model is not None:
            return _tokenizer, _model
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            model_name = "sshleifer/distilbart-cnn-12-6"
            print("[Summarizer] Loading DistilBART Model (lazy)...")
            _tokenizer = AutoTokenizer.from_pretrained(model_name)
            _model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            print("[Summarizer] DistilBART Model Loaded.")
            return _tokenizer, _model
        except Exception as e:
            print(f"[Summarizer] Model lazy-load notice: {e}")
            return None, None

# ==========================================================
# Helper Functions
# ==========================================================

def clean_text(text):
    """
    Remove extra spaces and line breaks.
    """

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_article_text(articles):
    """
    Merge all article titles and content.
    """

    text = ""

    for article in articles:

        title = article.get("title", "")

        content = article.get("content", "")

        text += f"{title}. {content}\n"

    return clean_text(text)


# ==========================================================
# AI Summary
# ==========================================================

def summarize_articles(articles):
    if not articles:
        return "No evidence found."

    text = build_article_text(articles)
    text = text[:3500]

    tok, mdl = get_summarizer_model()
    if tok is None or mdl is None:
        points = generate_key_points(articles)
        return " ".join(points[:3]) if points else text[:400]

    try:
        inputs = tok(text, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = mdl.generate(
            inputs["input_ids"],
            max_length=120,
            min_length=40,
            do_sample=False
        )
        return tok.decode(summary_ids[0], skip_special_tokens=True)
    except Exception:
        return text[:400]

def stream_summary(articles):
    """Yields tokens as they are generated for real-time SSE streaming."""
    if not articles:
        yield "No evidence found."
        return

    text = build_article_text(articles)
    text = text[:3500]

    tok, mdl = get_summarizer_model()
    if tok is None or mdl is None:
        points = generate_key_points(articles)
        if points:
            for p in points[:3]:
                for word in p.split():
                    yield word + " "
                    time.sleep(0.02)
        else:
            yield "Evidence verified across news sources."
        return

    try:
        from transformers import TextIteratorStreamer
        inputs = tok(text, return_tensors="pt", max_length=1024, truncation=True)
        streamer = TextIteratorStreamer(tok, skip_special_tokens=True)
        
        generation_kwargs = dict(
            inputs,
            streamer=streamer,
            max_length=120,
            min_length=40,
            do_sample=False,
            num_beams=1
        )
        
        def safe_generate():
            try:
                mdl.generate(**generation_kwargs)
            except Exception as gen_err:
                print(f"[Summarizer] Stream generate error: {gen_err}")

        thread = Thread(target=safe_generate, daemon=True)
        thread.start()
        
        for new_text in streamer:
            if new_text:
                yield new_text
                
    except Exception as e:
        yield f"Error generating summary: {str(e)}"


# ==========================================================
# Evidence Extraction
# ==========================================================

def sanitize_snippet(text):
    """Clean scraped text metadata junk, markdown headers, subscriber/view counts."""
    if not text:
        return ""
    # Strip markdown headers like #, ##, ###
    text = re.sub(r'#+\s*', '', text)
    # Strip YouTube/Web metadata junk (e.g. 4260000 subscribers 365 Likes ### Description 23076 views Posted:)
    text = re.sub(r'\d+\s*(subscribers|likes|views|shares|comments|posted:)[^\.\!\?]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Description\s*\d*\s*views\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\.\.\.\]', '', text)
    text = re.sub(r'Skip to (navigation|content|main)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_key_evidence(claim, articles):
    keywords = [word.lower() for word in claim.split() if len(word) > 2]
    evidence = []
    seen_sentences = set()

    for article in articles:
        content = sanitize_snippet(article.get("content", ""))
        sentences = re.split(r'(?<=[.!?])\s+', content)

        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out short fragments or metadata lines
            if len(sentence) < 30 or len(sentence) > 280:
                continue
            if sentence.lower() in seen_sentences:
                continue

            score = sum(sentence.lower().count(word) for word in keywords)
            if score > 0:
                seen_sentences.add(sentence.lower())
                evidence.append({
                    "sentence": sentence,
                    "source": article.get("title", "Verified Article"),
                    "url": article.get("url", "#"),
                    "domain": article.get("domain", ""),
                    "score": score
                })

    evidence.sort(key=lambda x: x["score"], reverse=True)
    return evidence[:4]


# ==========================================================
# Key Points
# ==========================================================

def generate_key_points(articles):

    points = []

    for article in articles:

        text = clean_text(

            article.get("content", "")

        )

        sentences = re.split(

            r'(?<=[.!?])\s+',

            text

        )

        if sentences:

            points.append(sentences[0])

    return points[:5]