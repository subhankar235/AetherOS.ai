import logging
import re
from typing import List

import tiktoken

logger = logging.getLogger("services.ingestion.chunker")

ENCODING_NAME = "cl100k_base"


def get_encoding() -> tiktoken.Encoding:
    try:
        return tiktoken.get_encoding(ENCODING_NAME)
    except Exception:
        # Fallback to standard gpt-4 if the encoding is not cached
        return tiktoken.encoding_for_model("gpt-4")


def chunk_text(
    text: str,
    min_chunk_size: int = 300,
    max_chunk_size: int = 500,
    overlap_size: int = 50
) -> List[str]:
    """
    Chunks document text into semantic segments of size ~300-500 tokens.
    Uses sentence boundaries to avoid splitting mid-sentence and maintains an overlap.
    """
    if not text or not text.strip():
        return []

    encoding = get_encoding()

    # Split text into sentences using simple regex (respects period, question mark, exclamation, or double newlines)
    sentence_splits = re.split(r'(?<=[.!?])\s+|\n\n+', text)

    chunks = []
    current_chunk_sentences = []
    current_chunk_tokens = 0

    for sentence in sentence_splits:
        sentence = sentence.strip()
        if not sentence:
            continue

        try:
            sentence_tokens = len(encoding.encode(sentence))
        except Exception as e:
            logger.warning(f"Failed to encode sentence tokens: {str(e)}, falling back to character heuristic")
            # Fallback heuristic: 1 token ~= 4 characters
            sentence_tokens = max(1, len(sentence) // 4)

        # Handle edge case where a single sentence itself exceeds max_chunk_size
        if sentence_tokens > max_chunk_size:
            # If we have a pending chunk, finalize it first
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_chunk_tokens = 0

            # Split the oversized sentence into word blocks
            words = sentence.split(" ")
            sub_chunk_words = []
            sub_chunk_tokens = 0
            for word in words:
                try:
                    word_tokens = len(encoding.encode(word + " "))
                except Exception:
                    word_tokens = max(1, len(word) // 4)

                if sub_chunk_tokens + word_tokens > max_chunk_size:
                    if sub_chunk_words:
                        chunks.append(" ".join(sub_chunk_words))
                    # Overlap: keep the last few words
                    sub_chunk_words = sub_chunk_words[-15:] if len(sub_chunk_words) > 15 else sub_chunk_words
                    try:
                        sub_chunk_tokens = len(encoding.encode(" ".join(sub_chunk_words)))
                    except Exception:
                        sub_chunk_tokens = sum(max(1, len(w) // 4) for w in sub_chunk_words)

                sub_chunk_words.append(word)
                sub_chunk_tokens += word_tokens

            if sub_chunk_words:
                chunks.append(" ".join(sub_chunk_words))
            continue

        # If adding this sentence exceeds the maximum chunk size, close the current chunk and start next with overlap
        if current_chunk_tokens + sentence_tokens > max_chunk_size:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))

            # Backtrack to build the overlap
            overlap_sentences = []
            overlap_tokens = 0
            for s in reversed(current_chunk_sentences):
                try:
                    s_tok = len(encoding.encode(s))
                except Exception:
                    s_tok = max(1, len(s) // 4)

                if overlap_tokens + s_tok > overlap_size:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += s_tok

            current_chunk_sentences = overlap_sentences
            current_chunk_tokens = overlap_tokens

        current_chunk_sentences.append(sentence)
        current_chunk_tokens += sentence_tokens

    # Append any remaining content as the final chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks
