# package_converter/main.py
import os
import importlib
import inspect
import pkgutil # Added pkgutil import
from package_converter.plugins.plugin_interface import PluginInterface
from package_converter.package import Package

LOADED_PLUGINS = []

def load_plugins():
    """
    Discovers and loads plugins from the 'plugins' directory.
    """
    # Construct the path to the plugins directory relative to this file (main.py)
    # __file__ is the path to main.py
    # os.path.dirname(__file__) is the directory package_converter/
    # So, plugins_path will be package_converter/plugins
    plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')

    # The package name for plugins, assuming 'package_converter' is the top-level package
    # accessible in PYTHONPATH.
    plugins_package_name = "package_converter.plugins"

    print(f"Looking for plugins in: {plugins_path} (package: {plugins_package_name})")

    for module_finder, name, ispkg in pkgutil.iter_modules([plugins_path]):
        if name == 'plugin_interface':  # Don't load the interface itself
            print(f"Skipping module: {name}")
            continue

        full_module_name = f"{plugins_package_name}.{name}"
        print(f"Found potential plugin module: {name} (importing as {full_module_name})")

        try:
            module = importlib.import_module(full_module_name)
            for item_name, item_value in inspect.getmembers(module, inspect.isclass):
                # Check if it's a class, a subclass of PluginInterface, and not PluginInterface itself
                if issubclass(item_value, PluginInterface) and item_value is not PluginInterface:
                    try:
                        plugin_instance = item_value()  # Instantiate the plugin
                        LOADED_PLUGINS.append(plugin_instance)
                        print(f"Successfully loaded plugin: {plugin_instance.package_format_name} from {name}")
                    except Exception as e:
                        print(f"Failed to instantiate plugin {item_name} from {name}: {e}")
                #else:
                #    if item_value is PluginInterface:
                #        print(f"Skipping PluginInterface class in {name}")
                #    elif not issubclass(item_value, PluginInterface):
                #        print(f"Class {item_name} in {name} is not a subclass of PluginInterface")


        except ImportError as e:
            print(f"Failed to import plugin module {full_module_name}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading plugin {name}: {e}")


if __name__ == "__main__":
    print("Starting package converter...")
    load_plugins()
    if not LOADED_PLUGINS:
        print("No plugins were loaded.")
    else:
        print(f"Successfully loaded {len(LOADED_PLUGINS)} plugin(s):")
        for plugin in LOADED_PLUGINS:
            print(f"- {plugin.package_format_name}")

    print("Package converter finished (placeholder).")
