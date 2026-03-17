import os
import argparse
import tempfile
import subprocess
from tqdm import tqdm

# --- Import your formatting logic ---
from format_transcript import clean_transcript

# --- 1. Fix AMD & PyTorch Warnings via Environment Variables ---
# Enable experimental Flash Attention for ROCm to suppress the SDPA warning
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"
# Suppress the XNACK hardware warning specific to APUs
os.environ["HSA_XNACK"] = "1" 
# Tell PyTorch to manage memory fragmentation better (helps prevent OOM)
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

# Now we can import the heavy libraries
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
    """
    Bypasses the librosa audioread warning by using ffmpeg to silently 
    convert the file to a temporary .wav file, which librosa loads perfectly.
    """
    print(f"Extracting audio track from '{input_path}'...")
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    # Run ffmpeg to convert input to a mono, 24kHz wav file
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path, 
        "-ar", str(sr), "-ac", "1", temp_wav
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Load the clean wav file
    speech_array, sampling_rate = librosa.load(temp_wav, sr=sr)
    
    # Clean up the temporary file
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

    # Load audio cleanly without warnings
    speech_array, sampling_rate = load_audio_cleanly(input_path, sr=24000)

    # Instruct the model to specifically output the JSON format we need for the formatter
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
    # Process the audio in 300-second chunks to save VRAM
    chunk_duration_s = 300 
    chunk_size = chunk_duration_s * sampling_rate
    total_chunks = (len(speech_array) + chunk_size - 1) // chunk_size
    
    full_transcription = []

    print("\nStarting transcription process...")
    # Wrap the range in tqdm for a progress bar
    for i in tqdm(range(total_chunks), desc="Processing Audio Chunks", unit="chunk"):
        # Slice the audio array for this chunk
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(speech_array))
        chunk_audio = speech_array[start_idx:end_idx]

        # Prepare inputs
        inputs = processor.apply_transcription_request(
            audio=chunk_audio,
            sampling_rate=sampling_rate,
            prompt=prompt_text
        ).to(model.device, model.dtype)

        # Generate text
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=4096 # This fixes the max_length/max_new_tokens warning
            )

        # Decode and store
        chunk_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        full_transcription.append(chunk_text.strip())
        
        # Free up VRAM immediately after each chunk
        del inputs, output_ids
        torch.cuda.empty_cache()

    # Combine all chunks into the raw text
    final_text = " ".join(full_transcription)

    # --- INTEGRATED FORMATTING LOGIC ---
    print("\nApplying timestamps and formatting text...")
    
    # 1. Save the raw JSON output to a temporary file
    temp_raw = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8").name
    with open(temp_raw, "w", encoding="utf-8") as f:
        f.write(final_text)
        
    # 2. Feed the temporary file into the imported formatting function
    # It will read the temp file, process the JSON, and save the clean version to the requested output_path
    clean_transcript(temp_raw, output_path, milestone_interval=60)
    
    # 3. Clean up the temporary raw file
    os.remove(temp_raw)

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
