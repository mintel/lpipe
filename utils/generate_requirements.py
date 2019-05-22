from pipenv.project import Project


def list_requirements(section):
    reqs = []
    for package, ver in Project().parsed_pipfile[section].items():
        if isinstance(ver, dict):
            ver = ver["version"]

        if ver == "*":
            reqs.append(package)
        else:
            reqs.append(f"{package} {ver}")

    return reqs


def write_requirements(section, output):
    with open(output, mode="w") as fd:
        for req in list_requirements(section):
            print(req, file=fd)


def main():
    write_requirements("packages", "requirements.txt")
    write_requirements("dev-packages", "requirements-dev.txt")


if __name__ == "__main__":
    main()
