#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pyaudio
import wave
import google.generativeai as genai
import os


# In[2]:


# Configure the Generative AI API
genai.configure(api_key="AIzaSyDxzKd3HW4exjDgecSqGUUDHbmYkLRYTcQ")
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to record audio in real-time for a given duration
def record_audio(output_path, record_seconds=10, rate=44100, chunk=1024, channels=1):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    print(f"Recording for {record_seconds} seconds...")
    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))

# Function to process audio and generate a response from Gemini AI
def process_audio(audio_path, prompt):
    try:
        # Upload the audio file for processing
        audio_file = genai.upload_file(path=audio_path)
        # Generate the classification and explanation
        response = model.generate_content([prompt, audio_file])
        return response.text.strip().lower()  # Return the classification result (spam, fraud, genuine)
    except Exception as e:
        print(f"Error processing audio: {e}")
        return None

# Function to perform live analysis
def live_analysis():
    audio_path = "live_audio.wav"
    complete_audio_path = "complete_audio.wav"
    all_frames = []
    record_seconds = 5
    accumulated_seconds = 0

    while True:
        # Record 5 seconds of audio
        record_audio(audio_path, record_seconds)
        
        # Append the recorded audio to the complete audio file
        with wave.open(audio_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            all_frames.append(frames)
        
        # Save the complete audio so far
        with wave.open(complete_audio_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(44100)
            wf.writeframes(b"".join(all_frames))
        
        # Generate prompt with request for one-word response
        prompt = (
            "Classify the audio as 'spam', 'fraud', or 'genuine'."
        )

        # Get response from the model
        result = process_audio(complete_audio_path, prompt)

        if result:
            print(f"\nAnalysis Result: {result}")
            if result in ["fraud", "spam"]:
                print("\nSuspicious activity detected! Immediate action needed.")
                break  # Exit the loop if fraud or spam is detected

        # Increase the accumulated recording time
        accumulated_seconds += record_seconds
        print(f"Total recording time: {accumulated_seconds} seconds.")

# Start live analysis
live_analysis()

