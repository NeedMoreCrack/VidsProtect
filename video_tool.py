from pathlib import Path
import sys
import getpass

import encrypt_video
import decrypt_video


def pause():
    input("\nPress Enter to exit...")


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty.")


def run_encrypt():
    """
    Use the new encrypt_video flow:
    - automatically scan video files in the same folder as the .exe
    - automatically create/use ./Output
    - ask only for password and shard count inside encrypt_video.main()
    """
    sys.argv = ["encrypt_video.py"]
    raise SystemExit(encrypt_video.main())


def run_decrypt():
    """
    Use the new decrypt_video flow:
    - read shard files from the same folder as the .exe
    - only read the shard names listed in the user-provided order string
    - restore the video into ./DeVids
    """
    order = ask_non_empty("Paste the correct order string: ")

    password = getpass.getpass("Enter decryption password: ")
    if not password:
        print("Password cannot be empty.")
        return

    output_file = input("Enter output file path [auto]: ").strip()

    sys.argv = [
        "decrypt_video.py",
        "--order",
        order,
        "--password",
        password,
    ]

    if output_file:
        sys.argv.extend(["--output", output_file])

    raise SystemExit(decrypt_video.main())


def main():
    print("===================================")
    print("           Video Tool")
    print("===================================")
    print("1 = Encrypt")
    print("2 = Decrypt")

    choice = ask_non_empty("Select an option: ")

    try:
        if choice == "1":
            run_encrypt()
        elif choice == "2":
            run_decrypt()
        else:
            print("Invalid option.")
    finally:
        pause()


if __name__ == "__main__":
    main()
