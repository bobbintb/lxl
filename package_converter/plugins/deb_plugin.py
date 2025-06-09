# package_converter/plugins/deb_plugin.py
import subprocess
import os
import tarfile
import tempfile
import shutil
import re

# Attempt to import zstandard, but don't make it a hard requirement
try:
    import zstandard
    ZSTANDARD_AVAILABLE = True
except ImportError:
    ZSTANDARD_AVAILABLE = False
    # print("DebPlugin: 'zstandard' library not found. Support for .zst compressed control archives will be limited.")


from package_converter.plugins.plugin_interface import PluginInterface
from package_converter.package import Package

class DebPlugin(PluginInterface):
    @property
    def package_format_name(self) -> str:
        return "deb"

    def _check_ar_command(self) -> bool:
        # ... (previous implementation)
        try:
            subprocess.run(["ar", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: 'ar' command not found. It's required to unpack .deb files.")
            return False

    def identify(self, filepath: str) -> bool:
        # ... (previous implementation)
        return filepath.lower().endswith(".deb")

    def _parse_control_file(self, control_content: str) -> dict:
        # ... (previous implementation)
        metadata = {}
        unfolded_content = re.sub(r"\n\s+", " ", control_content)
        current_key = None
        for line in unfolded_content.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                current_key = key.strip()
                metadata[current_key] = value.strip()
            elif current_key:
                metadata[current_key] += "\n" + line
        if 'Depends' in metadata:
            dependencies_str = metadata['Depends']
            dependencies = []
            for dep in re.split(r',|\|', dependencies_str):
                match = re.match(r'^\s*([a-zA-Z0-9.+-]+)', dep)
                if match:
                    dependencies.append(match.group(1))
            metadata['Depends'] = dependencies
        else:
            metadata['Depends'] = []
        return metadata

    def extract_package(self, filepath: str) -> Package | None:
        # ... (previous implementation - ensuring it's complete for context)
        if not self.identify(filepath):
            print(f"DebPlugin: Not a .deb file: {filepath}")
            return None

        if not self._check_ar_command():
            return None

        temp_dir = tempfile.mkdtemp()
        # ... (rest of the extraction logic from previous step, including zstandard handling) ...
        control_archive_extracted_path = None
        extracted_member_name = None # To store the name of the control archive member

        try:
            print(f"DebPlugin: Processing {filepath} in temporary directory {temp_dir}")
            control_archive_names = ["control.tar.gz", "control.tar.xz", "control.tar.zst", "control.tar.bz2"]

            for name in control_archive_names:
                ar_command = ["ar", "p", filepath, name]
                # print(f"DebPlugin: Attempting to extract member '{name}' with command: {' '.join(ar_command)}")
                process = subprocess.run(ar_command, capture_output=True)
                if process.returncode == 0 and process.stdout: # Check stdout has content
                    control_archive_extracted_path = os.path.join(temp_dir, name)
                    with open(control_archive_extracted_path, "wb") as f:
                        f.write(process.stdout)
                    extracted_member_name = name
                    print(f"DebPlugin: Successfully extracted member '{name}' to '{control_archive_extracted_path}' (size: {len(process.stdout)} bytes)")
                    break
                # else:
                    # print(f"DebPlugin: Failed to extract member '{name}'. Return code: {process.returncode}, stdout empty: {not bool(process.stdout)}")
                    # if process.stderr:
                        # print(f"DebPlugin: Stderr for '{name}': {process.stderr.decode('utf-8', errors='replace')}")

            if not control_archive_extracted_path:
                # print(f"DebPlugin: Standard control archive names not found or failed to extract. Listing members of {filepath} as fallback.")
                list_process = subprocess.run(["ar", "t", filepath], capture_output=True, text=True)
                if list_process.returncode == 0:
                    # print(f"DebPlugin: Members of {filepath}: {list_process.stdout.splitlines()}")
                    for line in list_process.stdout.splitlines():
                        member_name_from_list = line.strip()
                        if member_name_from_list.startswith("control.tar."):
                            # print(f"DebPlugin: Found potential control archive member by listing: '{member_name_from_list}'")
                            ar_command_fallback = ["ar", "p", filepath, member_name_from_list]
                            # print(f"DebPlugin: Attempting to extract (fallback) member '{member_name_from_list}' with command: {' '.join(ar_command_fallback)}")
                            process_fallback = subprocess.run(ar_command_fallback, capture_output=True)
                            if process_fallback.returncode == 0 and process_fallback.stdout:
                                control_archive_extracted_path = os.path.join(temp_dir, member_name_from_list)
                                with open(control_archive_extracted_path, "wb") as f_fb:
                                    f_fb.write(process_fallback.stdout)
                                extracted_member_name = member_name_from_list
                                print(f"DebPlugin: Successfully extracted member '{member_name_from_list}' (fallback) to '{control_archive_extracted_path}' (size: {len(process_fallback.stdout)} bytes)")
                                break # Found and extracted in fallback
                            # else:
                                # print(f"DebPlugin: Failed to extract (fallback) member '{member_name_from_list}'. Return code: {process_fallback.returncode}, stdout empty: {not bool(process_fallback.stdout)}")
                                # if process_fallback.stderr:
                                    # print(f"DebPlugin: Stderr for (fallback) '{member_name_from_list}': {process_fallback.stderr.decode('utf-8', errors='replace')}")
                # else:
                    # print(f"DebPlugin: Failed to list members of {filepath}. Stderr: {list_process.stderr.decode('utf-8', errors='replace')}")

                if not control_archive_extracted_path: # Check again after fallback logic
                    print(f"DebPlugin: Could not find or extract control.tar.* from {filepath} even after fallback.")
                    return None

            # Handle Zstandard decompression if necessary
            tar_path_to_open = control_archive_extracted_path
            # decompressed_tar_temp_file = None # For zstd # Not needed
            if extracted_member_name.endswith(".zst"):
                if not ZSTANDARD_AVAILABLE:
                    print(f"DebPlugin: {extracted_member_name} is Zstandard compressed, but 'zstandard' library is not available. Cannot extract control file.")
                    return None
                try:
                    decompressed_tar_temp_file_path = os.path.join(temp_dir, "control.tar")
                    # print(f"DebPlugin: Decompressing {control_archive_extracted_path} to {decompressed_tar_temp_file_path} using zstandard.")
                    with open(control_archive_extracted_path, "rb") as compressed_file, \
                         open(decompressed_tar_temp_file_path, "wb") as decompressed_file:
                        dctx = zstandard.ZstdDecompressor()
                        dctx.copy_stream(compressed_file, decompressed_file)
                    tar_path_to_open = decompressed_tar_temp_file_path
                    # print(f"DebPlugin: Decompressed {extracted_member_name} to {tar_path_to_open} using zstandard.")
                except Exception as e_zstd:
                    print(f"DebPlugin: Failed to decompress {extracted_member_name} with zstandard: {e_zstd}")
                    return None

            # print(f"DebPlugin: Opening tar archive: {tar_path_to_open} with mode r:*")
            with tarfile.open(tar_path_to_open, "r:*") as tar: # Use r:* to auto-detect compression for gz, bz2, xz
                control_member = None
                for member in tar.getmembers():
                    if os.path.basename(member.name) == "control" and member.isfile():
                        control_member = member
                        break

                if control_member:
                    extracted_control_file = tar.extractfile(control_member)
                    if extracted_control_file:
                        control_content = extracted_control_file.read().decode("utf-8")
                        metadata = self._parse_control_file(control_content)

                        package_obj = Package(
                            name=metadata.get("Package", "Unknown"),
                            version=metadata.get("Version", "Unknown"),
                            description=metadata.get("Description", ""),
                            dependencies=metadata.get("Depends", []),
                            arch=metadata.get("Architecture", "Unknown"),
                            maintainer=metadata.get("Maintainer", ""),
                            homepage=metadata.get("Homepage", ""),
                            files={}
                        )
                        # print(f"DebPlugin: Successfully parsed control file for {filepath}")
                        return package_obj
                    else: # Should not happen if control_member is valid
                        print(f"DebPlugin: Failed to extract control file content from {extracted_member_name}")
                        return None
                else:
                    print(f"DebPlugin: 'control' file not found within tar archive from {extracted_member_name}")
                    return None

        except FileNotFoundError:
            # This specific exception for the .deb file itself should be clear
            print(f"DebPlugin: Error - Input .deb file not found at {filepath}")
            return None
        except subprocess.CalledProcessError as e:
            # Errors from 'ar' command
            print(f"DebPlugin: Error during 'ar' command execution: {e}")
            return None
        except tarfile.TarError as e:
            # Errors from tarfile operations
            print(f"DebPlugin: Error extracting tar file {tar_path_to_open if 'tar_path_to_open' in locals() else control_archive_extracted_path}: {e}")
            return None
        except Exception as e:
            # Catch-all for other unexpected errors during extraction
            print(f"DebPlugin: An unexpected error occurred in extract_package for {filepath}: {e}")
            return None
        finally:
            if os.path.exists(temp_dir): # Check if temp_dir was created before trying to remove
                shutil.rmtree(temp_dir)
                # print(f"DebPlugin: Cleaned up temporary directory {temp_dir}")


    def create_package(self, package_info: Package, output_dir: str) -> str | None:
        """
        Creates a .deb package from the given Package object.
        This method is currently a placeholder and not implemented.
        """
        print(f"DebPlugin: create_package for {package_info.name} - NOT IMPLEMENTED YET")
        raise NotImplementedError("Creating .deb packages from scratch is not yet implemented.")
