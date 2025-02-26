import shutil
import os
import yaml


DIST_PATH = "dist/"
INDEX_FILE_NAME = "index.html"
CONFIG_FILE_NAME = "config.js"
CONFIG_TEMPLATE = """
window.{release_constant_name} = "{release}";
window.BENCHMARK_OUTPUT_BASE_URL = "{benchmark_output_base_url}";
window.PROJECT_ID = "{project_id}";
"""
GCS_URL_TEMPLATE = (
    "https://storage.googleapis.com/crfm-helm-public/{project_id}/benchmark_output/"
)


def main():
    with open("src/projects_config.yaml") as f:
        projects = yaml.safe_load(f)
    source_index_path = os.path.join(DIST_PATH, INDEX_FILE_NAME)

    for project in projects:
        project_id = project["id"]
        project_path = os.path.join(DIST_PATH, project_id)
        os.mkdir(project_path)
        for release in project["releases"]:
            release_path = os.path.join(project_path, release)
            os.mkdir(release_path)
            release_index_path = os.path.join(release_path, INDEX_FILE_NAME)
            shutil.copyfile(source_index_path, release_index_path)
            config_path = os.path.join(release_path, CONFIG_FILE_NAME)
            benchmark_output_base_url = GCS_URL_TEMPLATE.format(project_id=project_id)
            config_contents = CONFIG_TEMPLATE.format(
                release_constant_name="RELEASE",
                release=release,
                project_id=project_id,
                benchmark_output_base_url=benchmark_output_base_url,
            )
            with open(config_path, "w") as f:
                f.write(config_contents)


if __name__ == "__main__":
    main()
