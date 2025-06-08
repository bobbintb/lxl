# package_converter/package.py

class Package:
    def __init__(self, name, version, description, dependencies, files, arch, maintainer, homepage):
        self.name = name
        self.version = version
        self.description = description
        self.dependencies = dependencies  # Should be a list of strings
        self.files = files  # Should be a dictionary: {'source_path': 'destination_path'}
        self.arch = arch # e.g., 'amd64', 'x86_64', 'noarch'
        self.maintainer = maintainer
        self.homepage = homepage

    def __str__(self):
        return f"Package(name='{self.name}', version='{self.version}', arch='{self.arch}')"

    def add_file(self, source_path, destination_path):
        self.files[source_path] = destination_path

    def add_dependency(self, dependency):
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
