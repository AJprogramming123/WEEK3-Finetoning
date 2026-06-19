# TakeMeter — planning.md

## Community

I picked r/nba because I actually like basketball and I know how those conversations go. Some people come in with real breakdowns and stats, some people just say bold stuff with nothing to back it up, and some people are just hype typing after a big play. Those differences felt real and worth trying to teach a model. Plus there's a ton of posts to work with so getting 200 examples felt doable.

---

## Label Taxonomy

### Label 1: `analysis`

The post is making an actual argument with real evidence — stats, historical comparisons, something you could actually fact check. The evidence would hold up even if you took out the opinion language.

**Example 1:**
> "Jokic's assist-to-turnover ratio of 5.1 this postseason is the highest ever recorded for a center in playoff history. For context, Shaq's best was 2.8 and Kareem's was 3.1. The case for him as the greatest passing big man ever is not even a debate at this point."

**Example 2:**
> "People forget that the 2016 Warriors went 73-9 with the exact same core. The drop-off after adding KD wasn't about wins, it was about defensive scheme — they switched to more drop coverage which inflated opponent 3P% by 2.4 points."

---

### Label 2: `hot_take`

Someone just saying something bold and confident with nothing really backing it up. They're not arguing, they're just asserting.

**Example 1:**
> "LeBron is cooked. He's never winning another ring. The era has passed him by. Book it."

**Example 2:**
> "Tatum is not a top-5 player and never will be. Celtics fans are delusional. He disappears every time it matters."

---

### Label 3: `reaction`

Someone typing in real time because something just happened in the game. Pure emotion, no real argument.

**Example 1:**
> "THAT CURRY THREE AT THE BUZZER I AM LITERALLY DEAD what is happening this series is insane"

**Example 2:**
> "I cannot believe they just blew a 20-point lead in the fourth. I'm done. I'm actually done with this team."

---

## Hard Edge Cases

The trickiest posts are ones that have a stat in them but are really just hot takes dressed up to sound credible. Like this one:

> "LeBron's playoff record against top-seeded opponents is below .500. He's the most overrated player in NBA history."

That has a stat so it looks like analysis but the stat is cherry picked and the real point is just a bold claim with nothing else backing it up.

**My decision rule:** If the evidence would actually support the claim on its own in neutral language, it's `analysis`. If the stat is just there to sound credible but the post is really just asserting something, it's `hot_take`.

The other tricky case is posts that react to a specific game but also build a real argument — like "Giannis went 4/14 tonight and here's why the defensive scheme worked." That has both reaction energy and analysis structure.

**Rule for that:** If there are at least 2 specific verifiable claims and it builds toward a conclusion, I call it `analysis`. If it's mostly emotional with one stat dropped in, it's `reaction`.

---

## Data Collection Plan

My original plan was to scrape r/nba using Reddit's public API. That ended up being blocked due to authentication restrictions so I switched to generating synthetic posts using Groq's llama model instead. I gave it my label definitions and had it generate posts in batches of 25 for each label.

**Target per label:**
- `analysis`: ~70 examples
- `hot_take`: ~70 examples
- `reaction`: ~70 examples
- **Total: 210 examples**

I kept the distribution equal across labels because if one label dominates the dataset the model just learns to predict that label all the time which isn't useful.

**What I filtered out:** Anything under 15 words, posts that are just links, and anything removed or deleted. Short posts don't give the model enough to learn from.

---

## Evaluation Metrics

Accuracy alone isn't enough because it hides how the model is doing per label. If the model just guessed hot_take every single time and that happened to be 50% of the data it would get 50% accuracy and look decent even though it's completely broken.

So on top of accuracy I'm using:

- **F1 score per label** — this is the main one. It balances how often the model is right when it predicts a label vs how many of that label it actually catches. If any label has F1 near zero the model basically can't identify it at all.
- **Precision per label** — of everything the model called analysis, how many actually were?
- **Recall per label** — of all the actual analysis posts, how many did the model find?
- **Confusion matrix** — shows exactly which labels the model is mixing up and in which direction

---

## Definition of Success

For this to actually be useful it needs to be able to sort posts better than just guessing randomly.

**Minimum I'd accept:**
- Overall accuracy above 70%
- No label with F1 below 0.60 — if it completely fails one label it's not usable
- Fine-tuned model should beat the zero-shot Groq baseline by at least 5%

**What I'd call strong:**
- Accuracy above 80%
- All F1 scores above 0.70
- No single error dominating the confusion matrix

**What would make me suspicious:**
- Accuracy above 95% on a subjective task with 200 examples — probably means something leaked from test to train
- One label with near perfect recall and the others near zero — model is just predicting one thing constantly

---

## AI Tool Plan

**Label stress-testing:** Before labeling anything I gave Claude my label definitions and asked it to generate posts that sit right at the boundary between analysis and hot_take. If I couldn't cleanly classify those I knew my definitions needed work before I started on 200 examples.

**Annotation help:** I used Groq to generate the dataset since Reddit's API was unavailable. I gave it my label definitions and reviewed samples from each batch to make sure they actually matched what I was going for.

**Failure analysis:** After fine-tuning I looked at the wrong predictions to find patterns. 3 out of 4 errors were reaction posts getting misclassified — short posts with basketball slang or evaluative language the model read as a different label type.

---

## Stretch Features

- [ ] Simple interface that takes a new post, runs it through the classifier, and shows the label and confidence score