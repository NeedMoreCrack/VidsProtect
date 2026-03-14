from __future__ import annotations

import getpass
import json
import os
import secrets
import sys
from pathlib import Path
from typing import List

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

"""
encrypt_video.py

Features:
1. Automatically scan video files in the same folder as the .exe
2. Encrypt all found videos
3. Split each video into shards
4. Save encrypted shards into ./Output/<video_name>/
5. Generate a formatted author_order.txt in ./Output/
"""

MAGIC = b"VENC001"
VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
CHUNK_SIZE = 1024 * 1024  # 1 MB
DEFAULT_PARTS = 10

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive an AES-256 key from the password using scrypt."""
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=2**14,
        r=8,
        p=1,
    )
    return kdf.derive(password.encode("utf-8"))


def build_header(
        *,
        original_name: str,
        total_parts: int,
        part_number: int,
        salt: bytes,
        nonce: bytes,
        part_plain_size: int,
) -> bytes:
    name_bytes = original_name.encode("utf-8")
    if len(name_bytes) > 65535:
        raise ValueError("Original filename is too long to fit in the header.")

    header = bytearray()
    header.extend(MAGIC)
    header.append(VERSION)
    header.append(total_parts)
    header.append(part_number)
    header.append(len(salt))
    header.append(len(nonce))
    header.extend(len(name_bytes).to_bytes(2, "big"))
    header.extend(part_plain_size.to_bytes(8, "big"))
    header.extend(salt)
    header.extend(nonce)
    header.extend(name_bytes)
    return bytes(header)


def split_sizes(file_size: int, total_parts: int) -> List[int]:
    base = file_size // total_parts
    remainder = file_size % total_parts
    return [base + (1 if i < remainder else 0) for i in range(total_parts)]


def encrypt_part(
        *,
        src_path: Path,
        dst_path: Path,
        start_offset: int,
        part_size: int,
        total_parts: int,
        part_number: int,
        password: str,
) -> None:
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    header = build_header(
        original_name=src_path.name,
        total_parts=total_parts,
        part_number=part_number,
        salt=salt,
        nonce=nonce,
        part_plain_size=part_size,
    )

    aad = json.dumps(
        {
            "original_name": src_path.name,
            "total_parts": total_parts,
            "part_number": part_number,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(aad)

    with src_path.open("rb") as fin, dst_path.open("wb") as fout:
        fin.seek(start_offset)
        fout.write(header)

        remaining = part_size
        while remaining > 0:
            read_size = min(CHUNK_SIZE, remaining)
            chunk = fin.read(read_size)
            if not chunk:
                raise IOError("Unexpected end of source file while reading data.")

            fout.write(encryptor.update(chunk))
            remaining -= len(chunk)

        encryptor.finalize()
        fout.write(encryptor.tag)


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def sanitize_folder_name(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    sanitized = "".join("_" if c in invalid_chars else c for c in name)
    return sanitized.strip().rstrip(".")


def find_video_files(base_dir: Path) -> List[Path]:
    files = []
    for item in base_dir.iterdir():
        if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
            files.append(item)
    return sorted(files, key=lambda p: p.name.lower())


def encrypt_single_video(
        src_path: Path,
        output_root: Path,
        password: str,
        total_parts: int,
) -> List[str]:
    file_size = src_path.stat().st_size
    if file_size == 0:
        raise ValueError(f"{src_path.name}: file size is 0.")

    video_folder = output_root / sanitize_folder_name(src_path.stem)
    video_folder.mkdir(parents=True, exist_ok=True)

    sizes = split_sizes(file_size, total_parts)
    generated_files: List[str] = []
    current_offset = 0

    print(f"\nStarting encryption: {src_path.name}")
    print(f"File size: {file_size} bytes")
    print(f"Number of shards: {total_parts}")
    print(f"Output folder: {video_folder}")

    for index, size in enumerate(sizes, start=1):
        random_name = f"shard_{secrets.token_hex(8)}.enc"
        dst_path = video_folder / random_name

        print(f"[{index}/{total_parts}] Encrypting -> {random_name}")
        encrypt_part(
            src_path=src_path,
            dst_path=dst_path,
            start_offset=current_offset,
            part_size=size,
            total_parts=total_parts,
            part_number=index,
            password=password,
        )
        generated_files.append(random_name)
        current_offset += size

    print("Encryption completed.")
    return generated_files


def write_author_order(output_root: Path, results: List[tuple[str, List[str]]]) -> None:
    lines: List[str] = []

    lines.append("AUTHOR ORDER FILE")
    lines.append("=" * 60)
    lines.append("Keep this file secure.")
    lines.append("The authorized user must know the correct shard order.")
    lines.append("")

    for video_name, shard_names in results:
        lines.append("=" * 60)
        lines.append(f"Video Name : {video_name}")
        lines.append(f"Total Parts: {len(shard_names)}")
        lines.append("=" * 60)
        lines.append("")

        for index, shard_name in enumerate(shard_names, start=1):
            lines.append(f"{index:02d}. {shard_name}")

        lines.append("")
        lines.append("Order String:")
        lines.append(", ".join(shard_names))
        lines.append("")
        lines.append("")

    order_file = output_root / "author_order.txt"
    order_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nFormatted order file saved to: {order_file}")


def main() -> int:
    base_dir = get_base_dir()
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)

    video_files = find_video_files(base_dir)
    if not video_files:
        print("No video files were found in the same folder as the executable.")
        print(f"Folder scanned: {base_dir}")
        return 1

    print("Found video files:")
    for idx, video in enumerate(video_files, start=1):
        print(f"{idx}. {video.name}")

    while True:
        password = getpass.getpass("\nEnter encryption password: ")
        confirm = getpass.getpass("Re-enter encryption password: ")
        if not password:
            print("Password cannot be empty.")
            continue
        if password != confirm:
            print("Passwords do not match.")
            continue
        break

    parts_text = input(f"Enter number of shards [{DEFAULT_PARTS}]: ").strip()
    total_parts = DEFAULT_PARTS if not parts_text else int(parts_text)

    if total_parts <= 0 or total_parts > 255:
        print("Number of shards must be between 1 and 255.")
        return 1

    all_results: List[tuple[str, List[str]]] = []

    for video_file in video_files:
        try:
            shard_names = encrypt_single_video(
                src_path=video_file,
                output_root=output_dir,
                password=password,
                total_parts=total_parts,
            )
            all_results.append((video_file.name, shard_names))
        except Exception as exc:
            print(f"Failed to encrypt {video_file.name}: {exc}")

    if not all_results:
        print("No videos were successfully encrypted.")
        return 1

    write_author_order(output_dir, all_results)

    print("\nAll tasks completed.")
    print(f"Output root: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
