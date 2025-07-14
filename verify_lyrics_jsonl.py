#verify_lyrics_jsonl.py
import json
import os
import re
import uuid

# Define allowed structure tags and their properties
VOCAL_SEGMENTS = {"[verse]", "[chorus]", "[bridge]"}
NON_VOCAL_SEGMENTS = {
    "[intro-short]", "[intro-medium]", 
    "[inst-short]", "[inst-medium]", 
    "[outro-short]", "[outro-medium]"
}
ALL_SEGMENTS = VOCAL_SEGMENTS | NON_VOCAL_SEGMENTS
FORBIDDEN_TAGS = {"[inst]"}  # Discouraged due to instability

# Valid auto_prompt_audio_type values
VALID_GENRES = [
    "Pop", "R&B", "Dance", "Jazz", "Folk", "Rock",
    "Chinese Style", "Chinese Tradition", "Metal", 
    "Reggae", "Chinese Opera", "Auto"
]

# Default placeholder lyrics for auto-correction
PLACEHOLDER_LYRICS = "[verse] Placeholder lyric one. Placeholder lyric two"

def validate_and_correct_jsonl_file(jsonl_path, output_path=None):
    """
    Validate and auto-correct a JSONL file for song generation prompts.
    Ensures mutual exclusivity of prompt_audio_path and auto_prompt_audio_type.
    Saves corrected JSONL to output_path or 'corrected_<jsonl_path>'.
    Returns True if valid or fully corrected, False if manual fixes are needed.
    Prints errors, warnings, corrections, and suggestions.
    """
    errors = []
    warnings = []
    corrections = []
    suggestions = []
    corrected_entries = []
    manual_fix_needed = False
    
    if not output_path:
        output_path = f"corrected_{jsonl_path}"
    
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                entry = {}
                try:
                    # Parse JSON line
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    errors.append(f"Line {line_num}: Invalid JSON format")
                    suggestions.append(f"Line {line_num}: Ensure the line is valid JSON (e.g., check quotes, commas)")
                    manual_fix_needed = True
                    continue
                
                # Initialize corrected entry
                corrected_entry = entry.copy()
                
                # Validate idx (required)
                if "idx" not in entry:
                    errors.append(f"Line {line_num}: Missing 'idx' field in JSON object")
                    new_idx = f"song_{line_num}_{uuid.uuid4().hex[:8]}"
                    corrected_entry["idx"] = new_idx
                    corrections.append(f"Line {line_num}: Added missing 'idx' as '{new_idx}'")
                elif not isinstance(entry["idx"], str) or not entry["idx"].strip():
                    errors.append(f"Line {line_num}: 'idx' must be a non-empty string")
                    new_idx = f"song_{line_num}_{uuid.uuid4().hex[:8]}"
                    corrected_entry["idx"] = new_idx
                    corrections.append(f"Line {line_num}: Replaced invalid 'idx' with '{new_idx}'")
                
                # Validate mutual exclusivity of prompt_audio_path and auto_prompt_audio_type
                if "prompt_audio_path" in entry and "auto_prompt_audio_type" in entry:
                    errors.append(
                        f"Line {line_num}: 'prompt_audio_path' and 'auto_prompt_audio_type' cannot be used together"
                    )
                    corrections.append(
                        f"Line {line_num}: Removed 'auto_prompt_audio_type' to enforce mutual exclusivity with 'prompt_audio_path'"
                    )
                    del corrected_entry["auto_prompt_audio_type"]
                
                # Validate prompt_audio_path (optional)
                if "prompt_audio_path" in entry:
                    audio_path = entry["prompt_audio_path"]
                    if not isinstance(audio_path, str):
                        errors.append(f"Line {line_num}: 'prompt_audio_path' must be a string")
                        corrections.append(f"Line {line_num}: Removed invalid 'prompt_audio_path'")
                        del corrected_entry["prompt_audio_path"]
                    elif not audio_path.endswith(".flac"):
                        errors.append(f"Line {line_num}: 'prompt_audio_path' must be a .flac file")
                        corrections.append(f"Line {line_num}: Removed invalid 'prompt_audio_path' (not .flac)")
                        del corrected_entry["prompt_audio_path"]
                    elif not os.path.isfile(audio_path):
                        errors.append(f"Line {line_num}: 'prompt_audio_path' file '{audio_path}' does not exist")
                        suggestions.append(
                            f"Line {line_num}: Provide a valid .flac file for 'prompt_audio_path', "
                            "e.g., '/workspace/SongGeneration/jsonl/vocal_sample.flac'"
                        )
                        corrections.append(f"Line {line_num}: Removed invalid 'prompt_audio_path' (file not found)")
                        del corrected_entry["prompt_audio_path"]
                
                # Validate auto_prompt_audio_type (optional, only if prompt_audio_path is absent)
                if "auto_prompt_audio_type" in entry and "prompt_audio_path" not in corrected_entry:
                    genre = entry["auto_prompt_audio_type"]
                    if genre not in VALID_GENRES:
                        errors.append(
                            f"Line {line_num}: Invalid 'auto_prompt_audio_type' '{genre}'. "
                            f"Allowed genres: {', '.join(VALID_GENRES)}"
                        )
                        corrected_entry["auto_prompt_audio_type"] = "Pop"
                        corrections.append(f"Line {line_num}: Replaced invalid 'auto_prompt_audio_type' '{genre}' with 'Pop'")
                
                # Validate gt_lyric (required)
                if "gt_lyric" not in entry:
                    errors.append(f"Line {line_num}: Missing 'gt_lyric' field in JSON object")
                    corrected_entry["gt_lyric"] = PLACEHOLDER_LYRICS
                    corrections.append(f"Line {line_num}: Added placeholder lyrics to 'gt_lyric'")
                    manual_fix_needed = True
                else:
                    lyrics = entry["gt_lyric"].strip()
                    if not lyrics:
                        errors.append(f"Line {line_num}: 'gt_lyric' is empty")
                        corrected_entry["gt_lyric"] = PLACEHOLDER_LYRICS
                        corrections.append(f"Line {line_num}: Replaced empty 'gt_lyric' with placeholder lyrics")
                        manual_fix_needed = True
                        lyrics = PLACEHOLDER_LYRICS
                    
                    # Split lyrics into segments by semicolon
                    segments = [s.strip() for s in lyrics.split(";") if s.strip()]
                    if not segments:
                        errors.append(f"Line {line_num}: No segments found in 'gt_lyric'")
                        corrected_entry["gt_lyric"] = PLACEHOLDER_LYRICS
                        corrections.append(f"Line {line_num}: Replaced empty segments with placeholder lyrics")
                        segments = [PLACEHOLDER_LYRICS]
                        manual_fix_needed = True
                    
                    corrected_segments = []
                    has_vocal_segment = False
                    for seg_num, segment in enumerate(segments, 1):
                        # Extract the structure tag
                        match = re.match(r"(\[.*?\])\s*(.*)", segment, re.DOTALL)
                        if not match:
                            errors.append(f"Line {line_num}, Segment {seg_num}: Segment does not start with a structure tag")
                            corrected_segments.append("[verse] Placeholder lyric one. Placeholder lyric two")
                            corrections.append(f"Line {line_num}, Segment {seg_num}: Replaced invalid segment with '[verse]' and placeholder lyrics")
                            has_vocal_segment = True
                            manual_fix_needed = True
                            continue
                        
                        tag, content = match.groups()
                        tag = tag.strip()
                        content = content.strip()
                        
                        # Check for forbidden or invalid tags
                        if tag in FORBIDDEN_TAGS:
                            errors.append(f"Line {line_num}, Segment {seg_num}: Forbidden tag '{tag}' used (unstable)")
                            new_tag = "[verse]" if content else "[inst-medium]"
                            corrections.append(f"Line {line_num}, Segment {seg_num}: Replaced forbidden tag '{tag}' with '{new_tag}'")
                            tag = new_tag
                        elif tag not in ALL_SEGMENTS:
                            errors.append(
                                f"Line {line_num}, Segment {seg_num}: Invalid structure tag '{tag}'. "
                                f"Allowed tags: {', '.join(ALL_SEGMENTS)}"
                            )
                            new_tag = "[verse]" if content else "[intro-medium]"
                            corrections.append(f"Line {line_num}, Segment {seg_num}: Replaced invalid tag '{tag}' with '{new_tag}'")
                            tag = new_tag
                        
                        # Validate vocal/non-vocal segments
                        if tag in VOCAL_SEGMENTS:
                            if not content:
                                errors.append(
                                    f"Line {line_num}, Segment {seg_num}: Vocal segment '{tag}' "
                                    "must contain at least one lyric sentence"
                                )
                                suggestions.append(
                                    f"Line {line_num}, Segment {seg_num}: Add at least one lyric sentence to '{tag}', "
                                    "e.g., 'Sample lyric one. Sample lyric two'"
                                )
                                content = "Placeholder lyric one. Placeholder lyric two"
                                corrections.append(
                                    f"Line {line_num}, Segment {seg_num}: Added placeholder lyrics to empty '{tag}'"
                                )
                                manual_fix_needed = True
                            else:
                                has_vocal_segment = True
                                # Check lyric sentences (must be separated by periods)
                                sentences = [s.strip() for s in content.split(".") if s.strip()]
                                if not sentences:
                                    errors.append(
                                        f"Line {line_num}, Segment {seg_num}: Vocal segment '{tag}' "
                                        "must contain valid lyric sentences separated by periods"
                                    )
                                    suggestions.append(
                                        f"Line {line_num}, Segment {seg_num}: Add valid lyric sentences to '{tag}', "
                                        "e.g., 'Sample lyric one. Sample lyric two'"
                                    )
                                    content = "Placeholder lyric one. Placeholder lyric two"
                                    corrections.append(
                                        f"Line {line_num}, Segment {seg_num}: Replaced invalid lyrics with placeholder lyrics"
                                    )
                                    manual_fix_needed = True
                                else:
                                    # Warn about other punctuation
                                    corrected_sentences = []
                                    for sentence in sentences:
                                        if re.search(r"[,!?;]", sentence):
                                            warnings.append(
                                                f"Line {line_num}, Segment {seg_num}: "
                                                f"Unsupported punctuation in lyric sentence '{sentence}'. "
                                                "Only periods are allowed between sentences"
                                            )
                                            cleaned_sentence = re.sub(r"[,!?;]", "", sentence).strip()
                                            corrections.append(
                                                f"Line {line_num}, Segment {seg_num}: "
                                                f"Removed unsupported punctuation from '{sentence}' to '{cleaned_sentence}'"
                                            )
                                            sentence = cleaned_sentence
                                        corrected_sentences.append(sentence)
                                    content = ". ".join(corrected_sentences)
                        elif tag in NON_VOCAL_SEGMENTS:
                            if content:
                                errors.append(
                                    f"Line {line_num}, Segment {seg_num}: Non-vocal segment '{tag}' "
                                    "must not contain lyrics"
                                )
                                corrections.append(
                                    f"Line {line_num}, Segment {seg_num}: Removed lyrics from non-vocal segment '{tag}'"
                                )
                                content = ""
                        
                        corrected_segments.append(f"{tag} {content}".strip())
                    
                    # Check for at least one vocal segment
                    if not has_vocal_segment:
                        errors.append(
                            f"Line {line_num}: Lyrics must contain at least one vocal segment: "
                            f"{', '.join(VOCAL_SEGMENTS)}"
                        )
                        suggestions.append(
                            f"Line {line_num}: Add a vocal segment (e.g., [verse]) with lyrics, "
                            f"e.g., '[verse] Sample lyric one. Sample lyric two'"
                        )
                        corrected_segments.append("[verse] Placeholder lyric one. Placeholder lyric two")
                        corrections.append(f"Line {line_num}: Added '[verse]' with placeholder lyrics due to missing vocal segment")
                        manual_fix_needed = True
                    
                    # Join corrected segments with semicolons
                    corrected_entry["gt_lyric"] = "; ".join(corrected_segments)
                
                # Validate descriptions (optional)
                if "descriptions" in entry:
                    if not isinstance(entry["descriptions"], str) or not entry["descriptions"].strip():
                        errors.append(f"Line {line_num}: 'descriptions' must be a non-empty string")
                        corrections.append(f"Line {line_num}: Removed invalid 'descriptions'")
                        del corrected_entry["descriptions"]
                    else:
                        # Check for comma-separated attributes
                        attributes = [a.strip() for a in entry["descriptions"].split(",") if a.strip()]
                        if not attributes:
                            errors.append(f"Line {line_num}: 'descriptions' must contain at least one attribute")
                            corrections.append(f"Line {line_num}: Removed empty 'descriptions'")
                            del corrected_entry["descriptions"]
                        else:
                            # Warn about unrecognized attributes
                            for attr in attributes:
                                if not re.match(r"^(male|female|[a-z\s]+|the bpm is \d+)$", attr, re.IGNORECASE):
                                    warnings.append(
                                        f"Line {line_num}: Unrecognized attribute '{attr}' in 'descriptions'. "
                                        "Recommended: gender (male, female), timbre (dark, bright), genre (pop, jazz), "
                                        "emotion (sad, energetic), instrument (piano, drums), BPM (the bpm is 120)"
                                    )
                
                corrected_entries.append(corrected_entry)
                
        # Save corrected JSONL
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in corrected_entries:
                json.dump(entry, f)
                f.write("\n")
        
        # Print feedback
        if errors:
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if corrections:
            print("Corrections applied:")
            for correction in corrections:
                print(f"  - {correction}")
        if suggestions:
            print("Suggestions for manual fixes:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        
        if not errors and not warnings:
            print(f"Validation successful: No errors or warnings found in '{jsonl_path}'")
        elif not manual_fix_needed:
            print(f"Validation completed: All errors were auto-corrected. Corrected file saved to '{output_path}'")
        else:
            print(
                f"Validation completed: Some errors were auto-corrected, but manual fixes are needed. "
                f"Partially corrected file saved to '{output_path}'"
            )
        
        return not manual_fix_needed
    
    except FileNotFoundError:
        print(f"Error: File '{jsonl_path}' not found")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python verify_lyrics_jsonl.py <path_to_jsonl_file> [output_path]")
        sys.exit(1)
    
    jsonl_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    is_valid = validate_and_correct_jsonl_file(jsonl_path, output_path)
    
    if is_valid:
        print("JSONL file is valid or was fully corrected for song generation")
        sys.exit(0)
    else:
        print("JSONL file contains errors requiring manual fixes")
        sys.exit(1)

if __name__ == "__main__":
    main()