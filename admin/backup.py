"""
Backup Utilities for Admin Panel
Handles automatic and manual backups of JSON files
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Tuple, Optional


# Constants
BACKUP_FOLDER = os.path.join('data', 'backups')
MAX_BACKUPS_TO_KEEP = 30


def ensure_backup_folder():
    """Ensure backup folder exists."""
    os.makedirs(BACKUP_FOLDER, exist_ok=True)


def generate_backup_filename(source_file: str) -> str:
    """
    Generate a timestamped backup filename.

    Args:
        source_file: Source file path

    Returns:
        Backup filename
    """
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(source_file))[0]

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create backup filename
    backup_filename = f"{base_name}_BACKUP_{timestamp}.json"

    return backup_filename


def create_backup(source_file: str) -> Tuple[bool, str]:
    """
    Create a backup of a JSON file.

    Args:
        source_file: Path to source JSON file

    Returns:
        Tuple of (success, backup_path_or_error)
    """
    ensure_backup_folder()

    # Check if source file exists
    if not os.path.exists(source_file):
        return False, f"Source file not found: {source_file}"

    try:
        # Generate backup filename
        backup_filename = generate_backup_filename(source_file)
        backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

        # Copy file
        shutil.copy2(source_file, backup_path)

        # Cleanup old backups
        cleanup_old_backups(os.path.basename(source_file))

        return True, backup_path

    except Exception as e:
        return False, f"Backup error: {str(e)}"


def list_backups(source_file: Optional[str] = None) -> List[dict]:
    """
    List all backups, optionally filtered by source file.

    Args:
        source_file: Optional source filename to filter by

    Returns:
        List of backup info dictionaries
    """
    ensure_backup_folder()

    backups = []

    try:
        files = os.listdir(BACKUP_FOLDER)

        for filename in files:
            if not filename.endswith('.json'):
                continue

            if source_file:
                base_name = os.path.splitext(os.path.basename(source_file))[0]
                if not filename.startswith(base_name):
                    continue

            file_path = os.path.join(BACKUP_FOLDER, filename)
            stat_info = os.stat(file_path)

            # Parse timestamp from filename
            try:
                # Format: basename_BACKUP_YYYYMMDD_HHMMSS.json
                parts = filename.replace('.json', '').split('_BACKUP_')
                if len(parts) == 2:
                    timestamp_str = parts[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                else:
                    timestamp = datetime.fromtimestamp(stat_info.st_mtime)
            except:
                timestamp = datetime.fromtimestamp(stat_info.st_mtime)

            backup_info = {
                "filename": filename,
                "path": file_path,
                "timestamp": timestamp,
                "size": stat_info.st_size,
                "source": parts[0] if len(parts) == 2 else "unknown"
            }

            backups.append(backup_info)

        # Sort by timestamp, newest first
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

    except Exception as e:
        print(f"Error listing backups: {e}")

    return backups


def restore_backup(backup_path: str, target_file: str) -> Tuple[bool, str]:
    """
    Restore a backup file.

    Args:
        backup_path: Path to backup file
        target_file: Target file to restore to

    Returns:
        Tuple of (success, error_message)
    """
    # Validate backup file exists
    if not os.path.exists(backup_path):
        return False, "קובץ גיבוי לא נמצא."

    try:
        # Validate it's a valid JSON file
        with open(backup_path, 'r', encoding='utf-8') as f:
            json.load(f)

        # Create backup of current state before restoring
        if os.path.exists(target_file):
            create_backup(target_file)

        # Copy backup to target
        shutil.copy2(backup_path, target_file)

        return True, ""

    except json.JSONDecodeError:
        return False, "קובץ הגיבוי אינו תקין (לא JSON תקין)."
    except Exception as e:
        return False, f"שגיאה בשחזור הגיבוי: {str(e)}"


def delete_backup(backup_path: str) -> Tuple[bool, str]:
    """
    Delete a backup file.

    Args:
        backup_path: Path to backup file

    Returns:
        Tuple of (success, error_message)
    """
    if not os.path.exists(backup_path):
        return False, "קובץ גיבוי לא נמצא."

    try:
        os.remove(backup_path)
        return True, ""
    except Exception as e:
        return False, f"שגיאה במחיקת הגיבוי: {str(e)}"


def cleanup_old_backups(source_file: str, keep_count: int = MAX_BACKUPS_TO_KEEP):
    """
    Delete old backups, keeping only the most recent ones.

    Args:
        source_file: Source filename to filter by
        keep_count: Number of backups to keep
    """
    backups = list_backups(source_file)

    # Keep only the specified number of most recent backups
    if len(backups) > keep_count:
        backups_to_delete = backups[keep_count:]

        for backup in backups_to_delete:
            try:
                os.remove(backup['path'])
                print(f"Deleted old backup: {backup['filename']}")
            except Exception as e:
                print(f"Error deleting backup {backup['filename']}: {e}")


def get_last_backup_info(source_file: str) -> Optional[dict]:
    """
    Get information about the most recent backup.

    Args:
        source_file: Source filename

    Returns:
        Backup info dictionary or None
    """
    backups = list_backups(source_file)

    if backups:
        return backups[0]  # Most recent

    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.2 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_backup_statistics() -> dict:
    """
    Get statistics about backups.

    Returns:
        Dictionary with backup statistics
    """
    ensure_backup_folder()

    try:
        backups = list_backups()

        total_count = len(backups)
        total_size = sum(b['size'] for b in backups)

        # Last backup time
        last_backup = backups[0] if backups else None
        last_backup_time = last_backup['timestamp'] if last_backup else None

        return {
            "total_count": total_count,
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "last_backup_time": last_backup_time
        }

    except Exception as e:
        print(f"Error getting backup statistics: {e}")
        return {
            "total_count": 0,
            "total_size": 0,
            "total_size_formatted": "0 B",
            "last_backup_time": None
        }
