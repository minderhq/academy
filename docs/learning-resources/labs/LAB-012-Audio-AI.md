---
Document ID: LAB-012
Title: "LAB-012: Audio AI"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 7 hours
Tags: ['lab', 'audio', 'whisper', 'hands-on']
---

# LAB-012: Audio AI

**Speech Recognition, Synthesis, and Voice Systems**

---

## Lab Overview

**Time:** 4-5 hours
**Difficulty:** ⭐⭐⭐ Advanced
**Prerequisites:**
- LAB-002: RAG Implementation
- LAB-004: ReAct Agent
- Basic understanding of audio processing

**Learning Objectives:**
- Master Whisper speech recognition
- Implement text-to-speech synthesis
- Build voice-enabled AI assistants
- Process and analyze audio data
- Create multi-modal audio+text systems
- Deploy voice applications in production

---

## What You'll Build

By the end of this lab, you will have:

1. **Speech Recognition System** - Transcribe audio with Whisper
2. **Voice Synthesis** - Generate natural speech with TTS
3. **Voice Assistant** - Conversational AI with voice I/O
4. **Audio Analysis Tools** - Extract insights from audio
5. **Production Voice API** - Deployed with Docker

---

## Part 1: Whisper Speech Recognition (90 minutes)

### Understanding Whisper

Whisper is OpenAI's speech recognition system trained on 680,000 hours of multilingual data. It achieves state-of-the-art accuracy on speech recognition and translation.

```python
# File: whisper_system.py
"""
Whisper Speech Recognition System
==================================

Whisper Architecture:
- Encoder-decoder transformer
- Trained on massive multilingual dataset
- Supports transcription and translation
- Handles multiple speakers, noise, accents
"""

import torch
import torchaudio
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

class WhisperRecognizer:
    """
    Production-ready speech recognition with Whisper.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str | None = None,
        language: str = "english"
    ):
        """
        Initialize Whisper recognizer.

        Args:
            model_size: tiny, base, small, medium, large
            device: cuda, cpu, or None (auto-detect)
            language: Language code (english, turkish, etc.)
        """
        import whisper

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_size = model_size
        self.language = language

        # Load model
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"Model loaded on {self.device}")

    def transcribe(
        self,
        audio_path: str,
        task: str = "transcribe",
        temperature: float = 0.0,
        beam_size: int = 5,
        best_of: int = 5,
        patience: float = 1.0
    ) -> dict:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file
            task: 'transcribe' or 'translate'
            temperature: Sampling temperature (0 = greedy)
            beam_size: Beam size for decoding
            best_of: Number of candidates when sampling
            patience: Beam search patience

        Returns:
            Dictionary with transcription results
        """
        # Load audio
        audio = whisper.load_audio(audio_path)

        # Transcribe
        result = self.model.transcribe(
            audio,
            task=task,
            language=self.language,
            temperature=temperature,
            beam_size=beam_size,
            best_of=best_of,
            patience=patience,
            # Return additional info
            word_timestamps=True,
            segment_timestamps=True
        )

        return {
            "text": result["text"].strip(),
            "segments": result["segments"],
            "language": result.get("language", self.language)
        }

    def transcribe_with_diarization(
        self,
        audio_path: str,
        num_speakers: int | None = None
    ) -> list[dict]:
        """
        Transcribe audio with speaker diarization.

        Args:
            audio_path: Path to audio file
            num_speakers: Number of speakers (None = auto-detect)

        Returns:
            The segments with speaker labels
        """
        # Transcribe first
        result = self.transcribe(audio_path)

        # Apply diarization
        diarization = self._speaker_diarization(audio_path, num_speakers)

        # Align with segments
        segments_with_speakers = []
        for segment in result["segments"]:
            speaker = self._get_speaker_for_segment(
                segment,
                diarization
            )
            segments_with_speakers.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": speaker
            })

        return segments_with_speakers

    def _speaker_diarization(
        self,
        audio_path: str,
        num_speakers: int | None = None
    ) -> list[dict]:
        """
        Perform speaker diarization using pyannote.audio.

        Returns list of (start, end, speaker) tuples
        """
        try:
            from pyannote.audio import Pipeline

            # Load diarization pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                token=False  # For demo; use HF token in production
            )

            # Send to device
            pipeline.to(self.device)

            # Apply diarization
            diarization = pipeline(audio_path)

            # Convert to list
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            return segments

        except Exception as e:
            print(f"Diarization failed: {e}")
            return []

    def _get_speaker_for_segment(
        self,
        segment: dict,
        diarization: list[dict]
    ) -> str:
        """Get speaker label for a transcribed segment"""
        segment_center = (segment["start"] + segment["end"]) / 2

        # Find overlapping diarization segment
        for dia in diarization:
            if dia["start"] <= segment_center <= dia["end"]:
                return dia["speaker"]

        return "UNKNOWN"

    def transcribe_streaming(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe audio chunk in real-time.

        Args:
            audio_chunk: Audio chunk as numpy array
            sample_rate: Sample rate

        Returns:
            Transcribed text
        """
        # Resample if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(
                sample_rate,
                16000
            )
            audio_chunk = resampler(torch.from_numpy(audio_chunk))
            audio_chunk = audio_chunk.numpy()

        # Transcribe
        result = self.model.transcribe(
            audio_chunk,
            language=self.language,
            temperature=0.0  # Greedy for speed
        )

        return result["text"].strip()

    def batch_transcribe(
        self,
        audio_paths: list[str],
        batch_size: int = 8
    ) -> dict[str, dict]:
        """
        Transcribe multiple audio files.

        Args:
            audio_paths: The audio file paths
            batch_size: Batch size for processing

        Returns:
            Dictionary mapping file paths to results
        """
        results = {}

        for i in range(0, len(audio_paths), batch_size):
            batch = audio_paths[i:i+batch_size]

            for path in batch:
                try:
                    result = self.transcribe(path)
                    results[path] = result
                    print(f"✓ Transcribed: {path}")
                except Exception as e:
                    print(f"✗ Failed: {path} - {e}")
                    results[path] = {"error": str(e)}

        return results

    def get_transcript_stats(
        self,
        transcription: dict
    ) -> dict:
        """
        Get statistics about transcription.

        Args:
            transcription: Result from transcribe()

        Returns:
            Statistics dictionary
        """
        text = transcription.get("text", "")
        segments = transcription.get("segments", [])

        # Basic stats
        word_count = len(text.split())
        duration = segments[-1]["end"] - segments[0]["start"] if segments else 0

        # Speaking rate (words per minute)
        if duration > 0:
            wpm = (word_count / duration) * 60
        else:
            wpm = 0

        # Segment stats
        segment_count = len(segments)
        avg_segment_duration = np.mean([
            s["end"] - s["start"] for s in segments
        ]) if segments else 0

        return {
            "word_count": word_count,
            "duration_seconds": duration,
            "speaking_rate_wpm": wpm,
            "segment_count": segment_count,
            "avg_segment_duration": avg_segment_duration,
            "language": transcription.get("language", "unknown")
        }

class AudioPreprocessor:
    """
    Audio preprocessing for speech recognition.
    """

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate

    def load_audio(
        self,
        audio_path: str,
        mono: bool = True
    ) -> tuple[np.ndarray, int]:
        """
        Load audio file.

        Returns:
            (audio_array, sample_rate)
        """
        waveform, sample_rate = torchaudio.load(audio_path)

        # Convert to mono if needed
        if mono and waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Convert to numpy
        audio = waveform.numpy()[0]

        return audio, sample_rate

    def resample(
        self,
        audio: np.ndarray,
        original_sample_rate: int
    ) -> np.ndarray:
        """Resample audio to target sample rate"""
        if original_sample_rate == self.target_sample_rate:
            return audio

        resampler = torchaudio.transforms.Resample(
            original_sample_rate,
            self.target_sample_rate
        )

        audio_tensor = torch.from_numpy(audio)
        resampled = resampler(audio_tensor)

        return resampled.numpy()

    def normalize_audio(
        self,
        audio: np.ndarray,
        method: str = "peak"
    ) -> np.ndarray:
        """
        Normalize audio.

        Args:
            audio: Audio array
            method: 'peak' or 'rms'
        """
        if method == "peak":
            # Peak normalization
            max_val = np.abs(audio).max()
            if max_val > 0:
                audio = audio / max_val

        elif method == "rms":
            # RMS normalization
            rms = np.sqrt(np.mean(audio ** 2))
            if rms > 0:
                audio = audio / rms

        return audio

    def remove_silence(
        self,
        audio: np.ndarray,
        sample_rate: int,
        threshold: float = 0.01
    ) -> np.ndarray:
        """
        Remove silence from audio.

        Args:
            audio: Audio array
            sample_rate: Sample rate
            threshold: Silence threshold
        """
        # Calculate energy
        frame_length = int(0.025 * sample_rate)  # 25ms frames
        energy = np.array([
            np.mean(audio[i:i+frame_length] ** 2)
            for i in range(0, len(audio), frame_length)
        ])

        # Find non-silent frames
        non_silent = energy > threshold

        # Create mask
        mask = np.zeros(len(audio), dtype=bool)
        for i, is_speech in enumerate(non_silent):
            start = i * frame_length
            end = min(start + frame_length, len(audio))
            mask[start:end] = is_speech

        return audio[mask]

# Demo
if __name__ == "__main__":
    import sys

    # Initialize recognizer
    recognizer = WhisperRecognizer(model_size="base")

    # Demo transcription
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        print(f"\n=== Transcribing: {audio_path} ===\n")

        result = recognizer.transcribe(audio_path)
        print(result["text"])

        # Get stats
        stats = recognizer.get_transcript_stats(result)
        print(f"\n=== Stats ===")
        print(f"Words: {stats['word_count']}")
        print(f"Duration: {stats['duration_seconds']:.1f}s")
        print(f"Speaking rate: {stats['speaking_rate_wpm']:.1f} WPM")
    else:
        print("Usage: python whisper_system.py <audio_file>")
```

### Step 1.1: Build Real-Time Transcription

```python
# File: realtime_transcription.py
"""
Real-time speech transcription with streaming.
"""

import queue
import threading
import torch
import whisper
import numpy as np
from collections.abc import Callable

class RealTimeTranscriber:
    """
    Real-time speech transcription using Whisper.
    """

    def __init__(
        self,
        model_size: str = "base",
        callback: Callable[[str], None] = None
    ):
        self.model = whisper.load_model(model_size)
        self.callback = callback or print
        self.audio_queue = queue.Queue()
        self.is_running = False

    def process_audio(self, audio_chunk: np.ndarray):
        """Process audio chunk"""
        self.audio_queue.put(audio_chunk)

    def start(self):
        """Start transcription thread"""
        self.is_running = True
        self.thread = threading.Thread(target=self._transcription_loop)
        self.thread.start()

    def stop(self):
        """Stop transcription"""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join()

    def _transcription_loop(self):
        """Main transcription loop"""
        while self.is_running:
            try:
                # Get audio chunk (with timeout)
                audio = self.audio_queue.get(timeout=0.1)

                # Transcribe
                result = self.model.transcribe(
                    audio,
                    language="english",
                    temperature=0.0
                )

                # Callback with result
                text = result["text"].strip()
                if text:
                    self.callback(text)

            except queue.Empty:
                continue

# Demo usage
if __name__ == "__main__":
    def on_transcript(text):
        print(f"Transcript: {text}")

    transcriber = RealTimeTranscriber(callback=on_transcript)
    transcriber.start()

    print("Listening... (Ctrl+C to stop)")
    try:
        while True:
            # In real usage, get audio from microphone
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        transcriber.stop()
```

**Checkpoint 1:** ✅ Whisper transcription working

---

## Part 2: Text-to-Speech Synthesis (90 minutes)

### Building Voice Synthesis

```python
# File: tts_system.py
"""
Text-to-Speech Synthesis System
================================

Supports multiple TTS engines:
- Coqui TTS (high quality)
- pyttsx3 (offline, simple)
- Edge TTS (Microsoft, free)
"""

import torch
import numpy as np
from dataclasses import dataclass
import io

class TTSEngine:
    """Base TTS engine interface"""

    def synthesize(self, text: str, **kwargs) -> np.ndarray:
        """Synthesize speech from text"""
        raise NotImplementedError

class CoquiTTSEngine(TTSEngine):
    """
    High-quality TTS using Coqui TTS.
    """

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/vits",
        device: str | None = None
    ):
        from TTS.api import TTS

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading Coqui TTS: {model_name}")

        self.tts = TTS(
            model_name=model_name,
            progress_bar=False,
            gpu=self.device == "cuda"
        )

        print("TTS model loaded")

    def synthesize(
        self,
        text: str,
        speaker_idx: str | None = None,
        language_idx: str | None = None
    ) -> np.ndarray:
        """
        Synthesize speech from text.

        Args:
            text: Input text
            speaker_idx: Speaker index (for multi-speaker models)
            language_idx: Language code

        Returns:
            Audio as numpy array (float32, [-1, 1])
        """
        # Synthesize
        wav = self.tts.tts(
            text=text,
            speaker=speaker_idx,
            language=language_idx
        )

        return np.array(wav, dtype=np.float32)

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        **kwargs
    ):
        """Synthesize and save to file"""
        wav = self.synthesize(text, **kwargs)

        # Save
        from scipy.io.wavfile import write
        write(output_path, 22050, wav)

        print(f"Saved to: {output_path}")

class EdgeTTSEngine(TTSEngine):
    """
    Microsoft Edge TTS (free, high quality).
    """

    def __init__(self, voice: str = "en-US-AriaNeural"):
        import edge_tts

        self.voice = voice
        self.communicate = edge_tts.Communicate

    async def synthesize(
        self,
        text: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> np.ndarray:
        """
        Synthesize speech with Edge TTS.

        Args:
            text: Input text
            rate: Speaking rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment

        Returns:
            Audio as numpy array
        """
        # Create communicate object
        communicate = self.communicate(
            text,
            self.voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )

        # Get audio
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        # Convert to numpy
        import scipy.io.wavfile as wavfile
        with io.BytesIO(audio_data) as f:
            sample_rate, audio = wavfile.read(f)

        # Normalize to [-1, 1]
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0

        return audio

    def synthesize(self, text: str, **kwargs) -> np.ndarray:
        """Sync wrapper for async method"""
        import asyncio
        return asyncio.run(self.synthesize(text, **kwargs))

class VoiceCloner:
    """
    Clone voices from audio samples.
    """

    def __init__(self):
        from TTS.api import TTS

        # Use voice cloning model
        self.tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/your_tts",
            progress_bar=False,
            gpu=torch.cuda.is_available()
        )

    def clone_voice(
        self,
        reference_audio: str,
        text: str,
        language: str = "en"
    ) -> np.ndarray:
        """
        Synthesize with cloned voice.

        Args:
            reference_audio: Path to reference audio
            text: Text to synthesize
            language: Language code

        Returns:
            Synthesized audio
        """
        wav = self.tts.tts(
            text=text,
            speaker_wav=reference_audio,
            language=language
        )

        return np.array(wav, dtype=np.float32)

class TTSManager:
    """
    Manager for multiple TTS engines.
    """

    def __init__(self):
        self.engines = {}
        self.default_engine = None

    def register_engine(self, name: str, engine: TTSEngine, set_default: bool = False):
        """Register a TTS engine"""
        self.engines[name] = engine
        if set_default or self.default_engine is None:
            self.default_engine = name

    def synthesize(
        self,
        text: str,
        engine: str | None = None,
        **kwargs
    ) -> np.ndarray:
        """Synthesize with specified engine"""
        engine_name = engine or self.default_engine

        if engine_name not in self.engines:
            raise ValueError(f"Unknown engine: {engine_name}")

        return self.engines[engine_name].synthesize(text, **kwargs)

    def list_voices(self, engine: str | None = None) -> list[str]:
        """List available voices"""
        # This is engine-specific
        # Implementation depends on the engine
        return ["default"]

# Demo
if __name__ == "__main__":
    import sys

    # Initialize TTS
    try:
        tts = CoquiTTSEngine()
    except:
        print("Coqui TTS not available, falling back to Edge TTS")
        tts = EdgeTTSEngine()

    # Synthesize
    text = "Hello, this is a text-to-speech demonstration."

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])

    print(f"Synthesizing: {text}")

    audio = tts.synthesize(text)

    # Save
    output_file = "output.wav"
    from scipy.io.wavfile import write
    write(output_file, 22050, audio)

    print(f"Saved to: {output_file}")
```

**Checkpoint 2:** ✅ TTS synthesis working

---

## Part 3: Voice Assistant (90 minutes)

### Building Conversational Voice AI

```python
# File: voice_assistant.py
"""
Voice-Enabled AI Assistant
==========================

Combines:
- Whisper (speech-to-text)
- LLM (text understanding/generation)
- TTS (text-to-speech)
"""

import torch
from typing import Any
import numpy as np
import queue
import threading

from whisper_system import WhisperRecognizer
from tts_system import CoquiTTSEngine, EdgeTTSEngine

class VoiceAssistant:
    """
    Complete voice assistant pipeline.
    """

    def __init__(
        self,
        llm_client=None,
        whisper_model: str = "base",
        tts_engine: str = "coqui"
    ):
        """
        Initialize voice assistant.

        Args:
            llm_client: LLM client (e.g., OpenAI, local model)
            whisper_model: Whisper model size
            tts_engine: TTS engine to use
        """
        print("Initializing voice assistant...")

        # Speech recognition
        self.stt = WhisperRecognizer(model_size=whisper_model)

        # Speech synthesis
        if tts_engine == "coqui":
            try:
                self.tts = CoquiTTSEngine()
            except:
                print("Coqui TTS unavailable, using Edge TTS")
                self.tts = EdgeTTSEngine()
        else:
            self.tts = EdgeTTSEngine()

        # LLM
        self.llm = llm_client

        # Audio buffer
        self.audio_queue = queue.Queue()
        self.is_listening = False

        print("Voice assistant ready!")

    def listen_and_respond(
        self,
        audio_path: str,
        context: str | None = None
    ) -> str:
        """
        Complete listening and responding cycle.

        Args:
            audio_path: Path to audio file
            context: The conversation context, or None

        Returns:
            Response text
        """
        # Step 1: Transcribe
        print("🎤 Listening...")
        transcription = self.stt.transcribe(audio_path)
        user_text = transcription["text"]
        print(f"👤 User: {user_text}")

        if not user_text:
            return "I couldn't hear you clearly."

        # Step 2: Generate response
        print("🧠 Thinking...")
        response = self._generate_response(user_text, context)
        print(f"🤖 Assistant: {response}")

        # Step 3: Speak response
        print("🔊 Speaking...")
        self._speak(response)

        return response

    def _generate_response(self, user_input: str, context: str | None = None) -> str:
        """Generate response using LLM"""
        if self.llm is None:
            # Simple rule-based responses
            responses = {
                "hello": "Hello! How can I help you?",
                "hi": "Hi there!",
                "how are you": "I'm doing well, thank you!",
                "bye": "Goodbye!",
                "thank": "You're welcome!",
                "what is your name": "I'm your AI voice assistant."
            }

            user_input_lower = user_input.lower()

            for key, response in responses.items():
                if key in user_input_lower:
                    return response

            return "I heard you say: " + user_input

        # Use LLM
        prompt = f"""
        You are a helpful voice assistant. Respond naturally and conversationally.

        User: {user_input}

        Respond concisely (1-2 sentences):
        """

        if context:
            prompt = f"""
            Context: {context}

            {prompt}
            """

        response = self.llm.generate(prompt)
        return response.strip()

    def _speak(self, text: str):
        """Convert text to speech"""
        audio = self.tts.synthesize(text)

        # Save to temp file
        import tempfile
        from scipy.io.wavfile import write

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
            write(output_path, 22050, audio)

        # Play audio
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()

        # Cleanup
        import os
        os.unlink(output_path)

    def start_conversation(self):
        """
        Start interactive voice conversation.

        Requires real-time audio input (microphone).
        """
        import pyaudio

        # Audio parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024

        # Initialize audio
        audio = pyaudio.PyAudio()

        print("\n=== Voice Conversation ===")
        print("Press ENTER to speak, 'q' to quit\n")

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        context = ""

        try:
            while True:
                user_input = input("Press ENTER to speak (or 'q' to quit): ")

                if user_input.lower() == 'q':
                    break

                # Record audio
                print("🎤 Recording... (speak now)")
                frames = []

                # Record for 5 seconds
                for _ in range(0, int(RATE / CHUNK * 5)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                print("✓ Recording stopped")

                # Convert to numpy
                audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                audio_data = audio_data.astype(np.float32) / 32768.0

                # Save to temp file
                import tempfile
                from scipy.io.wavfile import write

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                    write(temp_path, RATE, audio_data)

                # Process
                try:
                    response = self.listen_and_respond(temp_path, context)
                    context += f"\nUser: {user_input}\nAssistant: {response}"
                except Exception as e:
                    print(f"Error: {e}")

                # Cleanup
                import os
                os.unlink(temp_path)

        except KeyboardInterrupt:
            print("\nConversation ended")

        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

class ConversationManager:
    """
    Manage conversation state and context.
    """

    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
        self.context = {}

    def add_turn(self, role: str, content: str):
        """Add conversation turn"""
        self.history.append({
            "role": role,
            "content": content
        })

        # Trim if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_context(self) -> str:
        """Get conversation context as string"""
        context_parts = []
        for turn in self.history:
            role = turn["role"].capitalize()
            content = turn["content"]
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def set_context_var(self, key: str, value: Any):
        """Set context variable"""
        self.context[key] = value

    def get_context_var(self, key: str, default=None):
        """Get context variable"""
        return self.context.get(key, default)

# Demo with local LLM
if __name__ == "__main__":
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # Load small LLM
    print("Loading LLM...")
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    def generate_llm(prompt: str) -> str:
        """Simple LLM generation"""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    # Create assistant
    assistant = VoiceAssistant(llm_client=type("Client", (), {"generate": generate_llm})())

    # Test with audio file
    if len(sys.argv) > 1:
        assistant.listen_and_respond(sys.argv[1])
    else:
        print("Usage: python voice_assistant.py <audio_file>")
```

**Checkpoint 3:** ✅ Voice assistant working

---

## Part 4: Audio Analysis (60 minutes)

### Extracting Insights from Audio

```python
# File: audio_analytics.py
"""
Audio Analysis and Insights
============================

Extract:
- Speaking patterns
- Emotion detection
- Audio quality metrics
- Speaker characteristics
"""

import torch
import numpy as np
import torchaudio
import librosa

class AudioAnalyzer:
    """
    Comprehensive audio analysis.
    """

    def __init__(self):
        pass

    def analyze_audio_file(self, audio_path: str) -> dict:
        """
        Perform complete audio analysis.

        Args:
            audio_path: Path to audio file

        Returns:
            Analysis results
        """
        # Load audio
        audio, sr = torchaudio.load(audio_path)

        # Convert to mono if needed
        if audio.shape[0] > 1:
            audio = torch.mean(audio, dim=0)
        else:
            audio = audio[0]

        audio_np = audio.numpy()

        results = {
            "duration": len(audio_np) / sr,
            "sample_rate": sr,
            "channels": audio.shape[0] if len(audio.shape) > 1 else 1
        }

        # Add various analyses
        results.update(self._analyze_quality(audio_np, sr))
        results.update(self._analyze_spectral(audio_np, sr))
        results.update(self._analyze_temporal(audio_np, sr))

        return results

    def _analyze_quality(self, audio: np.ndarray, sr: int) -> dict:
        """Analyze audio quality metrics"""
        # Signal-to-noise ratio (simplified)
        signal_power = np.mean(audio ** 2)

        # Estimate noise (segments with low energy)
        frame_length = int(0.05 * sr)
        energy = np.array([
            np.mean(audio[i:i+frame_length] ** 2)
            for i in range(0, len(audio), frame_length)
        ])

        # Noise level = lowest 10% energy
        noise_level = np.percentile(energy, 10)

        if noise_level > 0:
            snr_db = 10 * np.log10(signal_power / noise_level)
        else:
            snr_db = float('inf')

        # Clipping detection
        clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)

        return {
            "snr_db": snr_db,
            "clipping_ratio": clipping_ratio,
            "signal_power": float(signal_power),
            "noise_level": float(noise_level)
        }

    def _analyze_spectral(self, audio: np.ndarray, sr: int) -> dict:
        """Analyze spectral characteristics"""
        # Compute spectrogram
        spec = librosa.feature.melspectrogram(y=audio, sr=sr)
        spec_db = librosa.power_to_db(spec, ref=np.max)

        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]

        return {
            "spectral_centroid_mean": float(np.mean(centroid)),
            "spectral_centroid_std": float(np.std(centroid)),
            "spectral_rolloff_mean": float(np.mean(rolloff)),
            "zero_crossing_rate_mean": float(np.mean(zcr)),
            "zero_crossing_rate_std": float(np.std(zcr))
        }

    def _analyze_temporal(self, audio: np.ndarray, sr: int) -> dict:
        """Analyze temporal characteristics"""
        # Tempo (BPM)
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)

        # RMS energy
        rms = librosa.feature.rms(y=audio)[0]

        # Onset detection
        onsets = librosa.onset.onset_detect(y=audio, sr=sr)

        return {
            "estimated_bpm": float(tempo),
            "num_beats": len(beats),
            "num_onsets": len(onsets),
            "rms_mean": float(np.mean(rms)),
            "rms_std": float(np.std(rms))
        }

    def detect_speech_segments(
        self,
        audio: np.ndarray,
        sr: int
    ) -> list[dict]:
        """
        Detect speech segments in audio.

        Args:
            audio: Audio array
            sr: Sample rate

        Returns:
            The (start, end) tuples
        """
        # Use energy-based VAD
        frame_length = int(0.025 * sr)  # 25ms
        hop_length = int(0.010 * sr)    # 10ms

        # Compute energy
        frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
        energy = np.mean(frames ** 2, axis=0)

        # Smooth energy
        from scipy.ndimage import gaussian_filter1d
        energy_smooth = gaussian_filter1d(energy, sigma=3)

        # Threshold
        threshold = np.percentile(energy_smooth, 75)

        # Find speech segments
        is_speech = energy_smooth > threshold

        # Convert to segments
        segments = []
        in_speech = False
        start = 0

        for i, speech in enumerate(is_speech):
            time = i * hop_length / sr

            if speech and not in_speech:
                start = time
                in_speech = True
            elif not speech and in_speech:
                segments.append({"start": start, "end": time})
                in_speech = False

        if in_speech:
            segments.append({"start": start, "end": len(audio) / sr})

        return segments

# Demo
if __name__ == "__main__":
    analyzer = AudioAnalyzer()

    import sys
    if len(sys.argv) > 1:
        results = analyzer.analyze_audio_file(sys.argv[1])
        print("\n=== Audio Analysis ===")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
```

**Checkpoint 4:** ✅ Audio analysis working

---

## Part 5: Production Deployment (60 minutes)

### Dockerizing Voice System

```dockerfile
# File: Dockerfile.voice
FROM python:3.13-slim

WORKDIR /app

# Install audio dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Official uv-in-Docker pattern: copy the uv binary from the uv image
# (https://docs.astral.sh/uv/guides/integration/docker/)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
COPY requirements-voice.txt .
RUN uv pip install --system --no-cache -r requirements-voice.txt

# Copy application
COPY voice_api.py .
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "voice_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# File: voice_api.py
"""
Voice API Service
=================
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import tempfile
import os

from voice_assistant import VoiceAssistant

app = FastAPI(title="Voice AI API")

# Initialize assistant
assistant = VoiceAssistant()

class SpeakRequest(BaseModel):
    text: str
    engine: str = "coqui"

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(await file.read())
        temp_path = f.name

    try:
        result = assistant.stt.transcribe(temp_path)
        return {"text": result["text"]}
    finally:
        os.unlink(temp_path)

@app.post("/speak")
async def speak(request: SpeakRequest):
    """Generate speech from text"""
    audio = assistant.tts.synthesize(request.text)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name

    from scipy.io.wavfile import write
    write(output_path, 22050, audio)

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename="speech.wav"
    )

@app.post("/chat")
async def chat(file: UploadFile = File(...)):
    """Voice chat"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(await file.read())
        temp_path = f.name

    try:
        response = assistant.listen_and_respond(temp_path)
        return {"response": response}
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Checkpoint 5:** ✅ Production deployment ready

---

## Lab Completion Checklist

- [ ] Part 1: Whisper speech recognition
- [ ] Part 2: Text-to-speech synthesis
- [ ] Part 3: Voice assistant
- [ ] Part 4: Audio analysis
- [ ] Part 5: Production API deployment

---

## Summary

In this lab, you learned:

1. **Whisper** - State-of-the-art speech recognition
2. **TTS Engines** - Coqui and Edge TTS
3. **Voice Assistant** - Complete voice pipeline
4. **Audio Analysis** - Extract insights from audio
5. **Production Deployment** - Dockerized voice services

---

## Next Steps

1. **LAB-013: Advanced Function Calling** - Enhance your assistant
2. **LAB-014: AI Evaluation** - Test your voice system
3. Build multi-modal voice + vision assistant

---

**Lab:** 012 - Audio AI
**Time Estimate:** 7 hours
**Difficulty:** ⭐⭐⭐ Advanced
