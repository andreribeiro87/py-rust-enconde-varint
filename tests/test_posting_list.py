import pytest
import py_rust_encode_varint


class TestEncodePostingList:
    """Tests for encode_posting_list function."""
    
    def test_encode_empty(self):
        """Test encoding empty posting list."""
        result = py_rust_encode_varint.encode_posting_list([])
        assert result == b''
    
    def test_encode_single_posting(self):
        """Test encoding a single posting."""
        postings = [(5, 10, 3)]
        encoded = py_rust_encode_varint.encode_posting_list(postings)
        assert len(encoded) > 0
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_encode_multiple_postings(self):
        """Test encoding multiple postings."""
        postings = [(1, 5, 2), (3, 10, 4), (7, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_encode_unsorted_auto_sorts(self):
        """Test that unsorted postings are automatically sorted by default."""
        postings = [(7, 5, 2), (1, 10, 4), (3, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=False)
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        # Should be sorted by default sort keys (-1, -0): content_freq desc, then doc_id desc
        # So: (3, 15, 6), (1, 10, 4), (7, 5, 2)
        assert decoded == [(3, 15, 6), (1, 10, 4), (7, 5, 2)]
    
    def test_encode_assume_sorted(self):
        """Test that assume_sorted=True preserves order."""
        postings = [(7, 5, 2), (1, 10, 4), (3, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        # Should preserve original order
        assert decoded == postings
    
    def test_encode_large_values(self):
        """Test encoding postings with large values."""
        postings = [(1000000, 50000, 30000), (1000001, 50001, 30001)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_encode_zero_values(self):
        """Test encoding postings with zero values."""
        postings = [(0, 0, 0), (1, 0, 0), (2, 5, 0)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_invalid_posting_format(self):
        """Test that invalid posting format raises error."""
        # Wrong number of elements
        with pytest.raises(ValueError, match="3 integers"):
            py_rust_encode_varint.encode_posting_list([(1, 2)])
        
        with pytest.raises(ValueError, match="3 integers"):
            py_rust_encode_varint.encode_posting_list([(1, 2, 3, 4)])


class TestDecodePostingList:
    """Tests for decode_posting_list function."""
    
    def test_decode_empty(self):
        """Test decoding empty posting list."""
        result = py_rust_encode_varint.decode_posting_list(b'')
        assert result == []
    
    def test_decode_single_posting(self):
        """Test decoding a single posting."""
        # Encode a single posting: (5, 10, 3)
        encoded = py_rust_encode_varint.encode_posting_list([(5, 10, 3)], assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == [(5, 10, 3)]
    
    def test_decode_multiple_postings(self):
        """Test decoding multiple postings."""
        postings = [(1, 5, 2), (3, 10, 4), (7, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_decode_large_deltas(self):
        """Test decoding with large doc_id deltas."""
        postings = [(1, 5, 2), (1000, 10, 4), (100000, 15, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == postings
    
    def test_decode_invalid_data(self):
        """Test decoding invalid data raises error."""
        # Incomplete varint
        with pytest.raises(ValueError):
            py_rust_encode_varint.decode_posting_list(b'\x80')
        
        # Invalid varint (too many continuation bytes)
        with pytest.raises(ValueError):
            invalid_data = b'\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80\x80'
            py_rust_encode_varint.decode_posting_list(invalid_data)
