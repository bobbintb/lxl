# package_converter/main.py
import os
import importlib
import inspect
import pkgutil
from package_converter.plugins.plugin_interface import PluginInterface
from package_converter.package import Package # Keep for potential future use in main

LOADED_PLUGINS = []

def load_plugins():
    """
    Discovers and loads plugins from the 'plugins' directory.
    """
    plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
    plugins_package_name = "package_converter.plugins"

    print(f"Looking for plugins in: {plugins_path} (package: {plugins_package_name})")

    for module_finder, name, ispkg in pkgutil.iter_modules([plugins_path]):
        if name == 'plugin_interface':
            print(f"Skipping module: {name}")
            continue

        full_module_name = f"{plugins_package_name}.{name}"
        print(f"Found potential plugin module: {name} (importing as {full_module_name})")

        try:
            module = importlib.import_module(full_module_name)
            for item_name, item_value in inspect.getmembers(module, inspect.isclass):
                if issubclass(item_value, PluginInterface) and item_value is not PluginInterface:
                    try:
                        plugin_instance = item_value()
                        LOADED_PLUGINS.append(plugin_instance)
                        print(f"Successfully loaded plugin: {plugin_instance.package_format_name} from {name}")
                    except Exception as e:
                        print(f"Failed to instantiate plugin {item_name} from {name}: {e}")
        except ImportError as e:
            print(f"Failed to import plugin module {full_module_name}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading plugin {name}: {e}")

def main():
    """
    Main function to load plugins and potentially orchestrate conversions.
    """
    print("Starting package converter...")
    load_plugins()
    if not LOADED_PLUGINS:
        print("No plugins were loaded.")
    else:
        print(f"Successfully loaded {len(LOADED_PLUGINS)} plugin(s):")
        for plugin in LOADED_PLUGINS:
            print(f"- {plugin.package_format_name}")

    # Example usage (can be commented out or expanded)
    # Find the deb plugin
    deb_plugin = next((p for p in LOADED_PLUGINS if p.package_format_name == "deb"), None)
    if deb_plugin:
        print("\nTesting DebPlugin metadata extraction...")
        # List files in the directory that package_converter/main.py is in.
        # The .deb file should be sibling to the package_converter directory for this path to work.
        # Or adjust the path as needed. For now, assume it's in the parent of package_converter.

        # Let's try to find the .deb file relative to the main.py script's parent directory
        # __file__ is package_converter/main.py
        # os.path.dirname(__file__) is package_converter/
        # os.path.dirname(os.path.dirname(__file__)) is the parent of package_converter/ (e.g. /root/lxl)

        script_dir = os.path.dirname(__file__) # package_converter/
        repo_root_dir = os.path.dirname(script_dir) # parent of package_converter/, e.g. /root/lxl/

        # Try to find a .deb file in the repo root (e.g. /root/lxl/*.deb)
        # This is just for demonstration; a real application would take the path as an argument.
        sample_deb_file = None
        files_in_repo_root = os.listdir(repo_root_dir)
        for f_name in files_in_repo_root:
            if f_name.endswith(".deb"):
                sample_deb_file = os.path.join(repo_root_dir, f_name)
                print(f"Found sample .deb file: {sample_deb_file}")
                break

        if sample_deb_file and os.path.exists(sample_deb_file):
            package_data = deb_plugin.extract_package(sample_deb_file)
            if package_data:
                print(f"Extracted package: {package_data.name} version {package_data.version}")
                print(f"  Arch: {package_data.arch}")
                print(f"  Maintainer: {package_data.maintainer}")
                print(f"  Homepage: {package_data.homepage}")
                print(f"  Description: {package_data.description[:60]}...") # Print first 60 chars
                print(f"  Dependencies: {package_data.dependencies}")
            else:
                print(f"Failed to extract metadata from {sample_deb_file}")
        else:
            print(f"No sample .deb file found in {repo_root_dir} to test metadata extraction.")
            print(f"(Looked for files like 'tree_2.1.1-2ubuntu3_amd64.deb')")


    print("\nPackage converter finished.")

if __name__ == "__main__":
    main()
