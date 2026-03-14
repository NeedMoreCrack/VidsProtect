from __future__ import annotations

import argparse
import getpass
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

"""
decrypt_video.py

Features:
1. Read encrypted .enc shards from the same folder as the .exe / .py
2. The user must provide:
   - The correct password
   - The correct file order provided by the author
3. Only the shard files listed in the order string will be read
4. Decryption fails if the order is wrong, the password is wrong,
   or the files have been modified
5. Restore the original video file into ./DeVids/
"""

MAGIC = b"VENC001"
VERSION = 1
KEY_SIZE = 32
CHUNK_SIZE = 1024 * 1024  # 1 MB
GCM_TAG_SIZE = 16


@dataclass
class PartMeta:
    path: Path
    version: int
    total_parts: int
    part_number: int
    salt: bytes
    nonce: bytes
    original_name: str
    plain_size: int
    header_size: int
    file_size: int


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


def get_base_dir() -> Path:
    """Return the directory where the .exe or .py file is located."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def parse_header(part_path: Path) -> PartMeta:
    with part_path.open("rb") as f:
        magic = f.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError(f"{part_path.name}: Invalid encrypted shard (wrong MAGIC value)")

        version_raw = f.read(1)
        if len(version_raw) != 1:
            raise ValueError(f"{part_path.name}: Corrupted header (version)")
        version = version_raw[0]

        total_parts_raw = f.read(1)
        part_number_raw = f.read(1)
        salt_len_raw = f.read(1)
        nonce_len_raw = f.read(1)

        if not (total_parts_raw and part_number_raw and salt_len_raw and nonce_len_raw):
            raise ValueError(f"{part_path.name}: Corrupted header (missing basic fields)")

        total_parts = total_parts_raw[0]
        part_number = part_number_raw[0]
        salt_len = salt_len_raw[0]
        nonce_len = nonce_len_raw[0]

        name_len_raw = f.read(2)
        if len(name_len_raw) != 2:
            raise ValueError(f"{part_path.name}: Corrupted header (name_len)")
        name_len = int.from_bytes(name_len_raw, "big")

        plain_size_raw = f.read(8)
        if len(plain_size_raw) != 8:
            raise ValueError(f"{part_path.name}: Corrupted header (plain_size)")
        plain_size = int.from_bytes(plain_size_raw, "big")

        salt = f.read(salt_len)
        if len(salt) != salt_len:
            raise ValueError(f"{part_path.name}: Corrupted header (salt)")

        nonce = f.read(nonce_len)
        if len(nonce) != nonce_len:
            raise ValueError(f"{part_path.name}: Corrupted header (nonce)")

        name_bytes = f.read(name_len)
        if len(name_bytes) != name_len:
            raise ValueError(f"{part_path.name}: Corrupted header (original_name)")

        original_name = name_bytes.decode("utf-8")

        header_size = (
                len(MAGIC) + 1 + 1 + 1 + 1 + 1 + 2 + 8 + salt_len + nonce_len + name_len
        )
        file_size = part_path.stat().st_size

        if file_size < header_size + GCM_TAG_SIZE:
            raise ValueError(f"{part_path.name}: File is too small to be a valid shard")

        return PartMeta(
            path=part_path,
            version=version,
            total_parts=total_parts,
            part_number=part_number,
            salt=salt,
            nonce=nonce,
            original_name=original_name,
            plain_size=plain_size,
            header_size=header_size,
            file_size=file_size,
        )


def decrypt_part(meta: PartMeta, password: str, fout) -> None:
    """Decrypt a single shard and write plaintext to the final output file."""
    aad = json.dumps(
        {
            "original_name": meta.original_name,
            "total_parts": meta.total_parts,
            "part_number": meta.part_number,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    key = derive_key(password, meta.salt)

    ciphertext_size = meta.file_size - meta.header_size - GCM_TAG_SIZE
    if ciphertext_size < 0:
        raise ValueError(f"{meta.path.name}: Invalid shard size")

    with meta.path.open("rb") as fin:
        fin.seek(meta.file_size - GCM_TAG_SIZE)
        tag = fin.read(GCM_TAG_SIZE)
        if len(tag) != GCM_TAG_SIZE:
            raise ValueError(f"{meta.path.name}: Missing GCM tag")

        cipher = Cipher(algorithms.AES(key), modes.GCM(meta.nonce, tag))
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)

        fin.seek(meta.header_size)
        remaining = ciphertext_size

        written = 0
        while remaining > 0:
            read_size = min(CHUNK_SIZE, remaining)
            chunk = fin.read(read_size)
            if not chunk:
                raise IOError(f"{meta.path.name}: Read interrupted while processing ciphertext")

            plaintext = decryptor.update(chunk)
            fout.write(plaintext)
            written += len(plaintext)
            remaining -= len(chunk)

        decryptor.finalize()

        if written != meta.plain_size:
            raise ValueError(
                f"{meta.path.name}: Decrypted size mismatch, expected {meta.plain_size}, got {written}"
            )


def parse_order(order_text: str) -> List[str]:
    parts = [x.strip() for x in order_text.split(",")]
    parts = [x for x in parts if x]
    if not parts:
        raise ValueError("The order string is empty.")
    return parts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore a video by using the correct file order and password."
    )
    parser.add_argument(
        "--order",
        help='The correct file order provided by the author, for example "a.enc,b.enc,c.enc,..."',
    )
    parser.add_argument(
        "--password",
        help="Decryption password; if omitted, it will be requested interactively",
    )
    parser.add_argument(
        "--output",
        help="Optional output path; default is ./DeVids/recovered_<original_filename>",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    base_dir = get_base_dir()
    output_dir = base_dir / "DeVids"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.order:
        order_text = args.order
    else:
        order_text = input("Paste the correct order string: ").strip()

    try:
        order_names = parse_order(order_text)
    except Exception as exc:
        print(f"Invalid order string: {exc}", file=sys.stderr)
        return 1

    password = args.password
    if not password:
        password = getpass.getpass("Enter decryption password: ")

    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        return 1

    ordered_paths: List[Path] = []
    for name in order_names:
        part_path = base_dir / name
        if not part_path.is_file():
            print(f"Missing shard: {name}", file=sys.stderr)
            return 1
        ordered_paths.append(part_path)

    try:
        metas = [parse_header(p) for p in ordered_paths]
    except Exception as exc:
        print(f"Failed to parse shard metadata: {exc}", file=sys.stderr)
        return 1

    try:
        first = metas[0]

        if first.version != VERSION:
            raise ValueError(f"Unsupported version: {first.version}")

        total_parts = first.total_parts
        original_name = first.original_name

        if len(metas) != total_parts:
            raise ValueError(
                f"Shard count mismatch: header requires {total_parts} shards, but {len(metas)} were provided"
            )

        for idx, meta in enumerate(metas, start=1):
            if meta.version != VERSION:
                raise ValueError(f"{meta.path.name}: Version mismatch")
            if meta.total_parts != total_parts:
                raise ValueError(f"{meta.path.name}: total_parts mismatch")
            if meta.original_name != original_name:
                raise ValueError(f"{meta.path.name}: original_name mismatch")

            if meta.part_number != idx:
                raise ValueError(
                    f"Wrong order: the file you provided at position {idx} is {meta.path.name}, "
                    f"but it actually belongs to shard {meta.part_number}"
                )

        output_path = (
            Path(args.output).resolve()
            if args.output
            else (output_dir / f"recovered_{original_name}")
        )

        print(f"Starting decryption -> {output_path}")

        with output_path.open("wb") as fout:
            for idx, meta in enumerate(metas, start=1):
                print(f"[{idx}/{total_parts}] Decrypting {meta.path.name}")
                decrypt_part(meta, password, fout)

        print("Decryption completed.")
        print(f"Output file: {output_path}")
        return 0

    except InvalidTag:
        print(
            "Decryption failed: wrong password, wrong file order, or file contents were modified.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"Decryption failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
