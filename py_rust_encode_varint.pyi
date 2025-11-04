"""Type stubs for py_rust_encode_varint module."""

def encode_posting_list(
    postings: list[tuple[int, int, int]],
    assume_sorted: bool = False
) -> bytes:
    """
    Encode a posting list using delta encoding and varint compression.
    
    Postings are sorted by document ID and delta-encoded:
    - First doc_id is stored as-is
    - Subsequent doc_ids are stored as deltas
    
    Args:
        postings: List of (doc_id, content_freq, title_freq) tuples.
        assume_sorted: If True, skip sorting (postings already sorted by doc_id).
    
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

