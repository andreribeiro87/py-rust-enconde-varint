import py_rust_encode_varint


class TestRoundTrip:
    """Tests for round-trip encoding and decoding."""
    
    def test_round_trip_single(self):
        """Test round-trip encoding/decoding of single posting."""
        original = [(42, 10, 5)]
        encoded = py_rust_encode_varint.encode_posting_list(original, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == original
    
    def test_round_trip_multiple(self):
        """Test round-trip encoding/decoding of multiple postings."""
        original = [(1, 5, 2), (3, 10, 4), (7, 15, 6), (20, 25, 30)]
        encoded = py_rust_encode_varint.encode_posting_list(original, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == original
    
    def test_round_trip_with_sorting(self):
        """Test round-trip with automatic sorting."""
        original = [(7, 15, 2), (1, 5, 4), (3, 10, 6)]
        encoded = py_rust_encode_varint.encode_posting_list(
            original,
            assume_sorted=False,
            sort_keys="(0)"  # Sort by doc_id asc
        )
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        # Should be sorted by doc_id
        assert decoded == [(1, 5, 4), (3, 10, 6), (7, 15, 2)]
    
    def test_round_trip_large_values(self):
        """Test round-trip with large values."""
        original = [
            (1000000, 50000, 30000),
            (1000001, 50001, 30001),
            (1000002, 50002, 30002),
        ]
        encoded = py_rust_encode_varint.encode_posting_list(original, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == original
    
    def test_round_trip_many_postings(self):
        """Test round-trip with many postings."""
        original = [(i, i * 2, i * 3) for i in range(100)]
        encoded = py_rust_encode_varint.encode_posting_list(original, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == original
    
    def test_round_trip_with_zero_doc_id(self):
        """Test round-trip with zero doc_id."""
        original = [(0, 5, 2), (1, 10, 4)]
        encoded = py_rust_encode_varint.encode_posting_list(original, assume_sorted=True)
        decoded = py_rust_encode_varint.decode_posting_list(encoded)
        assert decoded == original
