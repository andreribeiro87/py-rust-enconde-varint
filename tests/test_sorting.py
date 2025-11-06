import pytest
import py_rust_encode_varint


class TestSorting:
    """Tests for sorting functionality with different sort keys."""
    
    def test_sort_by_doc_id_ascending(self):
        """Test sorting by doc_id ascending."""
        postings = [(7, 5, 2), (1, 10, 4), (3, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings, 
            assume_sorted=False, 
            sort_keys="(0)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(1, 10, 4), (3, 15, 6), (7, 5, 2)]
    
    def test_sort_by_doc_id_descending(self):
        """Test sorting by doc_id descending."""
        postings = [(1, 5, 2), (3, 10, 4), (7, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(-0)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(7, 15, 6), (3, 10, 4), (1, 5, 2)]
    
    def test_sort_by_content_freq_ascending(self):
        """Test sorting by content_freq ascending."""
        postings = [(7, 15, 2), (1, 5, 4), (3, 10, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(1)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(1, 5, 4), (3, 10, 6), (7, 15, 2)]
    
    def test_sort_by_content_freq_descending(self):
        """Test sorting by content_freq descending."""
        postings = [(1, 5, 2), (3, 15, 4), (7, 10, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(-1)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(3, 15, 4), (7, 10, 6), (1, 5, 2)]
    
    def test_sort_by_title_freq_ascending(self):
        """Test sorting by title_freq ascending."""
        postings = [(7, 5, 15), (1, 10, 5), (3, 15, 10)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(2)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(1, 10, 5), (3, 15, 10), (7, 5, 15)]
    
    def test_sort_by_title_freq_descending(self):
        """Test sorting by title_freq descending."""
        postings = [(1, 5, 5), (3, 10, 15), (7, 15, 10)]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(-2)"
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(3, 10, 15), (7, 15, 10), (1, 5, 5)]
    
    def test_sort_multi_key_default(self):
        """Test default multi-key sort (content_freq desc, doc_id desc)."""
        postings = [
            (1, 10, 5),
            (5, 10, 5),  # Same content_freq, different doc_id
            (3, 15, 10),
            (2, 10, 5),  # Same content_freq, different doc_id
        ]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(-1, -0)"  # Default
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        # First by content_freq desc: 15, then 10s
        # Then by doc_id desc for ties
        assert decoded == [
            (3, 15, 10),   # Highest content_freq
            (5, 10, 5),    # Same content_freq, highest doc_id
            (2, 10, 5),    # Same content_freq, middle doc_id
            (1, 10, 5),    # Same content_freq, lowest doc_id
        ]
    
    def test_sort_multi_key_custom(self):
        """Test custom multi-key sort."""
        postings = [
            (1, 10, 20),
            (2, 15, 20),  # Same title_freq, different content_freq
            (3, 15, 10),
            (4, 10, 10),
        ]
        encoded = py_rust_encode_varint.encode_posting_list(
            postings,
            assume_sorted=False,
            sort_keys="(2, 1)"  # title_freq asc, then content_freq asc
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        # First by title_freq asc: 10, then 20
        # Then by content_freq asc for ties
        assert decoded == [
            (4, 10, 10),   # Lowest title_freq, lowest content_freq
            (3, 15, 10),   # Lowest title_freq, higher content_freq
            (1, 10, 20),   # Higher title_freq, lower content_freq
            (2, 15, 20),   # Higher title_freq, higher content_freq
        ]
    
    def test_sort_keys_invalid_format(self):
        """Test that invalid sort keys format raises error."""
        postings = [(1, 5, 2), (3, 10, 4)]
        
        # Not a tuple
        with pytest.raises(ValueError):
            py_rust_encode_varint.encode_posting_list(
                postings,
                sort_keys="1, 0"
            )
        
        # Invalid field index
        with pytest.raises(ValueError):
            py_rust_encode_varint.encode_posting_list(
                postings,
                sort_keys="(3)"
            )
        
        # Empty sort keys
        with pytest.raises(ValueError):
            py_rust_encode_varint.encode_posting_list(
                postings,
                sort_keys="()"
            )
