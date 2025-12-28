"""
Simple Nigerian Pidgin generator using OpenRouter API directly.
Saves both valid and failed results locally.
"""

import itertools
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import requests
from pydantic import BaseModel

# =============================================================================
# SCHEMA
# =============================================================================


class PidginText(BaseModel):
    title: str
    content: str


# =============================================================================
# DIMENSIONS
# =============================================================================

topics = [
    "family_and_home",
    "market_and_trading",
    "health_and_wellness",
    "food_and_cooking",
    "religion_and_faith",
    "work_and_hustle",
    "love_and_relationships",
    "education_and_school",
    "transport_and_travel",
    "entertainment",
    "community_and_neighbors",
    "technology_and_phones",
    "politics_and_government",
    "weather_and_farming",
    "celebrations_and_events",
    "sports_and_games",
    "money_and_finance",
    "housing_and_rent",
    "police_and_security",
    "marriage_and_weddings",
    "death_and_funerals",
]

genres = [
    "story",
    "dialogue",
    "monologue",
    "instructions",
    "news_report",
    "letter",
    "folklore",
    "life_advice",
    "complaint",
    "praise",
    "gossip",
    "testimony",
]

settings = [
    "lagos_urban",
    "village_rural",
    "market",
    "church_mosque",
    "workplace",
    "home",
    "street",
    "busstop",
    "hospital",
    "school",
]

tones = [
    "happy_excited",
    "sad_reflective",
    "angry_frustrated",
    "funny_playful",
    "serious_urgent",
    "hopeful_inspiring",
    "worried_anxious",
    "proud_boastful",
    "confused_uncertain",
]

speakers = [
    "elder_wise",
    "young_adult",
    "parent",
    "trader_business",
    "community_member",
    "child",
    "teacher",
    "pastor_imam",
    "girlfriend_boyfriend",
    "neighbor",
]

time_periods = ["present_day", "past_memory", "future_hopes"]


# =============================================================================
# GENERATION
# =============================================================================


def is_valid_combo(combo):
    topic, genre, setting, tone, speaker, time_period = combo

    if genre == "folklore" and time_period == "future_hopes":
        return False
    if genre == "news_report" and time_period == "past_memory":
        return False
    if genre == "instructions" and time_period == "past_memory":
        return False

    return True


def generate_inputs(shuffle=True):
    all_combos = list(
        itertools.product(topics, genres, settings, tones, speakers, time_periods)
    )

    valid = [c for c in all_combos if is_valid_combo(c)]

    if shuffle:
        random.seed(42)
        random.shuffle(valid)

    return [
        {
            "topic": c[0],
            "genre": c[1],
            "setting": c[2],
            "tone": c[3],
            "speaker": c[4],
            "time_period": c[5],
        }
        for c in valid
    ]


def generate_one(api_key, combo):
    """Generate one example. Returns (valid_dict, error) or (None, error)."""

    prompt = f"""Write a {combo["genre"]} in Nigerian Pidgin about {combo["topic"]}.
Setting: {combo["setting"]}
Tone: {combo["tone"]}
Speaker: {combo["speaker"]}
Time: {combo["time_period"]}

Write 200-500 words in Pidgin only.
Make it natural like real Naija people talk.

Return ONLY valid JSON:
{{
  "title": "short title in pidgin",
  "content": "the full text in pidgin (200-500 words)"
}}"""

    system_prompt = """You are a Nigerian Pidgin speaker. Write authentic Pidgin text.
Use common words: wetin, dey, na, abi, walahi.
Use exclamations: Chei!, Haba!, Ehen!
Stay in Pidgin only. No English sentences."""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )

        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]

        # Extract JSON
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text.strip()

        # Clean control characters
        json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", json_str)

        # Parse and validate
        data = json.loads(json_str)
        result = PidginText.model_validate(data)
        return result.model_dump(), None

    except Exception as e:
        return None, str(e)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Setup
    inputs = generate_inputs()
    print(f"Total combinations: {len(inputs)}")

    # How many to generate
    num = 5 if "--test" in sys.argv else 1000
    print(f"Generating {num} examples...\n")

    # Output dir
    output_dir = Path("pidgin_data")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "data.jsonl"
    failed_file = output_dir / "failed.jsonl"

    # Clear files in test mode
    if "--test" in sys.argv:
        if output_file.exists():
            output_file.unlink()
        if failed_file.exists():
            failed_file.unlink()

    # Generate
    valid_count = 0
    failed_count = 0

    for i, combo in enumerate(inputs[:num], 1):
        print(f"{i}/{num}: {combo['topic']} - {combo['genre']}")

        result, error = generate_one(api_key, combo)

        if result:
            valid_count += 1
            with open(output_file, "a") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"  ✓ Success")
        else:
            failed_count += 1
            failed_entry = {"combo": combo, "error": error}
            with open(failed_file, "a") as f:
                f.write(json.dumps(failed_entry, ensure_ascii=False) + "\n")
            print(f"  ✗ Failed: {error[:50]}")

        # Rate limit
        time.sleep(1)

    print(f"\n✅ Valid: {valid_count}/{num}")
    print(f"❌ Failed: {failed_count}/{num}")
    print(f"📁 Valid saved to: {output_file}")
    if failed_count > 0:
        print(f"📁 Failed saved to: {failed_file}")

    # Show sample
    if valid_count > 0:
        with open(output_file) as f:
            first_line = f.readline()
        sample = json.loads(first_line)
        print(f"\n📄 Sample output:")
        print(json.dumps(sample, indent=2, ensure_ascii=False))
