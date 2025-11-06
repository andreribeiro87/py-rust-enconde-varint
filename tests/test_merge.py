import py_rust_encode_varint


class TestMergePostingLists:
    """Tests for merge_posting_lists function."""
    
    def test_merge_empty(self):
        """Test merging empty list."""
        result = py_rust_encode_varint.merge_posting_lists([])
        assert result == b''
    
    def test_merge_single_list(self):
        """Test merging single posting list."""
        postings = [(1, 5, 2), (3, 10, 4)]
        encoded = py_rust_encode_varint.encode_posting_list(postings, assume_sorted=True)
        
        merged = py_rust_encode_varint.merge_posting_lists([encoded])
        decoded = py_rust_encode_varint.decode_posting_list(merged)
        # merge_posting_lists sorts by default keys (-1, -0): content_freq desc, doc_id desc
        expected = sorted(postings, key=lambda x: (-x[1], -x[0]))
        assert decoded == expected
    
    def test_merge_multiple_lists(self):
        """Test merging multiple posting lists."""
        list1 = [(1, 5, 2), (3, 10, 4)]
        list2 = [(5, 15, 6), (7, 20, 8)]
        list3 = [(2, 8, 3)]
        
        encoded1 = py_rust_encode_varint.encode_posting_list(list1, assume_sorted=True)
        encoded2 = py_rust_encode_varint.encode_posting_list(list2, assume_sorted=True)
        encoded3 = py_rust_encode_varint.encode_posting_list(list3, assume_sorted=True)
        
        merged = py_rust_encode_varint.merge_posting_lists([encoded1, encoded2, encoded3])
        decoded = py_rust_encode_varint.decode_posting_list(merged)
        
        # Should be merged and sorted by default keys (-1, -0)
        all_postings = list1 + list2 + list3
        # Sort by content_freq desc, then doc_id desc
        expected = sorted(all_postings, key=lambda x: (-x[1], -x[0]))
        assert decoded == expected
    
    def test_merge_with_duplicates(self):
        """Test merging lists with duplicate doc_ids."""
        list1 = [(1, 5, 2), (3, 10, 4)]
        list2 = [(1, 8, 3), (5, 15, 6)]  # doc_id 1 appears in both
        
        encoded1 = py_rust_encode_varint.encode_posting_list(list1, assume_sorted=True)
        encoded2 = py_rust_encode_varint.encode_posting_list(list2, assume_sorted=True)
        
        merged = py_rust_encode_varint.merge_posting_lists([encoded1, encoded2])
        decoded = py_rust_encode_varint.decode_posting_list(merged)
        
        # Both instances of doc_id 1 should be present
        all_postings = list1 + list2
        expected = sorted(all_postings, key=lambda x: (-x[1], -x[0]))
        assert decoded == expected
    
    def test_merge_with_custom_sort(self):
        """Test merging with custom sort keys."""
        list1 = [(7, 5, 2), (1, 10, 4)]
        list2 = [(3, 15, 6), (5, 8, 3)]
        
        encoded1 = py_rust_encode_varint.encode_posting_list(list1, assume_sorted=True)
        encoded2 = py_rust_encode_varint.encode_posting_list(list2, assume_sorted=True)
        
        merged = py_rust_encode_varint.merge_posting_lists(
            [encoded1, encoded2],
            sort_keys="(0)"  # Sort by doc_id ascending
        )
        decoded = py_rust_encode_varint.decode_posting_list(merged)
        
        all_postings = list1 + list2
        expected = sorted(all_postings, key=lambda x: x[0])
        assert decoded == expected
    
    def test_merge_large_lists(self):
        """Test merging large posting lists."""
        list1 = [(i, i * 2, i * 3) for i in range(0, 50, 2)]
        list2 = [(i, i * 2, i * 3) for i in range(1, 50, 2)]
        
        encoded1 = py_rust_encode_varint.encode_posting_list(list1, assume_sorted=True)
        encoded2 = py_rust_encode_varint.encode_posting_list(list2, assume_sorted=True)
        
        merged = py_rust_encode_varint.merge_posting_lists([encoded1, encoded2])
        decoded = py_rust_encode_varint.decode_posting_list(merged)
        
        all_postings = list1 + list2
        expected = sorted(all_postings, key=lambda x: (-x[1], -x[0]))
        assert decoded == expected
