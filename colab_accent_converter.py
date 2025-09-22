import streamlit as st
import requests
import tempfile
import os
import subprocess
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

import uuid
import time


def process_audio_local(audio_file, gender):
    unique_id = str(uuid.uuid4())[:8]
    input_path = f"input_{unique_id}.wav"
    output_path = f"voice_{unique_id}.wav"
    
    with open(input_path, "wb") as f:
        f.write(audio_file)
    
    if gender.lower() == "female":
        model = "NikkiDorkDiaries.pth"
        idx = "added_IVF110_Flat_nprobe_1_NikkiDorkDiaries_v2.index"
    else:
        model = "AndyField_350e_5950s.pth"
        idx = "AndyField.index"
    
    try:
        result = subprocess.run([
            "python3", "tools/infer_cli.py",
            "--input_path", input_path,
            "--index_path", idx,
            "--f0method", "harvest",
            "--opt_path", output_path,
            "--model_name", model,
            "--index_rate", "0.7",
            "--device", "cuda:0",
            "--is_half", "False",
            "--filter_radius", "1",
            "--resample_sr", "44100",
            "--rms_mix_rate", "0.5",
            "--protect", "0.33",
            "--f0up_key", "0"
        ], capture_output=True, text=True, check=True)
        
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if not os.path.exists(output_path):
            raise Exception("Voice conversion failed - output not created")
        
        with open(output_path, "rb") as f:
            result_audio = f.read()
        
        if os.path.exists(output_path):
            os.remove(output_path)
            
        return result_audio
    
    except subprocess.CalledProcessError as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        raise Exception(f"RVC processing failed: {e.stderr}")
    
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        raise Exception(f"Processing error: {str(e)}")


def download_video(url, output_path):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        
        progress_bar = st.progress(0)
        status_text = st.empty()        
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = downloaded / total_size
                        progress_bar.progress(progress)
                        status_text.text(f"Downloaded: {downloaded / 1024 / 1024:.1f} MB")
    
    return output_path


def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "44100", "-ac", "2",
        audio_path, "-y"
    ], check=True, capture_output=True)
    return audio_path


def get_audio_duration(audio_path):
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", 
        "format=duration", "-of", "csv=p=0", audio_path
    ], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def split_audio_chunks(audio_path, chunk_duration=300):
    duration = get_audio_duration(audio_path)
    num_chunks = math.ceil(duration / chunk_duration)
    
    temp_dir = tempfile.mkdtemp()
    chunk_files = []
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        remaining_duration = duration - start_time
        current_chunk_duration = min(chunk_duration, remaining_duration)
        
        chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
        
        subprocess.run([
            "ffmpeg", "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(current_chunk_duration),
            "-af", "afftdn", 
            "-ar", "44100",
            "-ac", "2", 
            chunk_file, "-y"
        ], check=True, capture_output=True)
        
        chunk_files.append(chunk_file)
    
    return chunk_files


def combine_audio_chunks(processed_chunks, output_path):
    if not processed_chunks:
        return None
    
    if len(processed_chunks) == 1:
        subprocess.run([
            "ffmpeg", "-i", processed_chunks[0],
            "-c", "copy", output_path, "-y"
        ], check=True, capture_output=True)
    else:
        inputs = []
        filter_parts = []
        
        for i, chunk in enumerate(processed_chunks):
            inputs.extend(["-i", chunk])
            filter_parts.append(f"[{i}:0]")
        
        filter_complex = "".join(filter_parts) + f"concat=n={len(processed_chunks)}:v=0:a=1[out]"
        
        cmd = ["ffmpeg"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]", output_path, "-y"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    return output_path


def replace_video_audio(video_path, audio_path, output_path):
    subprocess.run([
        "ffmpeg", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0",
        "-map", "1:a:0", "-shortest", output_path, "-y"
    ], check=True, capture_output=True)
    return output_path


def main():
    st.set_page_config(page_title="Accent Changer")
    st.title("American Accent Converter")
    
    video_url = st.text_input("Enter download video url")
    voice_gender = st.radio("Select Voice Gender", ("Male", "Female"), index=0)
    
    if st.button("Submit"):
        if not video_url.strip():
            st.error("Please enter a valid video URL.")
        else:
            st.info(f"Selected voice: {voice_gender}")
            
            try:
                with st.spinner("Downloading video..."):
                    temp_dir = tempfile.mkdtemp()
                    video_path = os.path.join(temp_dir, "video.mp4")
                    download_video(video_url, video_path)
                
                with st.spinner("Extracting audio..."):
                    audio_path = os.path.join(temp_dir, "audio.wav")
                    extract_audio(video_path, audio_path)
                
                st.success("Audio extracted successfully!")
                
                with st.spinner("Creating audio chunks..."):
                    chunk_files = split_audio_chunks(audio_path)
                
                st.success(f"Created {len(chunk_files)} audio chunks")
                
                for i, chunk_file in enumerate(chunk_files):
                    chunk_size = os.path.getsize(chunk_file) / 1024 / 1024
                    duration = get_audio_duration(chunk_file)
                    st.write(f"Chunk {i+1}: {duration:.1f}s ({chunk_size:.1f} MB)")      
                
                processed_chunks = {}
                
                def process_chunk(i, chunk_file):
                    with open(chunk_file, "rb") as f:
                        audio_data = f.read()
                    
                    processed_audio = process_audio_local(audio_data, voice_gender)
                    
                    processed_chunk = os.path.join(temp_dir, f"processed_chunk_{i:03d}.wav")
                    with open(processed_chunk, "wb") as out_f:
                        out_f.write(processed_audio)
                    
                    return i, processed_chunk
                
                with st.spinner("Processing audio chunks..."):
                    max_workers = 4
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [executor.submit(process_chunk, i, chunk_file) for i, chunk_file in enumerate(chunk_files)]
                        for future in as_completed(futures):
                            try:
                                i, processed_file = future.result()
                                processed_chunks[i] = processed_file 
                                st.success(f"Chunk {i+1} processed successfully")
                            except Exception as e:
                                st.error(f"Failed to process chunk {i+1}: {e}")   
                
                if len(processed_chunks) == len(chunk_files):
                    with st.spinner("Combining processed audio..."):
                        final_audio_path = os.path.join(temp_dir, "final_audio.wav")
                        ordered_chunks = [processed_chunks[i] for i in sorted(processed_chunks.keys())]
                        combine_audio_chunks(ordered_chunks, final_audio_path)
                    
                    with st.spinner("Creating final video..."):
                        final_video_path = os.path.join(temp_dir, "final_video.mp4")
                        replace_video_audio(video_path, final_audio_path, final_video_path)
                    
                    with open(final_video_path, "rb") as f:
                        st.download_button(
                            label="Download Converted Video",
                            data=f.read(),
                            file_name="accent_converted_video.mp4",
                            mime="video/mp4"
                        )
                    
                    st.success("Video processing completed successfully!")
                else:
                    st.error("Some chunks failed to process. Cannot create final video.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
