import shutil
import json
import os
from typing import Dict, List, Mapping
import yaml


# CLASSIC_PATH = "helm-classic/src/helm/benchmark/static"
DIST_PATH = "dist/"
LEGACY_PATH = "legacy/"
INDEX_FILE_NAME = "index.html"
CONFIG_FILE_NAME = "config.js"
PROJECT_METADATA_FILE_NAME = "project_metadata.json"
CONFIG_TEMPLATE = """
window.{release_constant_name} = "{release}";
window.BENCHMARK_OUTPUT_BASE_URL = "{benchmark_output_base_url}";
window.PROJECT_ID = "{project_id}";
"""
NLP_URL_TEMPLATE = "https://nlp.stanford.edu/helm/{project_id}/benchmark_output/"
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


def get_benchmark_output_base_url(storage_type: str, project_id: str) -> str:
    if storage_type == "nlp":
        return NLP_URL_TEMPLATE.format(project_id=project_id)
    elif storage_type == "gcs":
        return GCS_URL_TEMPLATE.format(project_id=project_id)
    elif storage_type == "classic":
        return (
            GCS_URL_TEMPLATE.format(project_id="classic")
            .replace("classic/", "")
            .strip("/")
        )
    else:
        raise ValueError(f"Unknown storage {storage_type}")


def get_visible_releases(project: Dict) -> List[str]:
    return project.get("releases", []) + project.get("legacy_releases", [])


def get_buildable_releases(project: Dict) -> List[str]:
    return project.get("releases", []) + project.get("preview_releases", [])


def get_all_releases(project: Dict) -> List[str]:
    return (
        project.get("releases", [])
        + project.get("preview_releases", [])
        + project.get("legacy_releases", [])
    )


def get_latest_release(project: Dict) -> str:
    all_releases = get_all_releases(project)
    if not all_releases:
        raise ValueError(f"No releases for project {project['id']}")
    return all_releases[0]


def build_project(
    vite_build_path: str,
    project_id: str,
    project_path: str,
    benchmark_output_base_url: str,
    latest_release: str,
    buildable_releases: List[str],
    suites_only: bool,
):
    os.makedirs(project_path, exist_ok=True)
    redirect_file_path = os.path.join(project_path, INDEX_FILE_NAME)
    with open(redirect_file_path, "w") as f:
        redirect_file_contents = REDIRECT_TEMPLATE.format(project_id=project_id)
        f.write(redirect_file_contents)
    for release in ["latest"] + buildable_releases:
        release = latest_release if release == "latest" else release
        release_path = os.path.join(project_path, release)
        os.makedirs(release_path, exist_ok=True)

        source_index_path = os.path.join(vite_build_path, INDEX_FILE_NAME)
        release_index_path = os.path.join(release_path, INDEX_FILE_NAME)
        shutil.copyfile(source_index_path, release_index_path)

        # Write the config.js file
        config_path = os.path.join(release_path, CONFIG_FILE_NAME)
        config_contents = CONFIG_TEMPLATE.format(
            release_constant_name="SUITE" if suites_only else "RELEASE",
            release=latest_release if release == "latest" else release,
            project_id=project_id,
            benchmark_output_base_url=benchmark_output_base_url,
        )
        with open(config_path, "w") as f:
            f.write(config_contents)


def build_project_metadata(projects: Mapping) -> None:
    project_metadata = []
    for project in projects:
        releases = get_visible_releases(project)
        if not releases:
            continue
        project_metadata.append({
            "title": project["title"],
            "description": project["description"],
            "id": project["id"],
            "releases": releases,
        })
    # Add special "home" project
    project_metadata.append({
        "title": "All Leaderboards",
        "description": "Home page for all HELM leaderboards",
        "id": "home",
        "releases": ["v1.0.0"],
    })
    return project_metadata


def main():
    with open("src/projects_config.yaml") as f:
        projects = yaml.safe_load(f)

    # For each route /helm/:project/:release/ (e.g. /helm/lite/v1.0.0/)
    # copy two files, index.html and config.js, to that route so that the single-page app
    # can be served at that route.
    # This works around not having a true backend server that can perform routing.
    # Also do this for the "latest" alias route /helm/:project/latest/
    for project in projects:
        project_id = project["id"]
        benchmark_output_base_url = get_benchmark_output_base_url(
            project.get("benchmark_output_storage", "gcs"), project_id
        )
        project_path = os.path.join(DIST_PATH, project_id)
        latest_release = get_latest_release(project)
        buildable_releases = get_buildable_releases(project)
        build_project(
            vite_build_path=DIST_PATH,
            project_id=project_id,
            project_path=project_path,
            benchmark_output_base_url=benchmark_output_base_url,
            latest_release=latest_release,
            buildable_releases=buildable_releases,
            suites_only=project.get("suites_only", False),
        )

    # Include legacy files
    shutil.copytree(LEGACY_PATH, DIST_PATH, dirs_exist_ok=True)

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

    # Write the project_metadata.json file at the root
    project_metadata_path = os.path.join(DIST_PATH, PROJECT_METADATA_FILE_NAME)
    with open(project_metadata_path, "w") as f:
        json.dump(build_project_metadata(projects), f, indent="\t")


if __name__ == "__main__":
    main()
