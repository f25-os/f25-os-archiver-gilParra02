#!/usr/bin/env python3
import os
import sys
import struct

def write_all(fd, data):
    while data:
        written = os.write(fd, data)
        data = data[written:]

def read_exact(fd, size):
    chunks = []
    while size > 0:
        chunk = os.read(fd, size)
        if not chunk:
            raise RuntimeError("Unexpected EOF")
        chunks.append(chunk)
        size -= len(chunk)
    return b''.join(chunks)

def create(files):
    for fname in files:
        try:
            fd = os.open(fname, os.O_RDONLY)
            size = os.fstat(fd).st_size
            encoded_name = fname.encode()
            write_all(sys.stdout.fileno(), struct.pack('>I', len(encoded_name)))
            write_all(sys.stdout.fileno(), encoded_name)
            write_all(sys.stdout.fileno(), struct.pack('>Q', size))
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                write_all(sys.stdout.fileno(), chunk)
            os.close(fd)
        except Exception as e:
            os.write(sys.stderr.fileno(), f"Error reading {fname}: {e}\n".encode())

def extract():
    fd_in = sys.stdin.fileno()
    while True:
        try:
            raw_len = os.read(fd_in, 4)
            if not raw_len:
                break  # EOF
            name_len = struct.unpack('>I', raw_len)[0]
            fname = read_exact(fd_in, name_len).decode()
            size = struct.unpack('>Q', read_exact(fd_in, 8))[0]
            fd_out = os.open(fname, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            remaining = size
            while remaining > 0:
                chunk = os.read(fd_in, min(4096, remaining))
                if not chunk:
                    raise RuntimeError("Unexpected EOF during file content")
                write_all(fd_out, chunk)
                remaining -= len(chunk)
            os.close(fd_out)
        except Exception as e:
            os.write(sys.stderr.fileno(), f"Error extracting: {e}\n".encode())
            break

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ['c', 'x']:
        os.write(sys.stderr.fileno(), b"Usage: mytar.py c [files...] | mytar.py x\n")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == 'c':
        create(sys.argv[2:])
    else:
        extract()

