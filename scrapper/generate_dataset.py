from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import csv
import json
import time
import os

# ─── PATHLIB SETUP ───────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR     = PROJECT_ROOT / "data"
OUTPUT_FILE  = DATA_DIR / "nba_posts_labeled.csv"

DATA_DIR.mkdir(exist_ok=True)

# ─── LOAD .env ───────────────────────────────────────────────────────────────
# load_dotenv() reads the .env file from the project root
# and loads the variables into the environment so os.getenv() can find them.
# This means your API key is NEVER written in code — it lives only in .env
# which is listed in .gitignore and never pushed to GitHub.

load_dotenv(PROJECT_ROOT / ".env")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found.\n"
        "Make sure your .env file in the project root contains:\n"
        "  GROQ_API_KEY=your_key_here"
    )

client = Groq(api_key=GROQ_API_KEY)

# ─── PROMPTS PER LABEL ───────────────────────────────────────────────────────

LABEL_PROMPTS = {
    "analysis": """Generate {n} realistic r/nba Reddit posts that are ANALYSIS posts.

Definition: Makes a structured argument supported by specific verifiable evidence — statistics, historical comparisons, or tactical observations. The evidence would support the claim even with neutral language.

Rules:
- Include real-sounding stats, percentages, historical comparisons
- Posts vary in length — some short with 1-2 stats, some longer with full arguments
- Cover different topics: player comparisons, team strategy, historical debates
- Sound like real Reddit users, not formal essays
- Some can be short comments, some longer original posts

Return ONLY a JSON array of {n} strings. No explanation, no markdown, just the raw JSON array.
Example: ["post one here", "post two here"]""",

    "hot_take": """Generate {n} realistic r/nba Reddit posts that are HOT TAKE posts.

Definition: A bold confident opinion stated without meaningful supporting evidence. Asserts a strong claim rather than argues for it.

Rules:
- Strong confident opinions with little or no real evidence
- Cover different topics: player rankings, team takes, predictions
- Sound like real Reddit users typing fast and confidently
- Mix of short punchy takes and slightly longer ones that are still evidence-free
- Can include mild frustration, hype, or strong stances

Return ONLY a JSON array of {n} strings. No explanation, no markdown, just the raw JSON array.
Example: ["post one here", "post two here"]""",

    "reaction": """Generate {n} realistic r/nba Reddit posts that are REACTION posts.

Definition: An immediate emotional response to a specific game, play, or moment. Little to no argument — just expressing a feeling in real time.

Rules:
- Emotional in-the-moment responses to specific plays or games
- Reference specific moments, players making plays, scores
- Short to medium length, high energy
- Mix of excitement, disappointment, disbelief, humor
- Sound like someone typing live while watching
- Can use caps for emphasis, ellipses, exclamation points

Return ONLY a JSON array of {n} strings. No explanation, no markdown, just the raw JSON array.
Example: ["post one here", "post two here"]"""
}

# ─── GENERATE ONE BATCH ──────────────────────────────────────────────────────

def generate_batch(label, n):
    prompt = LABEL_PROMPTS[label].format(n=n)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    posts = json.loads(raw)
    return posts

# ─── GENERATE ALL POSTS FOR ONE LABEL ────────────────────────────────────────

def generate_posts(label, total):
    all_posts  = []
    batch_size = 25
    batches    = total // batch_size
    remainder  = total % batch_size

    sizes = [batch_size] * batches
    if remainder:
        sizes.append(remainder)

    for i, n in enumerate(sizes):
        print(f"  Batch {i+1}/{len(sizes)} ({n} posts)...")
        try:
            batch = generate_batch(label, n)
            all_posts.extend(batch)
            print(f"  Got {len(batch)} — running total: {len(all_posts)}")
        except json.JSONDecodeError as e:
            print(f"  JSON parse error on batch {i+1}: {e}")
            print("  Skipping batch and continuing...")
        except Exception as e:
            print(f"  Error on batch {i+1}: {e}")
            print("  Skipping batch and continuing...")

        time.sleep(1)

    return all_posts

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print("TakeMeter — dataset generator (Groq)")
    print("=" * 50)
    print("Generating 70 posts per label, 210 total...\n")

    all_rows = []

    for label in ["analysis", "hot_take", "reaction"]:
        print(f"Generating label: '{label}'")
        posts = generate_posts(label, 70)

        for text in posts:
            all_rows.append({
                "text":  text.strip(),
                "label": label,
                "notes": "synthetic",
            })

        print(f"Finished '{label}' — {len(posts)} posts\n")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "notes"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved {len(all_rows)} posts to: {OUTPUT_FILE}")
    print("\nLabel distribution:")
    from collections import Counter
    counts = Counter(r["label"] for r in all_rows)
    for label, count in counts.items():
        print(f"  {label}: {count}")
    print("\nDone! Upload nba_posts_labeled.csv to Colab next.")

if __name__ == "__main__":
    main()