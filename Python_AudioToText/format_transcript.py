import json
import re
import os

def format_time(seconds):
    """Converts raw seconds into MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def clean_transcript(input_path, output_path, milestone_interval=60):
    print(f"Reading '{input_path}'...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Find all independent JSON arrays in the file
    json_blocks = re.findall(r'\[\s*\{.*?\}\s*\]', content, flags=re.DOTALL)
    
    if not json_blocks:
        print("Error: Could not find any valid JSON blocks in the file.")
        return

    print(f"Found {len(json_blocks)} audio chunks. Processing and stitching times...")

    all_dialogue = []
    
    # 2. Parse each chunk and adjust the global timestamps
    for chunk_index, block in enumerate(json_blocks):
        try:
            data = json.loads(block)
            for item in data:
                global_start = item["Start"] + (chunk_index * 600)
                
                all_dialogue.append({
                    "Start": global_start,
                    "Speaker": item.get("Speaker", "0"),
                    "Content": item.get("Content", "").strip() # Strip extra whitespace just in case
                })
        except json.JSONDecodeError as e:
            print(f"Warning: Skipped a chunk due to parsing error: {e}")

    # 3. Format and write to the new file
    print("Formatting into readable text...")
    with open(output_path, 'w', encoding='utf-8') as f:
        current_milestone = -1
        current_speaker = None

        for item in all_dialogue:
            start_time = item["Start"]
            speaker = item["Speaker"]
            text = item["Content"]

            # Calculate which time chunk this belongs to
            milestone_idx = int(start_time // milestone_interval)

            # If we enter a new time chunk, print the Milestone Header
            if milestone_idx > current_milestone:
                start_m = milestone_idx * milestone_interval
                end_m = start_m + milestone_interval
                
                # Add a blank line between sections for readability
                if current_milestone != -1:
                    f.write("\n\n") 
                    
                f.write(f"--- Time Milestone: {format_time(start_m)} to {format_time(end_m)} ---\n")
                current_milestone = milestone_idx
                
                # Reset the current speaker so we print their name again after the time jump
                current_speaker = None 

            # Check if the speaker is the same as the last line
            if speaker != current_speaker:
                # If it's a new speaker, start a new line
                if current_speaker is not None:
                    f.write("\n") 
                f.write(f"Speaker {speaker}: {text}")
                current_speaker = speaker
            else:
                # Same speaker continuing their thought, just append with a space
                f.write(f" {text}")
        
        # Add a final newline at the end of the document
        f.write("\n")
            
    print(f"✅ Finished! Clean transcript saved to: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    # Point this to your uploaded file or use via import
    input_file = "ENG_note.txt"
    output_file = "Clean_Transcript.txt"
    
    clean_transcript(input_file, output_file, milestone_interval=60)
