import os
import datetime
import stat
from PIL import Image
from PIL.ExifTags import TAGS
import struct

IMAGE_SIGNATURES = {
    b'\x89PNG\r\n\x1a\n': "PNG",
    b'\xff\xd8\xff': "JPEG",
    b'GIF87a': "GIF",
    b'GIF89a': "GIF",
    b'BM': "BMP",
}

def detect_format(file_path):
    with open(file_path, "rb") as f:
        header = f.read(8)

    for sig, fmt in IMAGE_SIGNATURES.items():
        if header.startswith(sig):
            return fmt
    return "Unknown"


def analyse_file(file_path):
    stats = os.stat(file_path)

    permissions = stat.filemode(stats.st_mode)

    file_format = detect_format(file_path)

    return {
        "file name": os.path.basename(file_path),
        "absolute_path": os.path.abspath(file_path),
        "file_size_bytes": stats.st_size,
        "file_size_kb": round(stats.st_size / 1024, 2),
        "creation_time": datetime.datetime.fromtimestamp(stats.st_birthtime),
        "modified_time": datetime.datetime.fromtimestamp(stats.st_mtime),
        "access_time": datetime.datetime.fromtimestamp(stats.st_atime),
        "permissions": permissions,
        "detected_format": file_format,
        "extension": os.path.splitext(file_path)[1],
        "extension_match": file_format.lower() in os.path.splitext(file_path)[1].lower()
    }



def extr_exif(image_path):
    data = {}
    try:
        img = Image.open(image_path)
        exif = img._getexif()

        if exif is not None:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                data[tag] = value
        else:
            data["Info"] = "No EXIF metadata found."

    except Exception as e:
        data["Error"] = str(e)
    

    return data


def byte_anal(path):
    report = {}

    with open(path, "rb") as f:
        header = f.read(10)

    file_size = os.path.getsize(path)
    report["Total File Size (bytes)"] = file_size
    # PNG ANALYSIS
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        report["Format Detected"] = "PNG"

        chunk_counts = {}
        essential_chunks = ["IHDR", "PLTE", "IDAT", "IEND"]
        essential_size = 0
        ancillary_size = 0

        with open(path, "rb") as f:
            f.read(8)#sign header

            while True:
                length_bytes = f.read(4)
                if not length_bytes:
                    break

                length = struct.unpack(">I", length_bytes)[0]
                chunk_type = f.read(4).decode()
                f.read(length)
                f.read(4)#CRC

                chunk_counts[chunk_type] = chunk_counts.get(chunk_type, 0) + 1

                if chunk_type in essential_chunks:
                    essential_size += length
                else:
                    ancillary_size += length

        report["Chunk Types"] = chunk_counts
        report["Essential Data %"] = round((essential_size / file_size) * 100, 2)
        report["Ancillary Data %"] = round((ancillary_size / file_size) * 100, 2)
    
    # JPEG ANALYSIS
    elif header.startswith(b'\xff\xd8'):
        report["Format Detected"] = "JPEG"

        marker_counts = {}
        segment_size_total = 0

        with open(path, "rb") as f:
            f.read(2)  # Skip SOI

            while True:
                byte = f.read(1)
                if not byte:
                    break

                if byte == b'\xff':
                    marker = f.read(1)
                    if marker == b'\xd9':  # EOI
                        break

                    marker_name = f"FF{marker.hex().upper()}"
                    marker_counts[marker_name] = marker_counts.get(marker_name, 0) + 1

                    length_bytes = f.read(2)
                    if len(length_bytes) != 2:
                        break

                    length = struct.unpack(">H", length_bytes)[0]
                    f.read(length - 2)
                    segment_size_total += length

        report["Markers Found"] = marker_counts
        report["Segment Data %"] = round((segment_size_total / file_size) * 100, 2)
    # GIF ANALYSIS
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        report["Format Detected"] = "GIF"

        with open(path, "rb") as f:
            f.read(6)  # signature
            logical_screen = f.read(7)

        report["GIF Version"] = header[:6].decode()
        report["Header Size (bytes)"] = 13
        report["Remaining Data Size (bytes)"] = file_size - 13
    # BMP ANALYSIS
    elif header.startswith(b'BM'):
        report["Format Detected"] = "BMP"

        with open(path, "rb") as f:
            f.read(2)
            size = struct.unpack("<I", f.read(4))[0]
            f.read(4)
            offset = struct.unpack("<I", f.read(4))[0]

        report["Declared File Size"] = size
        report["Pixel Data Offset"] = offset
        report["Header Size %"] = round((offset / file_size) * 100, 2)

    else:
        report["Format Detected"] = "Unknown or Unsupported"

    return report