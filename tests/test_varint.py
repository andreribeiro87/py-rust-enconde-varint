import pytest
import py_rust_encode_varint


class TestEncodeVarint:
    """Tests for encode_varint function."""
    
    def test_encode_zero(self):
        """Test encoding zero."""
        result = py_rust_encode_varint.encode_varint(0)
        assert result == b'\x00'
    
    def test_encode_small_numbers(self):
        """Test encoding small numbers (< 128)."""
        assert py_rust_encode_varint.encode_varint(1) == b'\x01'
        assert py_rust_encode_varint.encode_varint(127) == b'\x7f'
    
    def test_encode_medium_numbers(self):
        """Test encoding medium numbers (128-16383)."""
        # 128 = 0x80
        result = py_rust_encode_varint.encode_varint(128)
        assert len(result) == 2
        assert result == b'\x80\x01'
        
        # 300 = 0x12C = 0xAC in 7-bit chunks: 0xAC | 0x80, 0x02
        result = py_rust_encode_varint.encode_varint(300)
        assert len(result) == 2
        assert result[0] == 0xAC
        assert result[1] == 0x02
    
    def test_encode_large_numbers(self):
        """Test encoding large numbers."""
        # Test a few larger numbers
        result = py_rust_encode_varint.encode_varint(16384)
        assert len(result) >= 2
        
        result = py_rust_encode_varint.encode_varint(1000000)
        assert len(result) >= 2
    
    def test_encode_negative_raises_error(self):
        """Test that encoding negative numbers raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            py_rust_encode_varint.encode_varint(-1)
        
        with pytest.raises(ValueError, match="non-negative"):
            py_rust_encode_varint.encode_varint(-100)
