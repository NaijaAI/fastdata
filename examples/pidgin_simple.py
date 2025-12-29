"""
Simple Nigerian Pidgin generator using OpenRouter API directly.
Saves both valid and failed results locally.
"""

import argparse
import concurrent.futures
import itertools
import json
import os
import random
import re
import sys
import threading
import time
from pathlib import Path
from typing import Set

import requests
from pydantic import BaseModel

# =============================================================================
# GLOBAL
# =============================================================================

write_lock = threading.Lock()

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
    "current_events",
    "science_and_nature",
    "history_and_culture",
    "law_and_justice",
    "environment_and_climate",
    "business_and_economy",
    "youth_and_children",
    "women_and_gender",
    "mental_health",
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
    "article",
    "news_analysis",
    "lecture",
    "sermon",
    "speech",
    "opinion",
    "review",
    "announcement",
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

Requirements:
- Write 200-500 words in Pidgin only
- Make it natural like real Naija people talk
- Vary your sentence structure and opening words
- Don't start every sentence with "Ehen" or the same pattern
- Use different ways to begin sentences naturally

Return ONLY valid JSON:
{{
  "title": "short title in pidgin",
  "content": "the full text in pidgin (200-500 words)"
}}"""

    system_prompt = """You are a Nigerian Pidgin speaker. Write authentic, diverse Pidgin text.
Use common words: wetin, dey, na, abi, walahi.
Use exclamations naturally: Chei!, Haba!, Ehen! (but don't overuse them).
Vary your sentence openings - use different words and structures.
Stay in Pidgin only. No English sentences.
Write naturally, not formulaically."""

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
# PROGRESS TRACKING
# =============================================================================


def load_progress(output_dir: Path) -> Set[int]:
    """Load processed indices from progress file."""
    progress_file = output_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file) as f:
            data = json.load(f)
            return set(data.get("processed_indices", []))
    return set()


def save_progress(output_dir: Path, processed: Set[int], total: int):
    """Save processed indices to progress file."""
    progress_file = output_dir / "progress.json"
    with write_lock:
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "processed_indices": sorted(list(processed)),
                    "seed": 42,
                    "total": total,
                },
                f,
            )


def process_combo(
    index: int, combo: dict, api_key: str, output_file: Path, failed_file: Path
):
    """Worker function to process one combination."""
    result, error = generate_one(api_key, combo)

    with write_lock:
        if result:
            with open(output_file, "a") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        else:
            failed_entry = {"combo": combo, "error": error}
            with open(failed_file, "a") as f:
                f.write(json.dumps(failed_entry, ensure_ascii=False) + "\n")

    return index, bool(result)


# =============================================================================
# MAIN
# =============================================================================


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate Nigerian Pidgin synthetic data"
    )
    parser.add_argument(
        "--test", action="store_true", help="Generate 5 examples for testing"
    )
    parser.add_argument(
        "--workers", type=int, default=2, help="Number of parallel workers (default: 2)"
    )
    parser.add_argument(
        "--num",
        type=int,
        default=1000,
        help="Number of examples to generate (default: 1000)",
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Start fresh, ignore progress file"
    )
    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Setup output directory
    output_dir = Path("pidgin_data")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "data.jsonl"
    failed_file = output_dir / "failed.jsonl"

    # Generate all inputs
    all_inputs = generate_inputs()
    print(f"Total combinations: {len(all_inputs)}")

    # Load progress
    processed = set() if args.no_resume else load_progress(output_dir)
    if processed:
        print(f"Resuming: {len(processed)} already processed")

    # Clear files in test mode with no resume
    if args.test and args.no_resume:
        if output_file.exists():
            output_file.unlink()
        if failed_file.exists():
            failed_file.unlink()
        processed = set()

    # Get unprocessed indices
    unprocessed = [i for i in range(len(all_inputs)) if i not in processed]

    # Determine how many to process
    if args.test:
        to_process = unprocessed[:5]
    else:
        to_process = unprocessed[: args.num]

    if not to_process:
        print("No unprocessed combinations to generate!")
        return

    print(f"Generating {len(to_process)} examples with {args.workers} workers...\n")

    # Parallel execution
    valid_count = 0
    failed_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}

        # Submit tasks with rate limiting
        for idx in to_process:
            future = executor.submit(
                process_combo, idx, all_inputs[idx], api_key, output_file, failed_file
            )
            futures[future] = idx
            time.sleep(1.0 / args.workers)  # Stagger submissions

        # Process results as they complete
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            idx, success = future.result()
            processed.add(idx)
            save_progress(output_dir, processed, len(all_inputs))

            completed += 1
            if success:
                valid_count += 1
                status = "✓"
            else:
                failed_count += 1
                status = "✗"

            combo = all_inputs[idx]
            print(
                f"{status} {completed}/{len(to_process)}: {combo['topic']} - {combo['genre']}"
            )

    # Summary
    print(f"\n✅ Valid: {valid_count}/{len(to_process)}")
    print(f"❌ Failed: {failed_count}/{len(to_process)}")
    print(f"📁 Valid saved to: {output_file}")
    if failed_count > 0:
        print(f"📁 Failed saved to: {failed_file}")
    print(f"📊 Progress: {len(processed)}/{len(all_inputs)} total processed")

    # Show sample
    if valid_count > 0 and output_file.exists():
        with open(output_file) as f:
            first_line = f.readline()
        if first_line:
            sample = json.loads(first_line)
            print(f"\n📄 Sample output:")
            print(json.dumps(sample, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
