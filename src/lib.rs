use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};
use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Write};
use pyo3::wrap_pyfunction;
use std::borrow::Cow;
use pyo3::intern;

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
        let tuple: Bound<'_, PyTuple> = item.extract()?;
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
        postings_vec.sort_unstable_by_key(|x| (-x.1 - x.2, -x.1, -x.2, x.0));
    }

    // Pre-allocate buffer with estimated size
    let estimated_size = len * 15; // More conservative estimate
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
#[inline]
fn encode_varint_to_vec(result: &mut Vec<u8>, mut n: u64) {
    while n > 127 {
        result.push(((n & 0x7F) | 0x80) as u8);
        n >>= 7;
    }
    result.push((n & 0x7F) as u8);
}

/// Encode an integer using variable-length encoding (varint).
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

/// Decode varint from bytes slice, returns (value, bytes_consumed)
#[inline]
fn decode_varint(data: &[u8]) -> PyResult<(u64, usize)> {
    let mut result = 0u64;
    let mut shift = 0;

    for (i, &byte) in data.iter().enumerate() {
        if i >= 10 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Invalid varint encoding: too many bytes",
            ));
        }

        result |= ((byte & 0x7F) as u64) << shift;

        if (byte & 0x80) == 0 {
            return Ok((result, i + 1));
        }

        shift += 7;
    }

    Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
        "Invalid varint encoding: unexpected end of data",
    ))
}


#[pyfunction]
fn read_varint<'py>(py: Python<'py>, f: Bound<'py, PyAny>) -> PyResult<Option<u64>> {
    let mut result = 0u64;
    let mut shift = 0;
    let read_method = intern!(py, "read");

    loop {
        // Call Python's read(1) method - matches pyo3-file behavior
        let read_result = match f.call_method1(read_method, (1,)) {
            Ok(result) => result,
            Err(e) => {
                // If read() raises an exception, check if it's EOF-related
                if e.is_instance_of::<pyo3::exceptions::PyEOFError>(py) {
                    return Ok(None);
                }
                return Err(e);
            }
        };
        
        // Extract as bytes (handles both PyBytes and other byte-like objects)
        let bytes: Cow<[u8]> = match read_result.extract() {
            Ok(bytes) => bytes,
            Err(_) => {
                // If extraction fails, try to get bytes another way
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                    "read() must return bytes or bytearray",
                ));
            }
        };
        
        if bytes.is_empty() {
            // EOF reached
            return Ok(None);
        }
        
        let byte_val = bytes[0];
        result |= ((byte_val & 0x7F) as u64) << shift;
        if (byte_val & 0x80) == 0 {
            break;
        }
        shift += 7;
        if shift >= 35 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Invalid varint encoding: too many bytes",
            ));
        }
    }

    Ok(Some(result))
}

/// Decode a posting list from compressed bytes.
///
/// Args:
///     data: Compressed bytes representation of the posting list.
///
/// Returns:
///     List of (doc_id, content_freq, title_freq) tuples.
#[pyfunction]
fn decode_posting_list<'py>(py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyList>> {
    let mut postings = Vec::new();
    let mut pos = 0;
    let mut prev_doc_id = 0i32;

    while pos < data.len() {
        // Decode delta
        let (delta, consumed) = decode_varint(&data[pos..])?;
        pos += consumed;

        // Decode content_freq
        let (content_freq, consumed) = decode_varint(&data[pos..])?;
        pos += consumed;

        // Decode title_freq
        let (title_freq, consumed) = decode_varint(&data[pos..])?;
        pos += consumed;

        // Reconstruct doc_id from delta
        prev_doc_id += delta as i32;

        postings.push((prev_doc_id, content_freq as i32, title_freq as i32));
    }

    Ok(PyList::new(py, postings)?)
}

/// Read a term from a binary block file.
///
/// Args:
///     file_path: Path to the binary block file.
///     offset: Byte offset where the term starts.
///
/// Returns:
///     Tuple of (term, doc_freq_content, doc_freq_title, postings, next_offset)
///     or None if end of file.
#[pyfunction]
fn read_term_at_offset<'py>(
    py: Python<'py>,
    file_path: &str,
    offset: u64,
) -> PyResult<Option<Bound<'py, PyTuple>>> {
    let mut file = BufReader::new(File::open(file_path)?);

    // Seek to offset
    use std::io::Seek;
    file.seek(std::io::SeekFrom::Start(offset))?;

    // Read term length (4 bytes)
    let mut term_len_bytes = [0u8; 4];
    if file.read_exact(&mut term_len_bytes).is_err() {
        return Ok(None);
    }
    let term_len = u32::from_le_bytes(term_len_bytes) as usize;

    // Read term bytes
    let mut term_bytes = vec![0u8; term_len];
    file.read_exact(&mut term_bytes)?;
    let term = String::from_utf8(term_bytes).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid UTF-8: {}", e))
    })?;

    // Read varints into buffer for decoding
    let mut varint_buffer = vec![0u8; 128]; // Should be enough for 3 varints
    file.read_exact(&mut varint_buffer[..10])?; // Read at least enough for first varint

    let (doc_freq_content, consumed1) = decode_varint(&varint_buffer)?;
    let (doc_freq_title, consumed2) = decode_varint(&varint_buffer[consumed1..])?;
    let (posting_list_len, consumed3) = decode_varint(&varint_buffer[consumed1 + consumed2..])?;

    // Calculate actual bytes consumed for varints
    let total_varint_bytes = consumed1 + consumed2 + consumed3;

    // Read posting list data
    let mut posting_list_data = vec![0u8; posting_list_len as usize];
    file.read_exact(&mut posting_list_data)?;

    // Decode postings
    let postings = decode_posting_list(py, &posting_list_data)?;

    // Calculate next offset
    let next_offset = offset + 4 + term_len as u64 + total_varint_bytes as u64 + posting_list_len;

    let result_items = vec![
        term.into_pyobject(py)?.into_any(),
        doc_freq_content.into_pyobject(py)?.into_any(),
        doc_freq_title.into_pyobject(py)?.into_any(),
        postings.into_pyobject(py)?.into_any(),
        next_offset.into_pyobject(py)?.into_any(),
    ];
    let result = PyTuple::new(py, &result_items)?;

    Ok(Some(result))
}

/// Iterate over all terms in a binary block file.
///
/// Args:
///     file_path: Path to the binary block file.
///
/// Returns:
///     Iterator of (term, doc_freq_content, doc_freq_title, postings) tuples.
#[pyfunction]
fn iter_block_terms<'py>(py: Python<'py>, file_path: &str) -> PyResult<Bound<'py, PyList>> {
    let mut file = BufReader::new(File::open(file_path)?);

    // Read header (num_terms)
    let mut num_terms_bytes = [0u8; 8];
    file.read_exact(&mut num_terms_bytes)?;
    let num_terms = u64::from_le_bytes(num_terms_bytes);

    let mut results = Vec::with_capacity(num_terms as usize);

    for _ in 0..num_terms {
        // Read term length
        let mut term_len_bytes = [0u8; 4];
        if file.read_exact(&mut term_len_bytes).is_err() {
            break;
        }
        let term_len = u32::from_le_bytes(term_len_bytes) as usize;

        // Read term
        let mut term_bytes = vec![0u8; term_len];
        file.read_exact(&mut term_bytes)?;
        let term = String::from_utf8(term_bytes).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid UTF-8: {}", e))
        })?;

        // Read varints (doc_freq_content, doc_freq_title, posting_list_len)
        let mut varint_buffer = vec![0u8; 64];
        file.read_exact(&mut varint_buffer[..20])?;

        let (doc_freq_content, consumed1) = decode_varint(&varint_buffer)?;
        let (doc_freq_title, consumed2) = decode_varint(&varint_buffer[consumed1..])?;
        let (posting_list_len, _) = decode_varint(&varint_buffer[consumed1 + consumed2..])?;

        // Read posting list
        let mut posting_list_data = vec![0u8; posting_list_len as usize];
        file.read_exact(&mut posting_list_data)?;

        let postings = decode_posting_list(py, &posting_list_data)?;

        let tuple_items = vec![
            term.into_pyobject(py)?.into_any(),
            doc_freq_content.into_pyobject(py)?.into_any(),
            doc_freq_title.into_pyobject(py)?.into_any(),
            postings.into_pyobject(py)?.into_any(),
        ];
        let result = PyTuple::new(py, &tuple_items)?;

        results.push(result);
    }

    Ok(PyList::new(py, results)?)
}

/// Merge and sort multiple compressed posting lists efficiently.
///
/// Takes multiple compressed posting list bytes, decodes them, merges them,
/// sorts by content_freq + title_freq descending, then content_freq descending,
/// then doc_id descending, and returns a single compressed posting list.
///
/// Args:
///     postings_bytes_list: List of compressed posting list bytes.
///
/// Returns:
///     Single compressed bytes representation of merged and sorted postings.
#[pyfunction]
#[pyo3(signature = (postings_bytes_list))]
fn merge_posting_lists(
    postings_bytes_list: Bound<'_, PyList>,
) -> PyResult<Vec<u8>> {
    if postings_bytes_list.len() == 0 {
        return Ok(Vec::new());
    }

    // Collect all decoded postings
    let mut all_postings: Vec<(i32, i32, i32)> = Vec::new();

    // Decode all posting lists into a single vec
    for item in postings_bytes_list.iter() {
        // Extract bytes from Python bytes object
        let posting_bytes: &[u8] = item.extract()?;
        
        let mut pos = 0;
        let mut prev_doc_id = 0i32;

        while pos < posting_bytes.len() {
            // Decode delta
            let (delta, consumed) = decode_varint(&posting_bytes[pos..])?;
            pos += consumed;

            // Decode content_freq
            let (content_freq, consumed) = decode_varint(&posting_bytes[pos..])?;
            pos += consumed;

            // Decode title_freq
            let (title_freq, consumed) = decode_varint(&posting_bytes[pos..])?;
            pos += consumed;

            // Reconstruct doc_id from delta
            prev_doc_id += delta as i32;
            all_postings.push((prev_doc_id, content_freq as i32, title_freq as i32));
        }
    }

    // Sort the merged postings
    all_postings.sort_unstable_by_key(|x| (-x.1 - 4 * x.2, -x.1, -x.2, x.0));

    // Encode back to compressed format
    let mut result = Vec::with_capacity(all_postings.len() * 15);
    let mut prev_doc_id = 0i32;

    for (doc_id, content_freq, title_freq) in all_postings {
        // Delta encode document ID
        let delta = doc_id - prev_doc_id;
        prev_doc_id = doc_id;

        // Encode varints
        encode_varint_to_vec(&mut result, delta as u64);
        encode_varint_to_vec(&mut result, content_freq as u64);
        encode_varint_to_vec(&mut result, title_freq as u64);
    }

    Ok(result)
}


/// Write a binary block from dictionaries.
///
/// Args:
///     terms: List of terms (sorted).
///     doc_freqs: List of (doc_freq_content, doc_freq_title) tuples.
///     postings: List of posting lists (each is a list of (doc_id, content_freq, title_freq)).
///     output_path: Path to output binary block file.
#[pyfunction]
fn write_binary_block(
    terms: Vec<String>,
    doc_freqs: Vec<(u64, u64)>,
    postings: Vec<Vec<(i32, i32, i32)>>,
    output_path: &str,
) -> PyResult<()> {
    if terms.len() != doc_freqs.len() || terms.len() != postings.len() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "terms, doc_freqs, and postings must have the same length",
        ));
    }

    let mut file = BufWriter::new(File::create(output_path)?);

    // Write header (num_terms)
    file.write_all(&(terms.len() as u64).to_le_bytes())?;

    // Write each term
    for i in 0..terms.len() {
        let term = &terms[i];
        let (doc_freq_content, doc_freq_title) = doc_freqs[i];
        let posting_list = &postings[i];

        // Write term length and bytes
        let term_bytes = term.as_bytes();
        file.write_all(&(term_bytes.len() as u32).to_le_bytes())?;
        file.write_all(term_bytes)?;

        // Write doc frequencies
        let mut varint_buf = Vec::new();
        encode_varint_to_vec(&mut varint_buf, doc_freq_content);
        encode_varint_to_vec(&mut varint_buf, doc_freq_title);

        // Encode posting list
        let mut encoded_postings = Vec::new();
        let mut prev_doc_id = 0i32;
        for &(doc_id, content_freq, title_freq) in posting_list {
            let delta = doc_id - prev_doc_id;
            prev_doc_id = doc_id;
            encode_varint_to_vec(&mut encoded_postings, delta as u64);
            encode_varint_to_vec(&mut encoded_postings, content_freq as u64);
            encode_varint_to_vec(&mut encoded_postings, title_freq as u64);
        }

        // Write posting list length
        encode_varint_to_vec(&mut varint_buf, encoded_postings.len() as u64);

        file.write_all(&varint_buf)?;
        file.write_all(&encoded_postings)?;
    }

    file.flush()?;
    Ok(())
}

/// Get block statistics without loading all data.
///
/// Args:
///     file_path: Path to the binary block file.
///
/// Returns:
///     Tuple of (num_terms, file_size_bytes).
#[pyfunction]
fn get_block_stats(file_path: &str) -> PyResult<(u64, u64)> {
    let file = File::open(file_path)?;
    let file_size = file.metadata()?.len();

    let mut reader = BufReader::new(file);
    let mut num_terms_bytes = [0u8; 8];
    reader.read_exact(&mut num_terms_bytes)?;
    let num_terms = u64::from_le_bytes(num_terms_bytes);

    Ok((num_terms, file_size))
}

#[pymodule]
fn py_rust_encode_varint(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.3.7")?;
    m.add("__author__", "André Ribeiro & Rúben Garrido")?;
    m.add("__email__", "andrepedoribeiro04@gmail.com & rubentavaresgarrido@gmail.com")?;
    m.add("__package__", "py_rust_encode_varint")?;
    m.add("__all_functions__", ["encode_posting_list", "encode_varint", "decode_posting_list", "read_term_at_offset", "iter_block_terms", "write_binary_block", "get_block_stats", "merge_posting_lists", "read_varint"])?;

    m.add_function(wrap_pyfunction!(encode_posting_list, m)?)?;
    m.add_function(wrap_pyfunction!(encode_varint, m)?)?;
    m.add_function(wrap_pyfunction!(decode_posting_list, m)?)?;
    m.add_function(wrap_pyfunction!(read_term_at_offset, m)?)?;
    m.add_function(wrap_pyfunction!(iter_block_terms, m)?)?;
    m.add_function(wrap_pyfunction!(write_binary_block, m)?)?;
    m.add_function(wrap_pyfunction!(get_block_stats, m)?)?;
    m.add_function(wrap_pyfunction!(merge_posting_lists, m)?)?;
    m.add_function(wrap_pyfunction!(read_varint, m)?)?;
    Ok(())
}
