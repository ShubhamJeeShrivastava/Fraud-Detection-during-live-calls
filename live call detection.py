import pyaudio
import wave
import google.generativeai as genai
import streamlit as st
from time import sleep

# Configure the Generative AI API
genai.configure(api_key="ENTER YOUR API GEMINI API KEY") // i hidden my api key
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to record audio
def record_audio(output_path, record_seconds=5, rate=44100, chunk=1024, channels=1):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))

# Function to process audio with Gemini AI
def process_audio(audio_path, prompt):
    try:
        audio_file = genai.upload_file(path=audio_path)
        response = model.generate_content([prompt, audio_file])
        return response.text.strip().lower()
    except Exception as e:
        return f"error: {e}"

# Streamlit app
def main():
    st.title("Live Audio Analysis with Generative AI")
    st.write("Record an audio file, and the AI will classify it as 'Spam', 'Fraud', or 'Genuine'.")

    audio_path = "temp_audio.wav"
    complete_audio_path = "complete_audio.wav"
    all_frames = []
    accumulated_seconds = 0

    # Start button
    if st.button("Start Live Analysis"):
        st.write("🔴 Recording in progress... Speak now!")
        status_placeholder = st.empty()
        result_placeholder = st.empty()

        while True:  # Keep recording until manually stopped or 'spam'/'fraud' is detected
            # Record audio chunk
            record_audio(audio_path, record_seconds=5)

            # Append recorded chunk to the complete audio file
            with wave.open(audio_path, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                all_frames.append(frames)
            with wave.open(complete_audio_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(44100)
                wf.writeframes(b"".join(all_frames))

            # Generate prompt
            prompt = (
                "Classify the audio as 'spam', 'fraud', or 'genuine'. "
                'Respond with one word in double quotes (e.g., "fraud"), followed by a brief explanation.'
            )

            # Process audio
            result = process_audio(complete_audio_path, prompt)
            accumulated_seconds += 5
            status_placeholder.text(f"Total recording time: {accumulated_seconds} seconds.")

            # Check for result and stop if "spam" or "fraud" is detected
            if result:
                if "error" in result:
                    result_placeholder.error(result)
                else:
                    # Extract the one-word response in quotes
                    first_word = result.split('"')[1] if '"' in result else None
                    result_placeholder.markdown(f"### Analysis Result: {result}")
                    
                    if first_word in ["spam", "fraud"]:
                        st.error(f"🚨 DETECTED: {first_word.upper()}. Disconnect the call immediately!")
                        break  # Stop the analysis loop
            else:
                result_placeholder.error("Error processing the audio. Please try again.")

            # Pause for a moment before recording the next chunk
            sleep(1)

        st.success("Recording stopped automatically due to detection.")

    # Stop button to terminate the analysis manually
    if st.button("Stop Recording"):
        st.write("Recording manually stopped.")

if _name_ == "_main_":
    main()
