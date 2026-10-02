---
Document ID: 3500-QUIZ
Title: "3500: Multimodal Models - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'transformers', 'multimodal']
---

# 3500: Multimodal Models - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. What is a multimodal model?**

A) A model with multiple layers
B) An ensemble of models
C) A model that processes multiple data types (text, image, audio)
D) A model trained on multiple unrelated downstream tasks with no shared parameters

**2. What is CLIP primarily designed for?**

A) Image generation
B) Video generation
C) Audio processing and speech synthesis pipelines
D) Image-text retrieval and understanding

**3. What training objective does CLIP use?**

A) Masked language modeling
B) Next token prediction
C) Contrastive learning on image-text pairs
D) Full sequence-to-sequence supervised training on parallel corpora

**4. What is the main advantage of multimodal models?**

A) Faster training
B) Simpler architecture with fewer parameters to train and deploy
C) Smaller model size
D) Richer understanding by combining modalities

**5. Which model type is LLaVA?**

A) Vision-language model
B) Language-only model
C) Audio-language model
D) Video generation model

**6. What is the typical approach for building vision-language models?**

A) Train the entire multimodal stack from scratch on image-text data with no pretrained components
B) Use separate models for each modality
C) Pretrain each modality's encoder separately, then connect the two
D) Convert images to text before processing

**7. What is BLIP designed for?**

A) Image generation
B) Video understanding
C) Audio classification and speech-to-text transcription
D) Image-language understanding and generation

**8. How do most multimodal models handle different modalities?**

A) Separate processing with late fusion
B) Project all modalities to shared embedding space
C) Process text only, ignore other modalities
D) Convert every modality into plain text strings at the input layer

**9. What is a key challenge in multimodal learning?**

A) Model size alone, with modalities irrelevant to the challenge
B) Aligning different modalities in shared space
C) Training speed
D) A fixed model-size formula independent of modalities

**10. Which modality alignment technique is most common?**

A) Contrastive learning
B) Generative learning
C) Reinforcement learning
D) Unsupervised learning

**11. Which architecture is the typical vision encoder in modern VLMs?**

A) LSTM networks with attention over frame features
B) Vision Transformer (ViT)
C) U-Net
D) GAN discriminator

**12. In LLaVA, the projector's job is to:**

A) Generate novel images from the text prompt at inference time
B) Compress video frames
C) Map vision encoder outputs into the LLM's embedding space
D) Tokenize text

**13. OpenAI's Whisper is a model for:**

A) Text-to-image generation
B) Speech recognition (and translation)
C) Music recommendation
D) Video captioning with temporal action localization

**14. CLIP enables zero-shot classification by:**

A) Comparing the image embedding to text embeddings of class prompts
B) Training a softmax head per class
C) Running k-means clustering directly on the raw pixel values of every frame
D) Running OCR on the image

**15. Audio is commonly represented for neural processing as:**

A) Raw bytes
B) MIDI notes
C) MP3 file containers passed straight to the encoder
D) Spectrograms (or learned audio tokens)

**16. Images enter a vision-language model as:**

A) Patch embeddings projected into the LLM's input space
B) Raw pixel matrices appended to the text
C) File paths resolved at generation time
D) Base64 strings decoded inline by the LLM tokenizer at runtime

**17. CLIP-style models are trained on:**

A) Labeled ImageNet classes
B) Synthetic renders only
C) Hundreds of millions of web image-text pairs
D) Paired audio transcripts only, with no images involved

**18. Automatic speech recognition (ASR) and text-to-speech (TTS) differ in that:**

A) They are the same task with different names
B) ASR converts audio to text; TTS converts text to audio
C) ASR converts text to audio; TTS converts audio to text
D) Both tasks convert text into audio waveforms using exactly the same pipelines

**19. A standard benchmark family for evaluating vision-language models is:**

A) GLUE only
B) HumanEval only
C) LibriSpeech only, a speech corpus used for reading comprehension tasks
D) Visual question answering benchmarks (e.g., VQA)

**20. "Visual instruction tuning" means fine-tuning a VLM on:**

A) Instruction-following data that includes images
B) Image classification labels only
C) Contrastive image-text pairs used for pretraining alignment
D) Audio transcripts

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | A multimodal model processes several data types - text, image, audio |
| 2 | D | CLIP aligns images and text for retrieval and understanding |
| 3 | C | CLIP trains contrastively - matching image-text pairs pull together |
| 4 | D | Combining modalities gives richer understanding |
| 5 | A | LLaVA is a vision-language model |
| 6 | C | Standard recipe: pretrained ViT plus pretrained LLM, joined by a projector |
| 7 | D | BLIP covers image-language understanding and generation |
| 8 | B | Modalities are embedded into a shared space |
| 9 | B | The core challenge is aligning modalities in one space |
| 10 | A | Contrastive learning (CLIP-style) is the dominant alignment technique |
| 11 | B | ViT is the standard vision encoder in modern VLMs |
| 12 | C | LLaVA's projector maps ViT outputs into the LLM embedding space |
| 13 | B | Whisper does speech recognition (and translation) |
| 14 | A | Zero-shot: compare the image embedding to text prompts of class names |
| 15 | D | Audio enters as spectrograms or learned audio tokens |
| 16 | A | Images become patch embeddings projected into the LLM input space |
| 17 | C | CLIP-style training uses hundreds of millions of web image-text pairs |
| 18 | B | ASR converts audio to text; TTS converts text to audio |
| 19 | D | VQA-family benchmarks evaluate vision-language models |
| 20 | A | Visual instruction tuning fine-tunes on instruction data that includes images |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1-12, 14, 16-17, 19-20:** [3501: Vision-Language Models](../3501-Vision-Language-Models.md) — CLIP's contrastive objective and zero-shot classification, the ViT → projector → LLM recipe behind LLaVA-class models, shared embedding spaces and patch-embedding inputs
- **Questions 13, 15, 18:** [3502: Audio Models](../3502-Audio-Models.md) — Whisper speech recognition, mel-spectrogram vs codec-token representations, and the ASR/TTS direction split

