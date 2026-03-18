import os
import argparse
import tempfile
import subprocess
from tqdm import tqdm

# --- Import your formatting logic ---
from format_transcript import clean_transcript

# --- 1. Fix AMD & PyTorch Warnings via Environment Variables ---
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"
os.environ["HSA_XNACK"] = "1" 
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

import torch
import librosa
from transformers import AutoProcessor, VibeVoiceAsrForConditionalGeneration

def check_amd_gpu():
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        print(f"✅ Success: AMD ROCm detected! Using GPU: {device_name}")
        return True
    else:
        print("⚠️ Warning: ROCm GPU not detected. PyTorch will fall back to CPU.")
        return False

def load_audio_cleanly(input_path, sr=24000):
    print(f"Extracting audio track from '{input_path}'...")
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path, 
        "-ar", str(sr), "-ac", "1", temp_wav
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    speech_array, sampling_rate = librosa.load(temp_wav, sr=sr)
    os.remove(temp_wav)
    return speech_array, sampling_rate

def process_audio(input_path, output_path, in_lang, out_lang):
    check_amd_gpu()

    model_id = "microsoft/VibeVoice-ASR-HF"
    print("Loading processor and VibeVoice model...")
    processor = AutoProcessor.from_pretrained(model_id)
    
    model = VibeVoiceAsrForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.float16 
    )

    speech_array, sampling_rate = load_audio_cleanly(input_path, sr=24000)

    if in_lang or out_lang:
        source_lang = in_lang if in_lang else "its original language"
        target_lang = out_lang if out_lang else "its original language"
        prompt_text = (
            f"Please translate the following audio from {source_lang} to {target_lang}. "
            "Output the full translation word-for-word without summarizing. "
            "Please transcribe it with these keys: Start, End, Speaker, Content in JSON format."
        )
    else:
        prompt_text = "Please transcribe the audio and output it with these keys: Start, End, Speaker, Content in JSON format."

    # --- CHUNKING LOGIC ---
    chunk_duration_s = 600 # 10 minutes
    chunk_size = chunk_duration_s * sampling_rate
    total_chunks = (len(speech_array) + chunk_size - 1) // chunk_size
    
    full_transcription = []

    print("\nStarting transcription process...")
    for i in tqdm(range(total_chunks), desc="Processing Audio Chunks", unit="chunk"):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(speech_array))
        chunk_audio = speech_array[start_idx:end_idx]

        inputs = processor.apply_transcription_request(
            audio=chunk_audio,
            sampling_rate=sampling_rate,
            prompt=prompt_text
        ).to(model.device, model.dtype)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=4096, 
                max_length=None
            )

        chunk_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        full_transcription.append(chunk_text.strip())
        
        del inputs, output_ids
        torch.cuda.empty_cache()

    final_text = " ".join(full_transcription)

    # --- INTEGRATED FORMATTING LOGIC WITH PERMANENT BACKUP ---
    print("\nApplying timestamps and formatting text...")
    
    # 1. Create a permanent raw backup based on the requested output name
    base_name = os.path.splitext(output_path)[0]
    raw_backup_path = f"{base_name}_RAW_BACKUP.txt"
    
    with open(raw_backup_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    
    print(f"💾 Raw AI output permanently backed up to: {os.path.abspath(raw_backup_path)}")
        
    # 2. Feed the permanent file into the formatting function
    # Now, if this fails, you STILL have the RAW_BACKUP.txt file on your hard drive!
    clean_transcript(raw_backup_path, output_path, milestone_interval=60, chunk_duration_s=chunk_duration_s)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe or translate an audio/video file using VibeVoice.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output .txt file")
    parser.add_argument("-il", "--inlang", help="Input language (optional)")
    parser.add_argument("-ol", "--outlang", help="Output language (optional)")
    
    args = parser.parse_args()
    
    if not args.output.lower().endswith(".txt"):
        args.output += ".txt"
        
    process_audio(args.input, args.output, args.inlang, args.outlang)
