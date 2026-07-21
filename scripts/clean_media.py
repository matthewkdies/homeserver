"""This file cleans up my media for extraneous files, empty dirs, etc.

I also run this as a cron job, providing the directories that I want to
clean as arguments. When I add on new drives, I'll have to add them to the job.
"""

import logging
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

DRY_RUN: bool = False  # Set to False to perform actual filesystem changes

logger = logging.getLogger("media_cleaner")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class CleanupStats:
    """Tracks operations performed during the cleaning process."""

    forced_renamed: int = 0
    forced_deleted: int = 0
    en_renamed: int = 0
    junk_deleted: int = 0
    dirs_deleted: int = 0
    warnings: list[str] = field(default_factory=list)


def send_ntfy_notification(
    title: str, message: str, priority: str = "low", tags: str = "broom"
) -> None:
    """Sends a push notification via Ntfy using standard library urllib."""
    token = os.environ.get("NTFY_TOKEN")
    topic = os.environ.get("NTFY_SERVER_HEALTH_TOPIC")

    if not topic:
        logger.warning(
            "NTFY_SERVER_HEALTH_TOPIC env var not set; skipping Ntfy notification."
        )
        return

    url = f"https://ntfy.mattdies.com/{topic}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            logger.info("Ntfy notification sent successfully (HTTP %s).", resp.status)
    except urllib.error.URLError as e:
        logger.error("Failed to send Ntfy notification: %s", e)


def rename_forced_subs(content_dir: Path, stats: CleanupStats) -> None:
    """Fixes incorrect Sonarr/Radarr forced subtitle naming conventions."""
    logger.info("Checking forced subtitles in: '%s'", content_dir)

    for lang in ("en", "eng"):
        for orig_file in content_dir.glob(f"**/*.1.{lang}.srt"):
            orig_str = str(orig_file)
            forced_file = Path(orig_str.replace(f".1.{lang}.srt", f".2.{lang}.srt"))
            target_orig = Path(orig_str.replace(f".1.{lang}.srt", ".eng.srt"))

            if forced_file.exists():
                forced_size = forced_file.stat().st_size
                orig_size = orig_file.stat().st_size

                # Copy detection: Forced file is same size or larger -> duplicate
                if forced_size >= orig_size:
                    if DRY_RUN:
                        logger.info(
                            "[DRY RUN] Would delete duplicate forced subtitle: '%s'",
                            forced_file.name,
                        )
                    else:
                        logger.info(
                            "Deleting duplicate forced subtitle: '%s'", forced_file.name
                        )
                        forced_file.unlink()
                    stats.forced_deleted += 1

                # Check for abnormally large forced subtitle file
                elif forced_size > (orig_size * 0.4):
                    warn_msg = (
                        f"Large forced sub skipped (check manually): {forced_file.name}"
                    )
                    logger.warning(warn_msg)
                    stats.warnings.append(warn_msg)
                else:
                    target_forced = Path(
                        str(forced_file).replace(f".2.{lang}.srt", ".eng.forced.srt")
                    )
                    if DRY_RUN:
                        logger.info(
                            "[DRY RUN] Would rename forced sub: '%s' -> '%s'",
                            forced_file.name,
                            target_forced.name,
                        )
                    else:
                        forced_file.replace(target_forced)
                        logger.info(
                            "Renamed forced sub: '%s' -> '%s'",
                            forced_file.name,
                            target_forced.name,
                        )
                    stats.forced_renamed += 1

            # Rename original .1 file to standard .eng.srt
            if DRY_RUN:
                logger.info(
                    "[DRY RUN] Would rename sub: '%s' -> '%s'",
                    orig_file.name,
                    target_orig.name,
                )
            else:
                orig_file.replace(target_orig)
            stats.forced_renamed += 1


def rename_en_to_eng_subs(content_dir: Path, stats: CleanupStats) -> None:
    """Converts legacy 2-letter (.en.srt) subtitle codes to ISO 3-letter (.eng.srt)."""
    logger.info("Normalizing .en.srt subtitles to .eng.srt in: '%s'", content_dir)

    for en_file in content_dir.glob("**/*.en.srt"):
        # Skip forced intermediate files if any remain
        if en_file.name.endswith((".1.en.srt", ".2.en.srt", ".forced.en.srt")):
            continue

        eng_file = Path(str(en_file).replace(".en.srt", ".eng.srt"))

        if eng_file.exists():
            if DRY_RUN:
                logger.info(
                    "[DRY RUN] Would remove legacy '.en.srt' (duplicate exists): '%s'",
                    en_file.name,
                )
            else:
                logger.info(
                    "Duplicate '.eng.srt' exists; removing legacy '.en.srt': '%s'",
                    en_file.name,
                )
                en_file.unlink()
            stats.en_renamed += 1
        else:
            if DRY_RUN:
                logger.info(
                    "[DRY RUN] Would rename sub: '%s' -> '%s'",
                    en_file.name,
                    eng_file.name,
                )
            else:
                en_file.replace(eng_file)
            stats.en_renamed += 1


def delete_junk_files(content_dir: Path, stats: CleanupStats) -> None:
    """Removes leftover metadata files (.nfo, .txt)."""
    logger.info("Cleaning .nfo and .txt files in: '%s'", content_dir)

    for ext in ("*.nfo", "*.txt"):
        for junk_file in content_dir.glob(f"**/{ext}"):
            if DRY_RUN:
                logger.info("[DRY RUN] Would delete junk file: '%s'", junk_file)
            else:
                logger.debug("Deleting junk file: '%s'", junk_file)
                junk_file.unlink()
            stats.junk_deleted += 1


def delete_empty_directories(content_dir: Path, stats: CleanupStats) -> None:
    """Recursively removes empty directories from the bottom up."""
    logger.info("Cleaning empty directories in: '%s'", content_dir)

    for root, dirs, files in os.walk(content_dir, topdown=False):
        if Path(root) == content_dir:
            continue

        # In dry run mode, check if directory is empty without trying rmdir
        if DRY_RUN:
            if not os.listdir(root):
                logger.info("[DRY RUN] Would remove empty directory: '%s'", root)
                stats.dirs_deleted += 1
        else:
            try:
                os.rmdir(root)
                logger.info("Removed empty directory: '%s'", root)
                stats.dirs_deleted += 1
            except OSError:
                pass  # Directory was not empty


def process_directory(content_dir: Path) -> CleanupStats:
    """Executes all cleaning steps on a target directory."""
    if not content_dir.exists() or not content_dir.is_dir():
        raise NotADirectoryError(f"Directory does not exist: '{content_dir}'")

    stats = CleanupStats()
    rename_forced_subs(content_dir, stats)
    rename_en_to_eng_subs(content_dir, stats)
    delete_junk_files(content_dir, stats)
    delete_empty_directories(content_dir, stats)
    return stats


def main() -> None:
    target_dirs = [Path(arg) for arg in sys.argv[1:]]

    if not target_dirs:
        logger.error(
            "No target directories provided. Usage: python media_cleaner.py <dir1> [dir2 ...]"
        )
        sys.exit(1)

    if DRY_RUN:
        logger.info("=== RUNNING IN DRY RUN MODE (No files will be modified) ===")

    total_stats = CleanupStats()

    try:
        for target in target_dirs:
            logger.info("Starting processing for: '%s'", target)
            dir_stats = process_directory(target)

            # Aggregate stats
            total_stats.forced_renamed += dir_stats.forced_renamed
            total_stats.forced_deleted += dir_stats.forced_deleted
            total_stats.en_renamed += dir_stats.en_renamed
            total_stats.junk_deleted += dir_stats.junk_deleted
            total_stats.dirs_deleted += dir_stats.dirs_deleted
            total_stats.warnings.extend(dir_stats.warnings)

        prefix = "[DRY RUN] " if DRY_RUN else ""
        msg_lines = [
            f"{prefix}Processed {len(target_dirs)} directory(ies).",
            f"• Subtitles to rename/normalize: {total_stats.forced_renamed + total_stats.en_renamed}",
            f"• Duplicate subs to delete: {total_stats.forced_deleted}",
            f"• Metadata files (.nfo/.txt) to delete: {total_stats.junk_deleted}",
            f"• Empty folders to purge: {total_stats.dirs_deleted}",
        ]

        if total_stats.warnings:
            msg_lines.append("\nWarnings:")
            msg_lines.extend(f"- {w}" for w in total_stats.warnings)

        message = "\n".join(msg_lines)
        priority = "low" if not total_stats.warnings else "default"
        tags = (
            "test_tube,broom"
            if DRY_RUN
            else ("movie_camera,broom" if not total_stats.warnings else "warning,broom")
        )

        send_ntfy_notification(
            title=f"{prefix}Media Cleanup Finished",
            message=message,
            priority=priority,
            tags=tags,
        )

    except Exception as e:
        logger.exception("Media cleanup failed due to an error.")
        prefix = "[DRY RUN] " if DRY_RUN else ""
        send_ntfy_notification(
            title=f"{prefix}Media Cleanup Failed",
            message=f"Error encountered during processing: {str(e)}",
            priority="high",
            tags="warning,rotating_light",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
