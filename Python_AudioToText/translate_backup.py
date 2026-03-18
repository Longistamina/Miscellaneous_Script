import json
import re
import os
from deep_translator import GoogleTranslator

def format_time(seconds):
    """Converts raw seconds into MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def translate_and_format(input_path, output_path, target_lang='en', milestone_interval=60, chunk_duration_s=900):
    print(f"Reading raw Korean backup from '{input_path}'...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    json_blocks = re.findall(r'\[\s*\{.*?\}\s*\]', content, flags=re.DOTALL)
    
    if not json_blocks:
        print("Error: Could not find any valid JSON blocks in the file.")
        return

    print(f"Found {len(json_blocks)} audio chunks. Translating to English... (This will take a few seconds)")

    # Initialize the free Google Translator API
    translator = GoogleTranslator(source='auto', target=target_lang)
    all_dialogue = []
    
    for chunk_index, block in enumerate(json_blocks):
        try:
            data = json.loads(block, strict=False)
            for item in data:
                global_start = item["Start"] + (chunk_index * chunk_duration_s)
                korean_text = item.get("Content", "").strip()
                
                # --- TRANSLATION HAPPENS HERE ---
                if korean_text:
                    try:
                        # Translate the Korean sentence to English
                        english_text = translator.translate(korean_text)
                    except Exception as e:
                        print(f"Warning: API error on a line, keeping original: {e}")
                        english_text = korean_text 
                else:
                    english_text = ""
                
                all_dialogue.append({
                    "Start": global_start,
                    "Speaker": item.get("Speaker", "0"),
                    "Content": english_text
                })
        except json.JSONDecodeError as e:
            print(f"Warning: Skipped a chunk due to parsing error: {e}")

    print("Applying clean formatting...")
    with open(output_path, 'w', encoding='utf-8') as f:
        current_milestone = -1
        current_speaker = None

        for item in all_dialogue:
            start_time = item["Start"]
            speaker = item["Speaker"]
            text = item["Content"]

            milestone_idx = int(start_time // milestone_interval)

            if milestone_idx > current_milestone:
                start_m = milestone_idx * milestone_interval
                end_m = start_m + milestone_interval
                
                if current_milestone != -1:
                    f.write("\n\n") 
                    
                f.write(f"--- Time Milestone: {format_time(start_m)} to {format_time(end_m)} ---\n")
                current_milestone = milestone_idx
                current_speaker = None 

            if speaker != current_speaker:
                if current_speaker is not None:
                    f.write("\n") 
                f.write(f"Speaker {speaker}: {text}")
                current_speaker = speaker
            else:
                f.write(f" {text}")
        
        f.write("\n")
            
    print(f"✅ Finished! Translated English transcript saved to: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    # Point this to your RAW backup file
    input_file = "ENG_note_RAW_BACKUP.txt"
    # Name your final beautiful English output
    output_file = "Clean_English_Transcript.txt"
    
    # Process it!
    translate_and_format(input_file, output_file, target_lang='en', milestone_interval=60, chunk_duration_s=900)
