"""
Claude学習note記事 自動生成スクリプト
毎日topics.yamlから当日分のテーマを選び、Claude APIで記事を生成してMarkdownファイルに保存する
"""

import anthropic
import yaml
import os
from datetime import datetime
from pathlib import Path


def load_topics() -> dict:
    """topics.yamlを読み込む"""
    with open("topics.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def select_topic(topics: list, day_number: int) -> dict:
    """day_numberに対応するトピックを選択（1始まり、30日でループ）"""
    index = (day_number - 1) % len(topics)
    return topics[index]


def get_day_number() -> int:
    """
    何日目の記事かを決定する。
    articlesフォルダ内のファイル数 + 1 を使う。
    """
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    existing = list(articles_dir.glob("day*.md"))
    return len(existing) + 1


def generate_article(topic: dict, client: anthropic.Anthropic) -> str:
    """Claude APIで記事を生成する"""

    prompt = f"""あなたはnoteで「Claudeを一緒に学ぼう」というシリーズを書いているライターです。
読者は完全な初心者から始まり、毎日少しずつレベルアップしていきます。

今日のテーマ：{topic['title']}

キーワード：{', '.join(topic['keywords'])}
文体のトーン：{topic['tone']}
目標文字数：{topic['length']}字
記事の概要：{topic['summary']}

以下の条件で記事を書いてください：

【執筆ルール】
- 一人称は「私」を使う
- 読者に語りかけるような親しみやすい文体
- 難しい用語は使ったら必ず説明する
- 具体例や実際に試した体験を交えて書く
- 冒頭は共感できる「あるある」や疑問から始める
- 見出しはnoteで使えるよう ## を使う
- 最後は次回への期待や読者への問いかけで締める
- 「まとめ」という見出しは使わない

【禁止事項】
- 「〜とは」から始まる教科書的な説明
- 箇条書きの多用（使う場合は3項目以内）
- 根拠のない情報や未確認の数字

記事本文のみを出力してください（タイトルは含めない）。
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def save_article(day: int, title: str, body: str) -> str:
    """記事をMarkdownファイルとして保存する"""
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"day{day:02d}_{today}.md"
    filepath = articles_dir / filename

    content = f"""# {title}

{body}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)


def main():
    # APIキーの確認
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    # トピック読み込み
    data = load_topics()
    topics = data["topics"]

    # 何日目かを決定
    day_number = get_day_number()
    topic = select_topic(topics, day_number)

    print(f"=== Day {day_number}: {topic['title']} ===")
    print("記事を生成中...")

    # 記事生成
    body = generate_article(topic, client)

    # 保存
    filepath = save_article(day_number, topic["title"], body)

    print(f"✅ 保存完了: {filepath}")
    print(f"文字数: {len(body)}字")


if __name__ == "__main__":
    main()
