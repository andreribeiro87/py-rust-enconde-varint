"""Type stubs for py_rust_encode_varint module."""

def encode_posting_list(
    postings: list[tuple[int, int, int]],
    assume_sorted: bool = False,
    sort_keys: str | None = "(-1, -0)"
) -> bytes:
    """
    Encode a posting list using delta encoding and varint compression.
    
    Postings are sorted by document ID and delta-encoded:
    - First doc_id is stored as-is
    - Subsequent doc_ids are stored as deltas
    
    Args:
        postings: List of (doc_id, content_freq, title_freq) tuples.
        assume_sorted: If True, skip sorting (postings already sorted by doc_id).
        sort_keys: Optional sort key specification string. Format: "(field0, field1, ...)" 
                   where field can be:
                   - "0" for doc_id (ascending)
                   - "1" for content_freq (ascending)
                   - "2" for title_freq (ascending)
                   - "-0" for doc_id (descending)
                   - "-1" for content_freq (descending)
                   - "-2" for title_freq (descending)
                   Default: "(-1, -0)" sorts by content_freq descending, then doc_id descending.
    
    Returns:
        Compressed bytes representation of the posting list.
    """
    ...

def encode_varint(n: int) -> bytes:
    """
    Encode an integer using variable-length encoding (varint).
    
    Varint encoding uses 1-5 bytes depending on the value.
    
    Args:
        n: Non-negative integer to encode.
    
    Returns:
        Bytes representation of the encoded varint.
    
    Raises:
        ValueError: If n is negative.
    """
    ...

def decode_posting_list(data: bytes) -> list[tuple[int, int, int]]:
    """
    Decode a posting list from compressed bytes.
    
    Args:
        data: Compressed bytes representation of the posting list.
    
    Returns:
        List of (doc_id, content_freq, title_freq) tuples.
    
    Raises:
        ValueError: If data contains invalid varint encoding.
    """
    ...

def read_term_at_offset(
    file_path: str,
    offset: int
) -> tuple[str, int, int, list[tuple[int, int, int]], int] | None:
    """
    Read a term from a binary block file at a specific offset.
    
    Args:
        file_path: Path to the binary block file.
        offset: Byte offset where the term starts.
    
    Returns:
        Tuple of (term, doc_freq_content, doc_freq_title, postings, next_offset)
        or None if end of file reached.
        
    Raises:
        IOError: If file cannot be read.
        ValueError: If data is malformed.
    """
    ...

def iter_block_terms(
    file_path: str
) -> list[tuple[str, int, int, list[tuple[int, int, int]]]]:
    """
    Iterate over all terms in a binary block file.
    
    More efficient than repeated read_term_at_offset calls as it reads
    sequentially through the file.
    
    Args:
        file_path: Path to the binary block file.
    
    Returns:
        List of (term, doc_freq_content, doc_freq_title, postings) tuples.
    
    Raises:
        IOError: If file cannot be read.
        ValueError: If data is malformed.
    """
    ...

def write_binary_block(
    terms: list[str],
    doc_freqs: list[tuple[int, int]],
    postings: list[list[tuple[int, int, int]]],
    output_path: str
) -> None:
    """
    Write a binary block from dictionaries.
    
    Args:
        terms: List of terms (must be sorted alphabetically).
        doc_freqs: List of (doc_freq_content, doc_freq_title) tuples.
        postings: List of posting lists, where each posting list contains
                  (doc_id, content_freq, title_freq) tuples.
        output_path: Path to output binary block file.
    
    Raises:
        ValueError: If terms, doc_freqs, and postings have different lengths.
        IOError: If file cannot be written.
    """
    ...

def get_block_stats(file_path: str) -> tuple[int, int]:
    """
    Get block statistics without loading all data.
    
    Fast operation that only reads the file header and metadata.
    
    Args:
        file_path: Path to the binary block file.
    
    Returns:
        Tuple of (num_terms, file_size_bytes).
    
    Raises:
        IOError: If file cannot be read.
    """
    ...