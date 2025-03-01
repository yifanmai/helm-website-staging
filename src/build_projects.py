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
REDIRECT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<title>Holistic Evaluation of Language Models (HELM)</title>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; URL=https://crfm.stanford.edu/helm/{project_id}/latest">
</head>
</html>
"""


def main():
    with open("src/projects_config.yaml") as f:
        projects = yaml.safe_load(f)
    source_index_path = os.path.join(DIST_PATH, INDEX_FILE_NAME)

    for project in projects:
        project_id = project["id"]
        project_path = os.path.join(DIST_PATH, project_id)
        os.mkdir(project_path)
        latest_release = project["releases"][0]
        redirect_file_path = os.path.join(project_path, INDEX_FILE_NAME)
        with open(redirect_file_path, "w") as f:
            redirect_file_contents = REDIRECT_TEMPLATE.format(project_id=project_id)
            f.write(redirect_file_contents)
        for release_or_latest in ["latest"] + project.get("preview_releases", []) + project["releases"]:
            release = latest_release if release_or_latest == "latest" else release_or_latest
            release_path = os.path.join(project_path, release_or_latest)
            os.mkdir(release_path)
            release_index_path = os.path.join(release_path, INDEX_FILE_NAME)
            shutil.copyfile(source_index_path, release_index_path)
            config_path = os.path.join(release_path, CONFIG_FILE_NAME)
            benchmark_output_base_url = GCS_URL_TEMPLATE.format(project_id=project_id)
            config_contents = CONFIG_TEMPLATE.format(
                release_constant_name="SUITE" if project.get("suites_only") else "RELEASE",
                release=release,
                project_id=project_id,
                benchmark_output_base_url=benchmark_output_base_url,
            )
            with open(config_path, "w") as f:
                f.write(config_contents)


if __name__ == "__main__":
    main()
