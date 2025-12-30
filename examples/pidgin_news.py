"""
Nigerian Pidgin generator focused on formal/news content.
Uses expanded dimensions for 1M+ unique combinations.
Designed for cron job execution with timestamped outputs.
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
from datetime import datetime
from pathlib import Path
from typing import Set

import requests
from pydantic import BaseModel

# =============================================================================
# GLOBAL
# =============================================================================

write_lock = threading.Lock()
rate_limit_lock = threading.Lock()
last_request_time = 0
MIN_REQUEST_INTERVAL = 0.5  # Minimum 0.5 seconds between requests

# =============================================================================
# SCHEMA
# =============================================================================


class PidginText(BaseModel):
    title: str
    content: str


# =============================================================================
# DIMENSIONS (Expanded for 1M+ combinations)
# =============================================================================

# 40 formal/news topics
topics = [
    # Politics & Government
    "national_elections",
    "local_government",
    "international_relations",
    "policy_changes",
    "corruption_investigation",
    "parliamentary_debate",
    "presidential_address",
    "state_governance",
    # Economy & Business
    "stock_market",
    "currency_exchange",
    "banking_sector",
    "startup_ecosystem",
    "unemployment_rates",
    "inflation_impact",
    "trade_agreements",
    "oil_and_gas",
    # Technology & Innovation
    "fintech_developments",
    "telecommunications",
    "cybersecurity",
    "digital_transformation",
    "artificial_intelligence",
    "social_media_trends",
    # Education & Academia
    "university_research",
    "education_reform",
    "scholarship_programs",
    "academic_excellence",
    "vocational_training",
    # Health & Science
    "medical_breakthroughs",
    "public_health_crisis",
    "pharmaceutical_industry",
    "scientific_research",
    "healthcare_access",
    # Law & Justice
    "court_proceedings",
    "legal_reforms",
    "human_rights",
    "criminal_justice",
    # Environment & Climate
    "climate_change",
    "environmental_pollution",
    "renewable_energy",
    "natural_disasters",
]

# 15 formal genres
genres = [
    "news_report",
    "breaking_news",
    "investigative_article",
    "editorial_opinion",
    "expert_analysis",
    "feature_story",
    "press_conference",
    "public_lecture",
    "financial_report",
    "research_presentation",
    "policy_briefing",
    "market_update",
    "technical_explanation",
    "formal_announcement",
    "expert_interview",
]

# 12 formal settings
settings = [
    "newsroom",
    "government_house",
    "corporate_office",
    "university_lecture_hall",
    "research_institute",
    "television_studio",
    "radio_station",
    "conference_center",
    "stock_exchange",
    "law_court",
    "hospital_administration",
    "international_summit",
]

# 10 professional tones
tones = [
    "authoritative",
    "analytical",
    "investigative",
    "cautiously_optimistic",
    "critically_concerned",
    "balanced_objective",
    "urgently_informative",
    "professionally_skeptical",
    "pedagogically_clear",
    "diplomatically_firm",
]

# 15 professional speakers
speakers = [
    "news_anchor",
    "investigative_journalist",
    "economic_analyst",
    "political_commentator",
    "university_professor",
    "medical_expert",
    "legal_analyst",
    "business_correspondent",
    "technology_specialist",
    "environmental_scientist",
    "financial_advisor",
    "policy_expert",
    "senior_researcher",
    "industry_consultant",
    "government_spokesperson",
]

# 5 time contexts
time_periods = [
    "breaking_current",
    "recent_development",
    "ongoing_situation",
    "historical_context",
    "future_projection",
]

# 8 complexity levels (new dimension)
complexity_levels = [
    "executive_summary",
    "detailed_analysis",
    "technical_deep_dive",
    "comparative_review",
    "trend_analysis",
    "case_study",
    "data_driven_report",
    "expert_commentary",
]

# Total combinations: 40 × 15 × 12 × 10 × 15 × 5 × 8 = 4,320,000 combinations


# =============================================================================
# GENERATION
# =============================================================================


def is_valid_combo(combo):
    """Filter out nonsensical combinations."""
    topic, genre, setting, tone, speaker, time_period, complexity = combo

    # Breaking news shouldn't be historical
    if genre == "breaking_news" and time_period == "historical_context":
        return False

    # Future projections don't work with breaking news
    if genre == "breaking_news" and time_period == "future_projection":
        return False

    # Expert interviews need appropriate settings
    if genre == "expert_interview" and setting in ["stock_exchange", "newsroom"]:
        return False

    # Technical deep dives need expert speakers
    if complexity == "technical_deep_dive" and speaker in [
        "news_anchor",
        "business_correspondent",
    ]:
        return False

    return True


def generate_inputs(shuffle=True, seed=None):
    """Generate all valid input combinations."""
    all_combos = list(
        itertools.product(
            topics, genres, settings, tones, speakers, time_periods, complexity_levels
        )
    )

    valid = [c for c in all_combos if is_valid_combo(c)]

    if shuffle:
        if seed is None:
            # Use current date as seed for daily variation
            seed = int(datetime.now().strftime("%Y%m%d"))
        random.seed(seed)
        random.shuffle(valid)

    return [
        {
            "topic": c[0],
            "genre": c[1],
            "setting": c[2],
            "tone": c[3],
            "speaker": c[4],
            "time_period": c[5],
            "complexity": c[6],
        }
        for c in valid
    ]


def generate_one(api_key, combo,  lang="Pidgin", n_docs = 15,  use_exclamations="Chei!, Haba!, Ehen!", 
    common_words="wetin, dey, na, abi, walahi, omo, sey, fa"):
    """Generate one example. Returns (valid_dict, error) or (None, error)."""
    global last_request_time

    # Rate limiting: ensure minimum interval between requests
    with rate_limit_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
        last_request_time = time.time()

    prompt = f"""Write a {combo["genre"]} in Nigerian Pidgin about {combo["topic"]}.

Context:
- Setting: {combo["setting"]}
- Tone: {combo["tone"]}
- Speaker: {combo["speaker"]}
- Time frame: {combo["time_period"]}
- Complexity: {combo["complexity"]}

Requirements:
- Write {n_docs} unique text documents, each with 250-600 words in {lang} only (separated by a "</s>" tag)
- Maintain professional/formal style appropriate for {combo["genre"]}
- Use {lang} naturally but keep it informative and structured
- Include relevant details and context for the topic
- Vary sentence structure and opening patterns

Return ONLY valid JSON:
{{
  "title": "professional title in {lang}",
  "content": "the full text of {n_docs} unique documents in {lang} language (ranging from 250-500 words and separated by a `</s>` tag)"
}}"""

    system_prompt = f"""You are a professional Nigerian {lang} speaker covering formal/news content.
Write authentic Nigerian {lang} that is professional and informative.
Use common {lang} words naturally: {common_words}.
Keep the tone appropriate for news, lectures, or formal articles.
Be clear and structured while staying authentic to {lang}.
Avoid overly casual exclamations unless contextually appropriate.
Focus on delivering information clearly in natural {lang}.
Random seed: {random.choice(range(500_000_000))
}"""

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

        # Parse response and check for errors
        response_data = response.json()

        # Check if response contains error
        if "error" in response_data:
            error_msg = response_data["error"].get(
                "message", str(response_data["error"])
            )
            return None, f"API Error: {error_msg}"

        # Check if choices exist
        if "choices" not in response_data or not response_data["choices"]:
            return None, f"No choices in response: {response_data}"

        text = response_data["choices"][0]["message"]["content"]

        # Extract JSON
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
        else:
            json_str = text.strip()

        # Clean control characters
        json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", json_str)

        # Fix common invalid escape sequences by escaping backslashes
        # This handles cases like \s, \n in content that aren't valid JSON escapes
        # Only preserve valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        def fix_escapes(match):
            escaped = match.group(1)
            # Valid single-char escapes in JSON
            if escaped in ['"', "\\", "/", "b", "f", "n", "r", "t"]:
                return match.group(0)
            # Unicode escapes
            if escaped.startswith("u") and len(escaped) == 5:
                return match.group(0)
            # Invalid escape - escape the backslash
            return "\\\\" + escaped

        json_str = re.sub(r"\\(.)", fix_escapes, json_str)

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
    """Load successfully completed indices from progress file."""
    progress_file = output_dir / "progress.json"
    if progress_file.exists():
        with open(progress_file) as f:
            data = json.load(f)
            # Load successful indices (old files use "processed_indices" key)
            successful = set(
                data.get("successful_indices", data.get("processed_indices", []))
            )
            return successful
    return set()


def save_progress(output_dir: Path, successful: Set[int], total: int, seed: int):
    """Save successfully completed indices to progress file."""
    progress_file = output_dir / "progress.json"
    with write_lock:
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "successful_indices": sorted(list(successful)),
                    "seed": seed,
                    "total": total,
                    "successful_count": len(successful),
                },
                f,
            )


def process_combo(
    index: int, combo: dict, api_key: str, output_file: Path, failed_file: Path, lang="Pidgin", n_docs = 15,  use_exclamations="Chei!, Haba!, Ehen!", 
    common_words="wetin, dey, na, abi, walahi, omo, sey, fa"
):
    """Worker function to process one combination."""
    result, error = generate_one(api_key, combo, lang=lang, n_docs=n_docs, use_exclamations=use_exclamations, common_words=common_words)

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
        description="Generate formal Nigerian Pidgin synthetic data"
    )
    parser.add_argument(
        "--test", action="store_true", help="Generate 5 examples for testing"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of parallel workers (default: 1)"
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
    parser.add_argument(
        "--output-dir",
        type=str,
        default="pidgin_data/news",
        help="Output directory (default: pidgin_data/news)",
    )
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Use timestamped output filenames",
    )
    
    parser.add_argument(
        "--lang", type=str, default="Pidgin", help="Language to generate (default: Pidgin)"
    )
    parser.add_argument(
        "--n_docs", type=int, default=15, help="Number of documents to generate per request(default: 15)"
    )
    parser.add_argument(
        "--use_exclamations", type=str, default="Chei!, Haba!, Ehen!", help="Exclamations to use (default: Chei!, Haba!, Ehen!)"
    )
    parser.add_argument(
        "--common_words", type=str, default="wetin, dey, na, abi, walahi, omo, sey, fa", help="Common words to use (default: wetin, dey, na, abi, walahi, omo, sey, fa)"
    )
    
    
    args = parser.parse_args()
    
    lang = args.lang
    n_docs = args.n_docs
    use_exclamations = args.use_exclamations
    common_words = args.common_words

    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filenames if requested
    if args.timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = output_dir / f"data_{timestamp}.jsonl"
        failed_file = output_dir / f"failed_{timestamp}.jsonl"
    else:
        output_file = output_dir / "data.jsonl"
        failed_file = output_dir / "failed.jsonl"

    # Generate all inputs with daily seed
    seed = int(datetime.now().strftime("%Y%m%d"))
    all_inputs = generate_inputs(shuffle=True, seed=seed)
    print(f"Total valid combinations: {len(all_inputs):,}")
    print(f"Daily seed: {seed}")

    # Load progress (only if not using timestamp mode)
    if args.timestamp or args.no_resume:
        successful = set()
    else:
        successful = load_progress(output_dir)
        if successful:
            print(f"Resuming: {len(successful)} already successful")

    # Clear files in test mode with no resume
    if args.test and args.no_resume:
        if output_file.exists():
            output_file.unlink()
        if failed_file.exists():
            failed_file.unlink()
        successful = set()

    # Get unprocessed indices (anything not successfully completed)
    unprocessed = [i for i in range(len(all_inputs)) if i not in successful]

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
        # Submit all tasks
        future_to_idx = {}
        for idx in to_process:
            future = executor.submit(
                process_combo, idx, all_inputs[idx], api_key, output_file, failed_file, lang, n_docs, use_exclamations, common_words
            )
            future_to_idx[future] = idx

        print(
            f"Submitted {len(to_process)} tasks, processing with {args.workers} workers...\n"
        )

        # Process results as they complete
        completed = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            _, success = future.result()

            # Only add to successful set if generation succeeded
            if success:
                successful.add(idx)
                if not args.timestamp:  # Only save progress if not timestamped
                    save_progress(output_dir, successful, len(all_inputs), seed)

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
        print(f"💡 Failed combinations will be automatically retried on next run")
    if not args.timestamp:
        print(
            f"📊 Progress: {len(successful)}/{len(all_inputs):,} successfully completed"
        )

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
