"""一次性遷移: v1 目錄結構 → v2 目錄結構"""
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
OLD_PHOTO = PROJECT_DIR / "download" / "photo"
OLD_VIDEO = PROJECT_DIR / "download" / "video"
OLD_STATE = PROJECT_DIR / "download" / ".downloaded_state.json"

NEW_DIR = PROJECT_DIR / "download" / "ai_guoman"
NEW_PHOTO = NEW_DIR / "photo"
NEW_VIDEO = NEW_DIR / "video"
NEW_STATE = NEW_DIR / ".downloaded_state.json"


def migrate():
    if not OLD_PHOTO.exists() and not OLD_VIDEO.exists() and not OLD_STATE.exists():
        print("無需遷移：v1 目錄不存在或已遷移完畢")
        return

    NEW_PHOTO.mkdir(parents=True, exist_ok=True)
    NEW_VIDEO.mkdir(parents=True, exist_ok=True)

    if OLD_PHOTO.exists():
        for f in OLD_PHOTO.iterdir():
            shutil.move(str(f), str(NEW_PHOTO / f.name))
        OLD_PHOTO.rmdir()
        print(f"圖片已遷移 → {NEW_PHOTO}")

    if OLD_VIDEO.exists():
        for f in OLD_VIDEO.iterdir():
            shutil.move(str(f), str(NEW_VIDEO / f.name))
        OLD_VIDEO.rmdir()
        print(f"影片已遷移 → {NEW_VIDEO}")

    if OLD_STATE.exists():
        shutil.move(str(OLD_STATE), str(NEW_STATE))
        print(f"狀態檔已遷移 → {NEW_STATE}")

    print("遷移完成")


if __name__ == "__main__":
    migrate()
