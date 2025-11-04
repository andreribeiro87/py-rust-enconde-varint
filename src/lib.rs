use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

/// Encode a posting list using delta encoding and varint compression.
///
/// Postings are sorted by document ID and delta-encoded:
/// - First doc_id is stored as-is
/// - Subsequent doc_ids are stored as deltas
///
/// Args:
///     postings: List of (doc_id, content_freq, title_freq) tuples.
///     assume_sorted: If True, skip sorting (postings already sorted by doc_id).
///
/// Returns:
///     Compressed bytes representation of the posting list.
#[pyfunction]
#[pyo3(signature = (postings, assume_sorted=false))]
fn encode_posting_list(
    postings: Bound<'_, PyList>,
    assume_sorted: bool,
) -> PyResult<Vec<u8>> {
    let len = postings.len();
    if len == 0 {
        return Ok(Vec::new());
    }

    // Convert Python list to Rust Vec<(i32, i32, i32)>
    let mut postings_vec: Vec<(i32, i32, i32)> = Vec::with_capacity(len);
    for item in postings.iter() {
        let tuple = item.downcast::<PyTuple>()?;
        if tuple.len() != 3 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Posting must be a tuple of 3 integers",
            ));
        }
        let doc_id: i32 = tuple.get_item(0)?.extract()?;
        let content_freq: i32 = tuple.get_item(1)?.extract()?;
        let title_freq: i32 = tuple.get_item(2)?.extract()?;
        postings_vec.push((doc_id, content_freq, title_freq));
    }

    // Sort if needed
    if !assume_sorted {
        postings_vec.sort_by_key(|x| x.0);
    }

    // Pre-allocate buffer with estimated size
    // Each posting: ~3-15 bytes (varint) * 3 fields = ~9-45 bytes per posting
    // Add some headroom
    let estimated_size = len * 50;
    let mut result = Vec::with_capacity(estimated_size);
    let mut prev_doc_id = 0i32;

    for (doc_id, content_freq, title_freq) in postings_vec {
        // Delta encode document ID
        let delta = doc_id - prev_doc_id;
        prev_doc_id = doc_id;

        // Encode varints using Protocol Buffers format (same as Python)
        encode_varint_to_vec(&mut result, delta as u64);
        encode_varint_to_vec(&mut result, content_freq as u64);
        encode_varint_to_vec(&mut result, title_freq as u64);
    }

    Ok(result)
}

/// Encode varint using Protocol Buffers format (same as Python implementation).
/// This matches the Python implementation exactly.
fn encode_varint_to_vec(result: &mut Vec<u8>, mut n: u64) {
    while n > 127 {
        result.push(((n & 0x7F) | 0x80) as u8);
        n >>= 7;
    }
    result.push((n & 0x7F) as u8);
}

/// Encode an integer using variable-length encoding (varint).
///
/// Varint encoding uses 1-5 bytes depending on the value.
#[pyfunction]
fn encode_varint(n: i64) -> PyResult<Vec<u8>> {
    if n < 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Varint encoding only supports non-negative integers",
        ));
    }
    
    let mut result = Vec::new();
    encode_varint_to_vec(&mut result, n as u64);
    Ok(result)
}

/// A Python module implemented in Rust.
#[pymodule]
fn py_rust_encode_varint(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode_posting_list, m)?)?;
    m.add_function(wrap_pyfunction!(encode_varint, m)?)?;
    Ok(())
}

