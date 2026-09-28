---
Document ID: 3502
Title: Audio Models
Phase: 3
Module: 3500
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'multimodal', 'audio', 'whisper', 'tts']
---

# 3502: Audio Models

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [How Machines Represent Audio](#how-machines-represent-audio)
- [Whisper: Speech Recognition](#whisper-speech-recognition)
- [Whisper in Production](#whisper-in-production)
- [Audio and Speech Generation](#audio-and-speech-generation)
- [Voice Assistant Pipeline](#voice-assistant-pipeline)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Contrast mel-spectrogram and neural-codec audio representations and say which model family consumes each
- Explain Whisper's 30-second window, multitask prompt tokens, and why the decoder drives language/task selection
- Choose between openai-whisper, faster-whisper, and whisper.cpp using latency and hardware constraints
- Describe the text-to-token-to-audio generation stack behind modern speech synthesis
- Assemble a low-latency STT → LLM → TTS pipeline and name where the latency actually goes

---

## Abstract

Audio became a first-class modality for transformers once two representations matured: the mel-spectrogram (compact, visual, perfect for encoder-style perception) and discrete neural codecs (audio compressed to token sequences a language-model decoder can generate). Whisper — a 680k-hour encoder-decoder trained on both — is the reference speech-to-text stack, and codec-token models (AudioLM, MusicGen, modern TTS) are the reference generation stack. This lesson builds both mental models, shows production Whisper deployment with the faster variants, and closes with the voice-assistant pipeline where all of it meets an LLM.

## How Machines Represent Audio

### Two Representations, Two Model Families

```text
1. Mel spectrogram                        2. Neural codec tokens
   (perception / understanding)              (generation)

   raw waveform (16kHz)                      raw waveform
        |                                         |
   STFT -> power spectrum                  encoder compresses to
        |                                  discrete codes (e.g. 75 Hz,
   mel filterbank (80 bins,                multiple codebook streams)
   log scale, ~25ms frames)                     |
        |                                  transformer decoder
   [80, 3000] tensor per 30s window        generates code tokens
        |                                       |
   ENCODER consumes this                   vocoder / codec decoder
   (Whisper, wav2vec2, HuBERT)             reconstructs waveform
```

```text
Why the split matters

- Understanding tasks (ASR, speaker ID, emotion): spectrograms win -
  dense, differentiable, position-aligned with time
- Generation tasks (TTS, music): discrete tokens win - the whole
  autoregressive toolbox (sampling, temperature, beam search)
  applies to audio the way it applies to text
```

### Sampling Facts Worth Memorizing

```text
16 kHz        Whisper's input rate; downsample everything to this
30 seconds    Whisper's fixed window (3000 mel frames @ 10ms hop)
75 tokens/s   typical neural-codec frame rate -> 1 min audio ~ 4.5k tokens
```

## Whisper: Speech Recognition

### Architecture

```text
Encoder-decoder transformer, trained on 680k hours of weakly
supervised audio

Input:   log-mel spectrogram of a padded 30s window
Encoder: convolutional downsampler + transformer blocks
         (audio -> continuous representation)
Decoder: standard autoregressive text decoder over a 50k BPE
         vocabulary, PLUS special control tokens:

         <|startoftranscript|><|en|><|transcribe|><|notimestamps|>
            task selector  language   task          precision

The decoder CHOOSES language, task (transcribe vs translate
to English), and timestamp granularity - all via prompt tokens.
No separate models per language or per task.
```

Training trick worth knowing: 30% of training windows are padded with silence and the model is taught to predict nothing. This is what suppresses the classic hallucinate-when-silent failure of older ASR systems — mostly.

### Basic Usage

```python
import whisper

model = whisper.load_model("base")   # tiny/base/small/medium/large-v3

result = model.transcribe(
    "meeting.wav",
    language="tr",           # pin it; detection misfires on short clips
    task="transcribe",       # or "translate" (X -> English)
    fp16=True,
)

print(result["text"])                    # full transcript
for seg in result["segments"]:           # timestamped segments
    print(seg["start"], seg["end"], seg["text"])
```

```text
Model selection by workload

tiny/base       CPU-realtime, drafts, keyword spotting
small           single-GPU throughput workloads
medium          accuracy-sensitive batch jobs
large-v3        multilingual hard audio; 10GB VRAM fp16
```

## Whisper in Production

### faster-whisper: The Default Server Choice

The reference implementation is fine for scripts but leaves 4× speed on the table. faster-whisper re-implements Whisper on CTranslate2 with int8 quantization:

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")

segments, info = model.transcribe(
    "meeting.wav",
    language="tr",
    vad_filter=True,          # built-in voice activity detection:
                              # skips silence, cuts hallucinations + time
    beam_size=5,
)

print(f"detected: {info.language} (p={info.language_probability:.2f})")
for seg in segments:          # segments are a LAZY generator
    print(f"[{seg.start:07.2f} -> {seg.end:07.2f}] {seg.text}")
```

```text
Deployment options compared

openai-whisper     reference quality/behavior; slowest; PyTorch dep tree
faster-whisper     ~4x faster, int8, VAD built in; default for servers
whisper.cpp        CPU-only edge boxes, quantized GGML weights,
                   zero Python runtime (pairs with 4403 GGUF thinking)
whisper API        zero ops; data residency and cost per audio-minute
                   are the trade
```

### Batch Transcription Service

```python
import asyncio
import hashlib
from dataclasses import dataclass

@dataclass
class Transcript:
    text: str
    language: str
    duration_s: float

class TranscriptionService:
    """Single-model, GPU-bound worker pool.

    Whisper is memory-bandwidth bound: batching many long files on
    one GPU helps less than running 2 workers on 2 GPUs. Keep the
    concurrency bounded and let the VAD skip the silence.
    """

    def __init__(self, model_size: str = "large-v3", max_workers: int = 2):
        self._models = [
            WhisperModel(model_size, device="cuda", compute_type="int8_float16")
            for _ in range(max_workers)
        ]
        self._next = 0
        self._cache: dict[str, Transcript] = {}

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Transcript:
        key = hashlib.sha1(audio_bytes).hexdigest()
        if key in self._cache:                       # identical upload -> free
            return self._cache[key]

        path = await _write_temp(audio_bytes, sample_rate)
        model = self._models[self._next % len(self._models)]
        self._next += 1

        segments, info = await asyncio.to_thread(
            model.transcribe, path, vad_filter=True, language=None
        )
        text = " ".join(s.text.strip() for s in segments)
        result = Transcript(text, info.language, info.duration)
        self._cache[key] = result
        return result
```

```text
Production checklist
- hash-keyed cache: identical audio files are common (retries)
- language pinning per tenant, detection only as fallback
- long files: VAD + 30s windows stream results; do not buffer
  the whole transcript before responding
- diarization ("who spoke") is a SEPARATE model (pyannote);
  Whisper gives what, not who
- PII: transcripts inherit every promise made about the audio
```

## Audio and Speech Generation

### The Generation Stack

```text
Three layers, each a research field of its own

1. Semantic tokens     content: what is said / what is played
                       (HuBERT-style units, text, or music tokens)
2. Acoustic tokens     timbre, prosody, speaker identity
                       (codec codes: EnCodec / SoundStream)
3. Waveform            vocoder decodes acoustic tokens to audio
                       (or the codec decoder itself)

Text-to-speech:  text -> LLM-ish decoder -> acoustic tokens -> vocoder
Audio-to-audio:  AudioLM/MusicGen: prompt tokens -> AR continuation
```

The practical takeaway: modern speech generation is **a language-model problem over codec tokens**. Everything you know about sampling, temperature, and repetition penalties transfers — and so do the failure modes (loops, drift).

### TTS in Practice

```python
# Pattern for a self-hosted TTS worker (APIs vary by engine;
# XTTS / Piper / Bark all follow this shape)
from pathlib import Path

class TTSService:
    def __init__(self, engine, voice: str, out_dir: Path):
        self.engine = engine
        self.voice = voice
        self.out_dir = out_dir

    def synthesize(self, text: str) -> Path:
        out = self.out_dir / f"{hashlib.sha1(text.encode()).hexdigest()}.wav"
        if not out.exists():
            self.engine.save_wav(text=text, speaker=self.voice, file_path=str(out))
        return out
```

```text
Selection heuristics
- Latency-first (assistant replies): Piper / streaming-capable engines,
  target first-audio < 300 ms
- Quality-first (media production): XTTS-class engines, voice cloning,
  seconds of latency acceptable
- Consistency across replies: pin one voice + stable seed;
  otherwise the assistant "changes voice" between turns
```

## Voice Assistant Pipeline

```text
     mic           VAD            Whisper          LLM           TTS
   ─────── > ┌─────────┐    ┌─────────────┐  ┌─────────┐  ┌──────────┐
   raw pcm   │ gate: is │ -> │ streaming   |> | tokens  |> │ streaming│ > speaker
             │ speech?  │    │ partials    │  │ stream  │  │ synth    │
             └─────────┘    └─────────────┘  └─────────┘  └──────────┘
               ~10ms            300-800ms      TTFT        first audio
                                               budget      budget
```

```python
class VoiceAssistant:
    """STT -> LLM -> TTS with latency accounting at each hop."""

    def __init__(self, stt, llm, tts, language: str = "tr"):
        self.stt, self.llm, self.tts = stt, llm, tts
        self.language = language

    def handle_turn(self, audio: bytes) -> bytes:
        import time
        t0 = time.perf_counter()

        text = self.stt.transcribe_bytes(audio, language=self.language)
        t1 = time.perf_counter()

        reply = self.llm.generate(text, stream=False)   # stream in real systems
        t2 = time.perf_counter()

        audio_out = self.tts.synthesize(reply)
        t3 = time.perf_counter()

        self._log_latency(stt=t1 - t0, llm=t2 - t1, tts=t3 - t2)
        return audio_out
```

```text
Where the latency actually goes (typical assistant)

1. Whisper runs on 30s WINDOWS - a 2s utterance still pays the
   window cost unless you stream with partial results
2. LLM time-to-first-token dominates; stream the reply INTO the
   TTS sentence by sentence instead of waiting for the full text
3. Barge-in (user interrupts) requires stopping TTS playback and
   the STT gate - design it early, it reshapes the pipeline
4. Target budget: < 1s perceived response; VAD must be < 50ms
```

---

## References

### Related PROJECT-OMEGA Documents

- [3501: Vision-Language Models](3501-Vision-Language-Models.md)

---

## Next Steps

- Phase 3 Complete! Next: **[Phase 4: Quantization](../../phase4-quantization/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Related Resources

- **Previous:** [3501: Vision-Language Models](./3501-Vision-Language-Models.md)
- **Related:** [7201: Tool Calling](../../phase7-agentic/7200-tools/7201-Tool-Calling.md)
- **Experiment:** [EXP_3501: Multimodal RAG](../../../../experiments/EXP_3501_MULTIMODAL_RAG.md)
