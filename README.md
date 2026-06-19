# TakeMeter

So basically I built a classifier that reads NBA Reddit posts and tells you what kind of post it is — whether someone is actually breaking down the game with stats (analysis), just throwing out a bold opinion with nothing to back it up (hot_take), or typing in all caps because something crazy just happened in the game (reaction).

---

## Community

I picked r/nba because I actually like basketball and I know how those conversations go. Some people come in with real stats and comparisons, some people just say "this player is trash" with zero evidence, and some people are just hyped up after a big play. Those differences felt real and worth trying to teach a model. Plus there's tons of posts to work with.

---

## Label Taxonomy

### `analysis`
The post is making an actual argument with real evidence — stats, historical comparisons, something you could fact check. The evidence would hold up even if you took out the opinion language.

**Example 1:** "Jokic's assist-to-turnover ratio of 5.1 this postseason is the highest ever recorded for a center in playoff history. Compare that to Shaq at 2.8 — it's not even close. The case for him as the greatest passing big man ever is not a debate."

**Example 2:** "The 2016 Warriors went 73-9 with the exact same core. The drop-off after adding KD wasn't about wins — it was about defensive scheme. They switched to more drop coverage which inflated opponent 3P% by 2.4 points."

---

### `hot_take`
Someone just saying something bold and confident with nothing really backing it up. They're not arguing, they're asserting.

**Example 1:** "LeBron is cooked. He's never winning another ring. The era has passed him by. Book it."

**Example 2:** "Tatum is not a top-5 player and never will be. Celtics fans are delusional. He disappears every time it matters."

---

### `reaction`
Someone typing in real time because something just happened in the game. Pure emotion, no real argument.

**Example 1:** "THAT CURRY THREE AT THE BUZZER I AM LITERALLY DEAD what is happening this series is insane"

**Example 2:** "I cannot believe they just blew a 20-point lead in the fourth. I'm done. I'm actually done with this team."

---

## Data Collection

So Reddit's API ended up being locked down when I tried to scrape it, so I used Groq to generate synthetic NBA posts instead. I gave it my label definitions and had it generate posts in batches of 25 for each label. I reviewed samples to make sure they actually matched what I was going for before using them.

**Label distribution:**

| Label | Count |
|---|---|
| hot_take | 70 |
| analysis | 69 |
| reaction | 68 |
| **Total** | **207** |

**3 posts that were genuinely hard to label:**

1. *"LeBron's playoff record against top seeds is below .500. He's the most overrated player ever."* — It has a stat in it so it looks like analysis, but the stat is just there to sound credible. The real point is just a bold claim. → `hot_take`

2. *"Giannis went 4/14 from the field tonight and here's why the defensive scheme worked."* — This one reacts to a specific game but also builds a real argument. Since it has at least 2 verifiable claims and works toward a conclusion I went with → `analysis`

3. *"Jalen Brunson vs SGA playoff stats: 29.4 PPG vs 27.6 PPG..."* — Just drops numbers with no point being made. Looks like analysis but there's no actual argument. → `hot_take`

---

## Fine-Tuning Approach

**Base model:** `distilbert-base-uncased` — a smaller pretrained model that already understands English, I just taught it my 3 labels on top of that.

**Ran on:** Google Colab free T4 GPU. Training took about 25 seconds for 3 epochs on 144 examples which was honestly faster than I expected.

**Hyperparameters:**

| Parameter | Value | Why |
|---|---|---|
| num_train_epochs | 3 | More than this risks memorizing the training data |
| learning_rate | 2e-5 | Standard starting point for this type of model |
| per_device_train_batch_size | 16 | Works fine on T4 GPU |
| weight_decay | 0.01 | Helps prevent overfitting on a small dataset |

The main decision I made was keeping epochs at 3. With only 144 training examples going higher would probably just make the model memorize the data instead of actually learning the patterns.

---

## Baseline

I used Groq's `llama-3.3-70b-versatile` in zero-shot mode — meaning no training, just gave it my label definitions and examples in a prompt and had it classify each test post.

**Prompt I used:**
```
You are classifying posts from r/nba, the NBA basketball subreddit.
Assign each post to exactly one of the following categories.

analysis: The post makes a structured argument supported by specific verifiable
evidence — statistics, historical comparisons, or tactical observations.
Example: "Jokic's assist-to-turnover ratio of 5.1 this postseason is the highest
ever recorded for a center in playoff history."

hot_take: A bold confident opinion stated without meaningful supporting evidence.
Example: "LeBron is cooked. He's never winning another ring. Book it."

reaction: An immediate emotional response to a specific game, play, or moment.
Example: "THAT CURRY THREE AT THE BUZZER I AM LITERALLY DEAD"

Respond with ONLY the label name. Do not explain your reasoning.

Valid labels:
analysis
hot_take
reaction
```

---

## Evaluation Report

### Accuracy

| Model | Accuracy |
|---|---|
| Zero-shot baseline (Groq) | 96.9% |
| Fine-tuned DistilBERT | 87.5% |
| Difference | -9.4% |

---

### Per-class metrics — fine-tuned model

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| analysis | 0.77 | 1.00 | 0.87 | 10 |
| hot_take | 0.91 | 0.91 | 0.91 | 11 |
| reaction | 1.00 | 0.73 | 0.84 | 11 |
| **overall** | **0.90** | **0.88** | **0.87** | **32** |

---

### Per-class metrics — baseline

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| analysis | 1.00 | 0.90 | 0.95 | 10 |
| hot_take | 0.92 | 1.00 | 0.96 | 11 |
| reaction | 1.00 | 1.00 | 1.00 | 11 |
| **overall** | **0.97** | **0.97** | **0.97** | **32** |

---

### Confusion matrix — fine-tuned model

|  | Predicted: analysis | Predicted: hot_take | Predicted: reaction |
|---|---|---|---|
| **True: analysis** | 10 | 0 | 0 |
| **True: hot_take** | 1 | 10 | 0 |
| **True: reaction** | 2 | 1 | 8 |

The model did well on analysis and hot_take. Most of the mistakes were reaction posts getting misclassified — either as analysis or hot_take.

---

### Wrong predictions

**#1 — "Damian Lillard is UNCONSCIOUS right now!!!! 15 points in the last 5 minutes"**
- True: `reaction` → Predicted: `analysis` (confidence: 0.34)
- The word "unconscious" is basketball slang for someone who is shooting really well. The model never learned that slang and saw "player name + performance stat" and thought analysis. The low confidence tells you the model wasn't even sure about this one.

**#2 — "The Bucks will never win a chip with Budenholzer as their coach, he's too soft"**
- True: `hot_take` → Predicted: `analysis` (confidence: 0.39)
- This is that exact edge case I wrote about in planning.md. Specific claim about a specific person looks like analysis to the model even when there's zero evidence backing it up. Another low confidence prediction.

**#3 — "Tatum just hit a tough fadeaway... he's on fire"**
- True: `reaction` → Predicted: `hot_take` (confidence: 0.34)
- "He's on fire" sounds like a bold take if you don't know it was typed live during a game. The model has no way to know the context, so it made a reasonable but wrong guess.

---

### Sample classifications

| Post | Predicted | Confidence | Correct? |
|---|---|---|---|
| "Jokic's usage rate of 32.4% in the fourth quarter is statistically elite — only 3 players in NBA history have sustained that in the playoffs" | analysis | 0.91 | Yes |
| "Durant will never be considered the GOAT no matter what he does. KD fans are delusional" | hot_take | 0.88 | Yes |
| "HE JUST DID THAT WITH 2 SECONDS LEFT ARE YOU KIDDING ME" | reaction | 0.95 | Yes |
| "Damian Lillard is UNCONSCIOUS right now!!!! 15 points in the last 5 minutes" | analysis | 0.34 | No |
| "The Bucks will never win a chip with Budenholzer as their coach" | analysis | 0.39 | No |

The Jokic analysis prediction makes sense — it has a specific stat, a historical comparison, and a specific context. That's exactly what the label definition asks for.

---

## What the Model Learned vs What I Intended

I wanted the model to learn the actual reasoning structure — does this post build an argument, assert without evidence, or just react emotionally?

What it actually learned was more like pattern matching. Numbers and player names → analysis. Strong declarative sentences → hot_take. Caps and exclamation points → reaction. That works most of the time but breaks down when the surface patterns don't match the actual intent — like basketball slang or a question typed in frustration.

The bigger thing I noticed is that the baseline (Groq) beat my fine-tuned model 96.9% vs 87.5%. That's probably because my training data was generated by Groq in the first place. A massive model classifying text it essentially wrote will always have an edge over a tiny model trained on that same text. If I had used real Reddit posts the results would probably look different.

---

## Spec Reflection

**One way the spec helped:** Making me write the decision rule for hard edge cases before touching any data was actually the most useful part. I had to think about the hot_take vs analysis boundary before labeling anything, which made my definitions way sharper than they would have been if I just started labeling and figured it out as I went.

**One way I diverged:** The spec assumes you're collecting real posts from Reddit. I ended up using synthetic data because Reddit's API access was blocked. That changed the whole dynamic — instead of messy real-world annotation I was dealing with the question of whether AI-generated training data would actually teach a model anything useful. It did, but the baseline comparison shows the limitation clearly.

---

## AI Usage

**1. Dataset generation:** I used Groq to generate 207 NBA posts across 3 labels since Reddit's API was unavailable. I gave it my label definitions from planning.md and had it generate in batches of 25. I reviewed samples from each batch to make sure they matched the definitions before using them for training.

**2. Error pattern analysis:** After seeing the 4 wrong predictions I looked for what they had in common. 3 out of 4 were reaction posts that got misclassified. The pattern was short posts with basketball-specific slang or evaluative language that the model read as a different label type. That finding went into the reflection above.

---

## How to Run

**Generate the dataset:**
```bash
cd ai201-project3-takemeter
source venv/bin/activate
pip install groq python-dotenv
python3 scrapper/generate_dataset.py
```

**Fine-tune and evaluate:**
Open `takemeter_notebook.ipynb` in Google Colab, set runtime to T4 GPU, run all cells in order, upload `data/nba_posts_labeled.csv` when prompted in Section 1.

**Repo structure:**
```
ai201-project3-takemeter/
├── scrapper/
│   ├── collect_nba_posts.py    ← Reddit scraper (blocked by API restrictions)
│   └── generate_dataset.py     ← synthetic data generator using Groq
├── data/
│   ├── nba_posts_labeled.csv   ← 207 labeled posts
│   ├── confusion_matrix.png    ← confusion matrix image
│   └── evaluation_results.json ← accuracy numbers from both models
├── takemeter_notebook.ipynb    ← the notebook where training happens
├── planning.md                 ← my design thinking before the project
└── README.md                   ← this file
```