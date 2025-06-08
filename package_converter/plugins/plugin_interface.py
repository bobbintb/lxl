# package_converter/plugins/plugin_interface.py
import abc
from package_converter.package import Package # Assuming Package class is in package_converter.package

class PluginInterface(abc.ABC):
    @abc.abstractmethod
    def identify(self, filepath: str) -> bool:
        """
        Check if this plugin can handle the given package file.
        Returns True if it can, False otherwise.
        """
        pass

    @abc.abstractmethod
    def extract_package(self, filepath: str) -> Package | None:
        """
        Extracts package information from the given filepath and returns a Package object.
        Returns None if extraction fails or if the plugin cannot handle the file.
        """
        pass

    @abc.abstractmethod
    def create_package(self, package_info: Package, output_dir: str) -> str | None:
        """
        Creates a package file in the output_dir using the provided Package object.
        Returns the path to the created package file, or None if creation fails.
        """
        pass

    @property
    @abc.abstractmethod
    def package_format_name(self) -> str:
        """
        Returns the name of the package format this plugin handles (e.g., "deb", "rpm").
        """
        pass
