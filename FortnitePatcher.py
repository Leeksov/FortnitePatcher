import os
import re
import zipfile
import shutil
import tempfile
from plistlib import load, dump

ipa_path = input("Please paste the path to the IPA file: ").strip()

if os.path.exists(ipa_path):
    print("File exists. Starting patching process...")

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(ipa_path, 'r') as ipa:
            payload_folder = None
            for file_name in ipa.namelist():
                if file_name.startswith("Payload/") and file_name.endswith(".app/"):
                    payload_folder = file_name
                    break

            if not payload_folder:
                exit()

            binary_path = payload_folder + "FortniteClient-IOS-Shipping"
            if binary_path not in ipa.namelist():
                exit()

            with ipa.open(binary_path) as file:
                binary_data = file.read()

            pattern = re.compile(
                b'\xF5\x03\x00\xAA.{8}\xC8\x02\x40\xB9.{4}\xC8\x82\x5F\xF8',
                re.DOTALL
            )
            replace_from = bytes.fromhex("F50300AA")
            replace_to = bytes.fromhex("350080D2")

            match = pattern.search(binary_data)

            if match:
                patch_addr = match.start()

                if binary_data[patch_addr:patch_addr + 4] == replace_from:
                    patched_data = binary_data[:patch_addr] + replace_to + binary_data[patch_addr + 4:]

                    ipa_extract_path = os.path.join(temp_dir, "ipa_contents")
                    os.makedirs(ipa_extract_path, exist_ok=True)
                    with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
                        zip_ref.extractall(ipa_extract_path)

                    patched_binary_path = os.path.join(ipa_extract_path, payload_folder, "FortniteClient-IOS-Shipping")
                    with open(patched_binary_path, 'wb') as f:
                        f.write(patched_data)

                    info_plist_path = os.path.join(ipa_extract_path, payload_folder, "Info.plist")
                    with open(info_plist_path, 'rb') as f:
                        plist_data = load(f)

                    plist_data['Patched by GLESign'] = 'https://t.me/glesign'

                    with open(info_plist_path, 'wb') as f:
                        dump(plist_data, f)

                    temp_ipa_path = os.path.join(temp_dir, "patched_ipa.ipa")

                    shutil.make_archive(temp_ipa_path.replace('.ipa', ''), 'zip', ipa_extract_path)
                    os.rename(temp_ipa_path.replace('.ipa', '.zip'), temp_ipa_path)

                    shutil.move(temp_ipa_path, ipa_path)

                    print(f"Patch complete! Patched IPA saved at: {ipa_path}")

else:
    print(f"Error: The file {ipa_path} does not exist.")
