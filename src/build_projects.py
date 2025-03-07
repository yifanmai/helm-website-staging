import shutil
import os
from typing import Dict, List
import yaml


CLASSIC_PATH = "helm-classic/src/helm/benchmark/static"
DIST_PATH = "dist/"
LEGACY_PATH = "legacy/"
INDEX_FILE_NAME = "index.html"
CONFIG_FILE_NAME = "config.js"
CONFIG_TEMPLATE = """
window.{release_constant_name} = "{release}";
window.BENCHMARK_OUTPUT_BASE_URL = "{benchmark_output_base_url}";
window.PROJECT_ID = "{project_id}";
"""
NLP_URL_TEMPLATE = (
    "https://nlp.stanford.edu/helm/{project_id}/benchmark_output/"
)
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

def _get_benchmark_output_base_url(storage_type: str, project_id: str) -> str:
    if storage_type == "nlp":
        return NLP_URL_TEMPLATE.format(project_id=project_id)
    elif storage_type == "gcs":
        return GCS_URL_TEMPLATE.format(project_id=project_id)
    elif storage_type == "classic":
        return GCS_URL_TEMPLATE.format(project_id="classic").replace("classic/", "").strip("/")
    else:
        raise ValueError(f"Unknown storage {storage_type}")

def _get_all_visible_releases(project: Dict) -> List[str]:
    return project.get("releases", []) + project.get("legacy_releases", []) 

def _get_all_buildable_releases(project: Dict) -> List[str]:
    return project.get("releases", []) + project.get("preview_releases", [])

def _get_all_releases(project: Dict) -> List[str]:
    return project.get("releases", []) + project.get("preview_releases", []) + project.get("legacy_releases", []) 

def _get_latest_release(project: Dict) -> str:
    all_releases = _get_all_releases(project)
    if not all_releases:
        raise ValueError(f"No releases for project {project["id"]}")
    return all_releases[0]

def main():
    with open("src/projects_config.yaml") as f:
        projects = yaml.safe_load(f)
    source_index_path = os.path.join(DIST_PATH, INDEX_FILE_NAME)

    # Include legacy files
    shutil.copytree(LEGACY_PATH, DIST_PATH, dirs_exist_ok=True)

    # For each route /helm/:project/:release/ (e.g. /helm/lite/v1.0.0/)
    # copy two files, index.html and config.js, to that route so that the single-page app
    # can be served at that route.
    # This works around not having a true backend server that can perform routing.
    # Also do this for the "latest" alias route /helm/:project/latest/
    for project in projects:
        project_id = project["id"]
        if project_id == "home":
            continue
        project_path = os.path.join(DIST_PATH, project_id)
        os.makedirs(project_path, exist_ok=True)
        latest_release = _get_latest_release(project)
        redirect_file_path = os.path.join(project_path, INDEX_FILE_NAME)
        with open(redirect_file_path, "w") as f:
            redirect_file_contents = REDIRECT_TEMPLATE.format(project_id=project_id)
            f.write(redirect_file_contents)
        for release_or_latest in ["latest"] + _get_all_buildable_releases(project):
            release = latest_release if release_or_latest == "latest" else release_or_latest
            release_path = os.path.join(project_path, release_or_latest)
            os.makedirs(release_path, exist_ok=True)

            release_index_path = os.path.join(release_path, INDEX_FILE_NAME)
            shutil.copyfile(source_index_path, release_index_path)

            # Write the config.js file
            config_path = os.path.join(release_path, CONFIG_FILE_NAME)
            benchmark_output_base_url = _get_benchmark_output_base_url(project.get("benchmark_output_storage", "gcs"), project_id)
            config_contents = CONFIG_TEMPLATE.format(
                release_constant_name="SUITE" if project.get("suites_only") else "RELEASE",
                release=release,
                project_id=project_id,
                benchmark_output_base_url=benchmark_output_base_url,
            )
            with open(config_path, "w") as f:
                f.write(config_contents)

    # Write the config.js file at the root
    source_config_path = os.path.join(DIST_PATH, CONFIG_FILE_NAME)
    source_config_contents = CONFIG_TEMPLATE.format(
        release_constant_name="RELEASE",
        release="v1.0.0",
        project_id="home",
        benchmark_output_base_url=GCS_URL_TEMPLATE.format(project_id="home"),
    )
    with open(source_config_path, "w") as f:
        f.write(source_config_contents)




if __name__ == "__main__":
    main()
