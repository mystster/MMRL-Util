import functools
import os
import shutil
import re
from pathlib import Path
from typing import Optional

from git import Repo, InvalidGitRepositoryError, GitCommandError, exc
from github import Github, Auth, UnknownObjectException # Assuming these were added for clone_or_download_release
from .HttpUtils import HttpUtils # Assuming this was added
from .Log import Log # Assuming this was added


class GitUtils:
    @classmethod
    @functools.lru_cache()
    def current_branch(cls, repo_dir: Path) -> Optional[str]:
        try:
            return Repo(repo_dir).active_branch.name
        except InvalidGitRepositoryError:
            return None

    @classmethod
    def _get_repo_name_from_url(cls, url: str) -> Optional[tuple[str, str]]:
        """Extracts owner and repo name from GitHub URL."""
        # Handles https://github.com/owner/repo.git and git@github.com:owner/repo.git
        match = re.match(r"(?:https?://github\.com/|git@github\.com:)([^/]+)/([^/.]+)(?:\.git)?", url)
        if match:
            return match.group(1), match.group(2)
        return None

    @classmethod
    def clone_or_download_release(cls, url: str, out: Path, module_id: str, log_config: tuple) -> float:
        repo_dir = out.with_suffix("")
        enable_log, log_dir_path = log_config
        logger = Log("GitUtils", enable_log=enable_log, log_dir=log_dir_path)
        api_token = os.getenv("GITHUB_TOKEN")

        repo_parts = cls._get_repo_name_from_url(url)

        if repo_parts and api_token:
            owner, repo_name = repo_parts
            logger.d(f"[{module_id}] Attempting to download release from GitHub: {owner}/{repo_name}")
            try:
                gh = Github(auth=Auth.Token(api_token))
                repo_gh = gh.get_repo(f"{owner}/{repo_name}")
                releases = repo_gh.get_releases()
                if releases.totalCount > 0:
                    latest_release = releases[0]
                    logger.i(f"[{module_id}] Found latest release: {latest_release.tag_name} with {latest_release.get_assets().totalCount} asset(s)")

                    release_zip_assets = []
                    other_zip_assets = []

                    for asset in latest_release.get_assets():
                        if asset.name.endswith(".zip"):
                            if "release" in asset.name.lower():
                                release_zip_assets.append(asset)
                            else:
                                other_zip_assets.append(asset)

                    chosen_asset = None
                    if release_zip_assets:
                        chosen_asset = release_zip_assets[0]
                        logger.i(f"[{module_id}] Prioritizing release-named ZIP asset: {chosen_asset.name}")
                    elif other_zip_assets:
                        chosen_asset = other_zip_assets[0]
                        logger.i(f"[{module_id}] Found other ZIP asset: {chosen_asset.name}")

                    if chosen_asset:
                        logger.i(f"[{module_id}] Downloading asset: {chosen_asset.name} from {chosen_asset.browser_download_url}")
                        HttpUtils.download(chosen_asset.browser_download_url, out)
                        return latest_release.published_at.timestamp()

                    logger.w(f"[{module_id}] No suitable .zip asset found in release {latest_release.tag_name}. Will attempt to clone.")
                else:
                    logger.w(f"[{module_id}] No releases found for {owner}/{repo_name}. Will attempt to clone.")
            except UnknownObjectException:
                logger.e(f"[{module_id}] Repository not found or access denied: {owner}/{repo_name}. Will attempt to clone.")
                # Not raising here, will fall through to clone
            except Exception as e:
                logger.e(f"[{module_id}] Error fetching GitHub release for {url}: {e}. Will attempt to clone.")
                # Fall through to clone if release download fails
        elif repo_parts and not api_token:
            logger.w(f"[{module_id}] GitHub URL detected but GITHUB_API_TOKEN env var not set. Skipping release check, will attempt to clone.")

        # Fallback to cloning and zipping
        logger.i(f"[{module_id}] Cloning repository: {url}")
        if repo_dir.exists():
            shutil.rmtree(repo_dir)

        try:
            repo = Repo.clone_from(url, repo_dir)
            if repo.head.is_detached:
                logger.w(f"[{module_id}] Repository HEAD is detached. Using HEAD commit for timestamp.")
                last_committed = float(repo.head.commit.committed_date)
            else:
                last_committed = float(repo.active_branch.commit.committed_date)
        except exc.GitCommandError as e:
            shutil.rmtree(repo_dir, ignore_errors=True)
            logger.e(f"[{module_id}] Clone failed for {url}: {e}")
            raise

        for path in repo_dir.iterdir():
            if path.name.startswith(".git"):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                if path.is_file():
                    path.unlink(missing_ok=True)

                continue

            os.utime(path, (last_committed, last_committed))

        archive_base_name = repo_dir.as_posix()
        try:
            shutil.make_archive(archive_base_name, format="zip", root_dir=repo_dir)
            logger.i(f"[{module_id}] Successfully created zip archive from clone: {archive_base_name}.zip")
        except FileNotFoundError:
            logger.e(f"[{module_id}] Archive creation from clone failed for {archive_base_name}")
            raise FileNotFoundError(f"archive failed: {archive_base_name}")
        finally:
            shutil.rmtree(repo_dir)
        return last_committed
