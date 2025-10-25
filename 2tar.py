#!/usr/bin/env python3
import os
import sys
import struct

def write_all(fd, data):
    """Write all data, handling partial writes"""
    while data:
        written = os.write(fd, data)
        data = data[written:]

def read_exact(fd, size):
    """Read exactly size bytes"""
    chunks = []
    while size > 0:
        chunk = os.read(fd, size)
        if not chunk:
            raise RuntimeError("Unexpected EOF")
        chunks.append(chunk)
        size -= len(chunk)
    return b''.join(chunks)

def create_archive(files):
    """Create archive containing the specified files"""
    for fname in files:
        try:
            # Get file metadata
            stat = os.stat(fname)
            encoded_name = fname.encode('utf-8')
            
            # Write header: name_len(4), name, size(8), mode(4), mtime(8)
            write_all(sys.stdout.fileno(), struct.pack('>I', len(encoded_name)))
            write_all(sys.stdout.fileno(), encoded_name)
            write_all(sys.stdout.fileno(), struct.pack('>Q', stat.st_size))
            write_all(sys.stdout.fileno(), struct.pack('>I', stat.st_mode))
            write_all(sys.stdout.fileno(), struct.pack('>Q', int(stat.st_mtime)))
            
            # Write file content
            with open(fname, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    write_all(sys.stdout.fileno(), chunk)
                    
        except Exception as e:
            sys.stderr.write(f"Error reading {fname}: {e}\n")
            sys.stderr.flush()
    
    # Write end-of-archive marker
    write_all(sys.stdout.fileno(), struct.pack('>I', 0))

def extract_archive():
    """Extract files from archive on stdin"""
    fd = sys.stdin.fileno()
    
    while True:
        try:
            # Read name length
            name_len_data = read_exact(fd, 4)
            name_len = struct.unpack('>I', name_len_data)[0]
            
            # End-of-archive marker
            if name_len == 0:
                break
                
            # Read filename
            name_data = read_exact(fd, name_len)
            filename = name_data.decode('utf-8')
            
            # Read file metadata
            size_data = read_exact(fd, 8)
            size = struct.unpack('>Q', size_data)[0]
            
            mode_data = read_exact(fd, 4)
            mode = struct.unpack('>I', mode_data)[0]
            
            mtime_data = read_exact(fd, 8)
            mtime = struct.unpack('>Q', mtime_data)[0]
            
            # Extract file
            print(f"Extracting: {filename} ({size} bytes)")
            
            # Check if file exists and warn
            if os.path.exists(filename):
                sys.stderr.write(f"Warning: overwriting {filename}\n")
                sys.stderr.flush()
            
            # Write file content
            with open(filename, 'wb') as f:
                remaining = size
                while remaining > 0:
                    chunk_size = min(4096, remaining)
                    chunk = read_exact(fd, chunk_size)
                    f.write(chunk)
                    remaining -= len(chunk)
            
            # Restore metadata
            os.chmod(filename, mode)
            os.utime(filename, (mtime, mtime))
            
        except Exception as e:
            sys.stderr.write(f"Error extracting file: {e}\n")
            sys.stderr.flush()
            break

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: mytar.py c|x [files...]\n")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == 'c':
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: mytar.py c file1 [file2...]\n")
            sys.exit(1)
        create_archive(sys.argv[2:])
        
    elif mode == 'x':
        if len(sys.argv) > 2:
            sys.stderr.write("Warning: extra arguments ignored for extract mode\n")
        extract_archive()
        
    else:
        sys.stderr.write(f"Unknown mode: {mode}. Use 'c' or 'x'\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
