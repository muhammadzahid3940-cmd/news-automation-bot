import re


def _slack_format(digest: str) -> str:
    """Convert the markdown digest to Slack-friendly formatting
    (*bold*, <url|link>) with article links on their own line."""
    text = digest
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    text = re.sub(r"\[link\]\(([^)]+)\)", r"\n<\1|Full story>", text, flags=re.I)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"*\1*", text)
    text = re.sub(r"^\*(.+)\*$", r"\1", text, flags=re.M)
    return text.strip()
