# package_converter/plugins/dummy_plugin.py
from package_converter.plugins.plugin_interface import PluginInterface
from package_converter.package import Package # Required for type hinting and potentially creating dummy Package objects

class DummyPlugin(PluginInterface):
    @property
    def package_format_name(self) -> str:
        return "dummy"

    def identify(self, filepath: str) -> bool:
        print(f"DummyPlugin: Checking if '{filepath}' is a dummy package.")
        # For this dummy plugin, let's say it 'identifies' any file ending with '.dummy'
        return filepath.lower().endswith(".dummy")

    def extract_package(self, filepath: str) -> Package | None:
        print(f"DummyPlugin: Attempting to 'extract' {filepath}")
        if not self.identify(filepath):
            print(f"DummyPlugin: Cannot extract {filepath}, not a dummy package.")
            return None

        # Create a dummy Package object
        # For a real plugin, this would involve parsing the package file
        package = Package(
            name="dummy-package",
            version="1.0.0",
            description="A dummy package for testing.",
            dependencies=["dummy-dep1", "dummy-dep2"],
            files={"/path/to/dummy/file1.txt": "/usr/local/bin/file1.txt"},
            arch="noarch",
            maintainer="dummy_maintainer@example.com",
            homepage="http://example.com/dummy"
        )
        print(f"DummyPlugin: Successfully 'extracted' package data for {filepath}")
        return package

    def create_package(self, package_info: Package, output_dir: str) -> str | None:
        print(f"DummyPlugin: Attempting to 'create' a {self.package_format_name} package for {package_info.name} in {output_dir}")
        # For this dummy plugin, let's pretend it creates a file
        # In a real plugin, this would involve building the actual package file
        output_filename = f"{package_info.name}-{package_info.version}.{self.package_format_name}"
        output_filepath = f"{output_dir}/{output_filename}" # Using f-string for path concatenation for simplicity

        try:
            # Simulate creating a file
            with open(output_filepath, "w") as f:
                f.write(f"This is a dummy package file for {package_info.name}\n")
                f.write(f"Version: {package_info.version}\n")
                f.write(f"Description: {package_info.description}\n")
            print(f"DummyPlugin: Successfully 'created' package at {output_filepath}")
            return output_filepath
        except IOError as e:
            print(f"DummyPlugin: Error creating dummy package file at {output_filepath}: {e}")
            return None

# To make it discoverable, ensure the class name is unique or handled appropriately by the loader.
# The current loader iterates through classes, so 'DummyPlugin' will be found.
