---
Document ID: CHEAT-SHEET-019
Title: "CHEAT-SHEET-019: Tokenizers"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'tokenizer', 'tokenization', 'bpe', 'transformers']
---

# CHEAT-SHEET-019: Tokenizers

**Quick Reference for:** the four-stage tokenization pipeline, the BPE merge loop, the byte-level twist that kills `<unk>`, the Unigram contrast, SentencePiece settings, and the vocab ladder.

**Version:** 1.0

---

## The Four-Stage Pipeline

Every tokenizer - BPE, Unigram, WordPiece - is the same four stages. The model stage is the only place they differ.

| Stage | What it does | Canonical example |
|---|---|---|
| Normalization | lowercase, accent strip, NFD/NFC | `Héllo` → `hello` |
| Pre-tokenization | split on whitespace/punctuation | GPT-2 regex: contractions first, then ` ?\p{L}+` |
| Subword model | learn/apply merges | BPE, Unigram, WordPiece |
| Post-processing | special tokens, offsets, truncation | `[CLS] ... [SEP]`, `<\|endoftext\|>` |

The pipeline's cost claim: **tokenizer choice is an architecture decision wearing a preprocessing costume** - it sets the cost of every forward pass and the ceiling of every context window (module 3202's closing rule).

## The BPE Merge Loop

BPE starts from the 256 byte symbols and repeatedly merges the **most frequent pair**. On the canonical corpus the first three merges are:

```python
CORPUS = ["hug", "pug", "pun", "bun", "hugs"]

def pair_counts(words):
    counts = {}
    for word, freq in words.items():
        for a, b in zip(word, word[1:]):
            counts[(a, b)] = counts.get((a, b), 0) + freq
    return counts

def apply_merge(words, pair):
    merged, joined = {}, "".join(pair)
    for word, freq in words.items():
        i, out = 0, []
        while i < len(word):
            if i + 1 < len(word) and (word[i], word[i + 1]) == pair:
                out.append(joined); i += 2
            else:
                out.append(word[i]); i += 1
        key = tuple(out)
        merged[key] = merged.get(key, 0) + freq
    return merged

words = {tuple(w): 1 for w in CORPUS}
chars = sum(len(w) for w in CORPUS)
for step in range(1, 4):
    counts = pair_counts(words)
    best = max(counts, key=counts.get)
    print("merge %d: %s+%s  count=%d" % (step, best[0], best[1], counts[best]))
    words = apply_merge(words, best)
symbols = sum(len(k) for k in words)
vocab = set()
for key in words:
    vocab.update(key)
print("%d chars -> %d symbols after 3 merges; vocab %d symbols" %
      (chars, symbols, len(vocab)))
```

Canonical trace: `merge 1: u+g count=3` (hug, pug, hugs all carry it), `merge 2: h+ug count=2` (producing `hug`), `merge 3: u+n count=2` (producing `un`). Note the teaching moment inside `apply_merge`: a merge rule is applied at **every occurrence in the corpus**, not just where it was counted first - `hugs` silently becomes `hug s` in merge 2 because the `h+ug` rule reaches it too. The compression bill: 16 chars → 9 symbols after 3 merges (43.8% shorter), with a 6-symbol learned vocab on top of the 256 byte symbols.

## GPT-2's Two Twists

1. **The regex pre-tokenizer.** `'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+` - contractions are protected, and a leading space attaches to the word it belongs to, so `" the"` and `"the"` are different tokens.
2. **Byte-level unicode mapping.** `bytes_to_unicode()` maps the 256 bytes to visible unicode characters (printable ASCII 33-126 plus `\t\n\r` keep their own codepoints; everything else lands at `256+n`). Because **every byte sequence is representable**, arbitrary binary, emoji, and any script tokenize without ever hitting `<unk>` - the property char-level vocabularies never had.

## BPE vs Unigram vs WordPiece

| Tokenizer | Model | Vocab Size | Multilingual | Code Support |
|-----------|-------|------------|--------------|--------------|
| BPE (GPT-2) | GPT-2 | 50k | ✗ | Limited |
| BPE (GPT-4) | GPT-4 | 100k | ✓ | ✓ |
| SentencePiece | T5, mT5 | 32k-250k | ✓ | ✗ |
| Unigram | ALBERT, BERT | 30k | ✓ | ✗ |
| WordPiece | BERT | 30k | Limited | ✗ |

The algorithmic contrast:

- **BPE is bottom-up**: start from bytes, merge the most frequent pair, repeat until the target vocab. Training is a merge loop; encoding is apply-the-learned-rules-in-order. Segmentation is deterministic.
- **Unigram is top-down**: start from a LARGE vocabulary, score the loss increase of removing each token, drop the least-damaging one, repeat. Because the final model is probabilistic, it can **score ambiguous segmentations** (`un|break|able` vs alternatives) - the thing BPE structurally cannot do.
- **WordPiece** is BPE's likelihood variant with the `##` continuation prefix and greedy longest-match-first encoding.

## SentencePiece in Five Settings

| Setting | Canonical value | Why |
|---|---|---|
| `model_type` | `'unigram'` (or `'bpe'`) | Unigram is the default; `'word'`/`'char'` for baselines |
| `character_coverage` | `0.995` (multilingual), `0.9995` (CJK) | rarer chars get folded to `<unk>` below it |
| whitespace | `▁` marker | "Hello world" → `▁Hello` `▁world`; decode is a lossless round-trip |
| `user_defined_symbols` | `['[CLS]', '[SEP]', '[MASK]']` | reserved pieces, never pruned by training |
| ids | `sp.pad_id() unk_id() bos_id() eos_id()` | `<pad> <unk> <s> </s>` resolved from the model file |

## The Vocab Ladder

The vocabulary is a compression-vs-coverage dial, and it prices the context window: the same text is a **longer token sequence** under a weaker tokenizer, so the model's nominal context buys fewer characters.

- **256** - the byte floor every byte-level BPE starts from; never an `<unk>`.
- **30k** - BERT-class (WordPiece/Unigram); limited multilingual reach.
- **50k** - GPT-2; English-first, Chinese text costs several tokens per character.
- **100k** - GPT-4 `cl100k_base`; multilingual + code both pull their weight.
- **32k-250k** - T5/mT5 SentencePiece family spans the whole range.

## Special Tokens and resize_token_embeddings

Canonical id maps: BERT `[PAD]`=0, `[UNK]`=1, `[CLS]`=2, `[SEP]`=3, `[MASK]`=4; GPT `<|endoftext|>`=50256; T5 `<pad>`=0, `<eos>`=1, `<unk>`=2.

Adding tokens is a **two-call contract**:

```text
tokenizer.add_special_tokens({'pad_token': '<pad>', ...})
model.resize_token_embeddings(len(tokenizer))   # without this: index-out-of-range
```

The second call is load-bearing twice over: it grows the input embedding AND the output head (they are tied), and the new rows start **randomly initialized** - a freshly added token that the model never learned to emit is the silent failure, not the crash.

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| `decode(encode(x)) != x` | char-level vocab dropped bytes to `<unk>` | use a byte-level tokenizer (GPT-2, tiktoken); coverage-check domain text |
| model never selects the new token | `resize_token_embeddings` done but no fine-tuning | new rows are random-init; train until the token earns probability mass |
| index out of range at forward | vocab grew, model table did not | run `resize_token_embeddings(len(tokenizer))` after every vocab change |
| Chinese text costs 3-5x the tokens | GPT-2's 50k English-first vocab | switch to `cl100k_base`-class multilingual coverage |
| `▁` symbols polluting comparisons | SentencePiece whitespace marker is part of the output | `replace('▁', ' ')` (or decode) before any text comparison |
| same text, different token counts across models | tokenizers are per-model architecture decisions | always count with THE model's own tokenizer, never a stand-in |

## Quick Reference For

- [Module 3202: Tokenizer Sciences](../../phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)
- [Module 3201: Rotary Positional Embeddings](../../phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md)
- [Module 3101: Self-Attention DeepDive](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md)
- [CHEAT-SHEET-018: Speculative Decoding](./CHEAT-SHEET-018-Speculative-Decoding.md)
