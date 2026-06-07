from pathlib import Path

from config import ALLOWED_FILE_ROOTS


def resolve_safe_path(path: str) -> Path:
    requested_path = Path(path).expanduser().resolve()

    for allowed_root in ALLOWED_FILE_ROOTS:
        allowed_root = allowed_root.resolve()

        if requested_path == allowed_root or allowed_root in requested_path.parents:
            return requested_path

    raise PermissionError(
        f"Access denied. Path is outside allowed roots: {requested_path}"
    )


def register_filesystem_tools(mcp):
    @mcp.tool()
    def list_files(path: str = ".") -> dict:
        """
        List files in an allowed local directory.
        """
        target = resolve_safe_path(path)

        if not target.exists():
            raise FileNotFoundError(f"Path does not exist: {target}")

        if not target.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {target}")

        items = []

        for item in sorted(target.iterdir()):
            items.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                }
            )

        return {
            "path": str(target),
            "items": items,
        }

    @mcp.tool()
    def read_text_file(path: str, max_chars: int = 20000) -> dict:
        """
        Read a text file from an allowed local directory.
        """
        target = resolve_safe_path(path)

        if not target.exists():
            raise FileNotFoundError(f"File does not exist: {target}")

        if not target.is_file():
            raise IsADirectoryError(f"Path is not a file: {target}")

        text = target.read_text(encoding="utf-8", errors="replace")

        return {
            "path": str(target),
            "content": text[:max_chars],
            "truncated": len(text) > max_chars,
        }