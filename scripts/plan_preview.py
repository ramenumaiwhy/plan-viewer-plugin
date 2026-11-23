"""Publish the exact plan submitted to ExitPlanMode before its approval prompt."""
import hashlib
import html
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


def publish(event, directory):
    plan = event["tool_input"]["plan"]
    session = event["session_id"]
    if not isinstance(plan, str) or not plan.strip() or not isinstance(session, str) or not session:
        raise ValueError("計画本文またはセッション ID が空です")

    # Each submitted revision keeps its own URL, including simultaneous sessions.
    key = hashlib.sha256((session + "\0" + plan).encode()).hexdigest()[:16]
    filename = f"review-{key}.html"
    page = f"""<!doctype html>
<html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>承認前の計画 | View</title>
<style>
:root {{color-scheme:light dark}} body {{font:1rem/1.75 system-ui,sans-serif;
max-width:46rem;margin:auto;padding:1rem}} h1 {{font-size:1.25rem}}
article {{white-space:pre-wrap;overflow-wrap:anywhere}}
</style><main><h1>承認前の計画</h1><article>{html.escape(plan)}</article></main></html>"""
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, prefix=".review-", delete=False) as tmp:
        try:
            tmp.write(page.encode())
            tmp.close()
            os.replace(tmp.name, directory / filename)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
    return filename


if __name__ == "__main__":
    try:
        directory = Path(os.environ.get("PLAN_VIEWER_DIR") or Path.home() / "plan-viewer")
        filename = publish(json.load(sys.stdin), directory)
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(f"View の承認前プレビューを保存できません。{error}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"systemMessage": f"承認前にスマホで確認してください。View サーバーの /{filename} を開きます。"}, ensure_ascii=False))
