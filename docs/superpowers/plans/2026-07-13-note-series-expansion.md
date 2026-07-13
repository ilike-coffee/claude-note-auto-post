# Note記事シリーズ続編（day31〜）実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 中級編（day31〜50、無料）・上級編（day51〜70、有料）のトピックデータを追加し、サムネイル生成を難易度別配色に対応させる。

**Architecture:** `topics.yaml` に `tier`/`is_paid`/`price` フィールドを追加してデータを拡張し、`generate_thumbnail.py` がそのデータを読んで day から tier を解決、tier ごとの配色パレットを適用する。既存の `create_thumbnail(day, title, output_path)` の呼び出しインターフェースは変更しない。

**Tech Stack:** Python 3, Pillow（画像生成）, PyYAML, pytest（テスト）

## Global Constraints

- ロボットの形状・フォントは変更しない。変えるのは背景色（メイン/アクセント/ダーク）とロボットの目・口の色のみ。
- tier文字列は `"初級"` / `"中級"` / `"上級"` の3値固定。
- 配色（設計レビュー済み）:
  - 初級: main `#E8630A`, accent `#F5A623`, dark `#C44D00`
  - 中級: main `#1E5FA8`, accent `#4FA8D8`, dark `#123F73`
  - 上級: main `#4B2E83`, accent `#7A5AC2`, dark `#2E1B54`
- 上級編の価格は一律 `380`（円）を初期値とする。
- `git push` は全タスク完了後にユーザーへ確認してから行う。各タスクでは `git commit` まで。
- 対象リポジトリ: `/Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post`

---

## Task 1: current_day リセットと不要サムネイルの削除

day31〜33は以前生成されたが記事本文のみ削除され、サムネイルだけ残っていた不整合状態。day31から作り直すためにクリーンアップする。

**Files:**
- Modify: `topics.yaml:1`
- Delete: `thumbnails/day31.png`, `thumbnails/day32.png`, `thumbnails/day33.png`

**Interfaces:**
- Consumes: なし
- Produces: `topics.yaml` の `current_day: 31`（Task 3以降が前提とする状態）

- [ ] **Step 1: current_day を 34 から 31 に変更する**

`topics.yaml` の1行目を編集:

```yaml
current_day: 31
```

- [ ] **Step 2: 不要になったday31〜33のサムネイルを削除する**

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
git rm thumbnails/day31.png thumbnails/day32.png thumbnails/day33.png
```

- [ ] **Step 3: 変更を確認する**

```bash
git status
```

Expected: `topics.yaml` が modified、3つの `thumbnails/day3{1,2,3}.png` が deleted としてステージされている。

- [ ] **Step 4: コミット**

```bash
git add topics.yaml
git commit -m "Reset current_day to 31, remove orphaned day31-33 thumbnails"
```

---

## Task 2: generate_thumbnail.py をtier別配色に対応させる

**Files:**
- Modify: `generate_thumbnail.py`
- Test: `tests/test_generate_thumbnail.py`

**Interfaces:**
- Consumes: `topics.yaml` の `topics[].day` / `topics[].tier`（Task 1でリセット済みのファイルを読む）
- Produces:
  - `PALETTES: dict[str, dict[str, str]]` — キーは `"初級"`/`"中級"`/`"上級"`、値は `{"main": str, "accent": str, "dark": str}`
  - `_resolve_tier(topics_data: dict, day: int) -> str` — 該当dayが見つからない、または`tier`フィールドが無ければ `"初級"` を返す
  - `_load_topics_data() -> dict` — `generate_thumbnail.py` と同じディレクトリの `topics.yaml` を読み込む
  - `_draw_robot(draw, cx, cy, size, color, face_color)` — 既存シグネチャに `face_color` 引数を追加（目・口の色）
  - `create_thumbnail(day, title, output_path)` — 呼び出しシグネチャは不変。内部で tier を解決してパレットを適用する

- [ ] **Step 1: テスト用ディレクトリにpytestの探索パス設定を書く**

`tests/` ディレクトリが `generate_thumbnail.py` をimportできるよう、テストファイル冒頭でパスを追加する（後述のテストコードに含む）。

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_generate_thumbnail.py` を新規作成:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_thumbnail import _resolve_tier, PALETTES


def test_resolve_tier_returns_tier_for_matching_day():
    topics_data = {
        "topics": [
            {"day": 1, "tier": "初級"},
            {"day": 31, "tier": "中級"},
            {"day": 51, "tier": "上級"},
        ]
    }
    assert _resolve_tier(topics_data, 31) == "中級"
    assert _resolve_tier(topics_data, 51) == "上級"


def test_resolve_tier_defaults_to_shokyu_when_day_not_found():
    topics_data = {"topics": [{"day": 1, "tier": "初級"}]}
    assert _resolve_tier(topics_data, 999) == "初級"


def test_resolve_tier_defaults_to_shokyu_when_tier_field_missing():
    topics_data = {"topics": [{"day": 1}]}
    assert _resolve_tier(topics_data, 1) == "初級"


def test_all_tiers_have_complete_palette_entries():
    for tier in ["初級", "中級", "上級"]:
        assert tier in PALETTES
        assert set(PALETTES[tier].keys()) == {"main", "accent", "dark"}
```

- [ ] **Step 3: テストを実行して失敗を確認する**

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
python3 -m pytest tests/test_generate_thumbnail.py -v
```

Expected: `ImportError: cannot import name '_resolve_tier'`（まだ実装していないため）

- [ ] **Step 4: generate_thumbnail.py にパレット定義とtier解決ロジックを実装する**

`generate_thumbnail.py` の `import` ブロック直後（`try: from PIL import ...` の後）に以下を追加:

```python
import yaml

PALETTES = {
    "初級": {"main": "#E8630A", "accent": "#F5A623", "dark": "#C44D00"},
    "中級": {"main": "#1E5FA8", "accent": "#4FA8D8", "dark": "#123F73"},
    "上級": {"main": "#4B2E83", "accent": "#7A5AC2", "dark": "#2E1B54"},
}


def _load_topics_data() -> dict:
    """generate_thumbnail.pyと同じディレクトリのtopics.yamlを読み込む"""
    topics_path = Path(__file__).parent / "topics.yaml"
    with open(topics_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_tier(topics_data: dict, day: int) -> str:
    """topics_dataからdayに対応するtierを返す。見つからなければ"初級" """
    for topic in topics_data.get("topics", []):
        if topic.get("day") == day:
            return topic.get("tier", "初級")
    return "初級"
```

- [ ] **Step 5: テストを再実行して通ることを確認する**

```bash
python3 -m pytest tests/test_generate_thumbnail.py -v
```

Expected: 4件 PASS

- [ ] **Step 6: create_thumbnail() をtier対応に書き換える**

`generate_thumbnail.py` の `create_thumbnail` 関数本体を以下に置き換える（`W, H = 1280, 670` の後、`# ベースカラー` セクションから `img = Image.new(...)` の直前まで）:

```python
    W, H = 1280, 670

    # tierに応じた配色を解決
    tier = _resolve_tier(_load_topics_data(), day)
    palette = PALETTES.get(tier, PALETTES["初級"])
    COLOR_BG_MAIN   = palette["main"]
    COLOR_BG_ACCENT = palette["accent"]
    COLOR_WHITE     = "#FFFFFF"
    COLOR_DARK      = palette["dark"]
```

（既存の `COLOR_BG_MAIN = "#E8630A"` などのハードコードされた4行を削除し、上記に置き換える）

- [ ] **Step 7: ロボット描画の目・口の色を背景メインカラーに連動させる**

`_draw_robot` の関数シグネチャと呼び出し元を変更する。

まず定義側（`def _draw_robot(draw, cx, cy, size, color):`）を:

```python
def _draw_robot(draw, cx, cy, size, color, face_color):
    """シンプルなロボットを描画する"""
    s = size

    # 頭
    head_x1 = cx - s * 0.35
    head_y1 = cy - s * 0.55
    head_x2 = cx + s * 0.35
    head_y2 = cy - s * 0.10
    draw.rounded_rectangle(
        [(head_x1, head_y1), (head_x2, head_y2)],
        radius=s * 0.1, fill=color
    )

    # 目（左）
    draw.ellipse([
        (cx - s * 0.22, cy - s * 0.45),
        (cx - s * 0.08, cy - s * 0.31)
    ], fill=face_color)

    # 目（右）
    draw.ellipse([
        (cx + s * 0.08, cy - s * 0.45),
        (cx + s * 0.22, cy - s * 0.31)
    ], fill=face_color)

    # 口
    draw.rounded_rectangle([
        (cx - s * 0.18, cy - s * 0.22),
        (cx + s * 0.18, cy - s * 0.14)
    ], radius=s * 0.04, fill=face_color)
```

（以降のアンテナ・胴体・腕・足の描画コードは変更なし、そのまま残す）

次に `create_thumbnail` 内の呼び出し箇所を:

```python
    # --- ロボットアイコン（左エリア） ---
    _draw_robot(draw, cx=220, cy=340, size=180, color=COLOR_WHITE, face_color=COLOR_BG_MAIN)
```

に変更する。

- [ ] **Step 8: 全テストを再実行して通ることを確認する**

```bash
python3 -m pytest tests/test_generate_thumbnail.py -v
```

Expected: 4件 PASS（Step 6, 7 の変更後も壊れていないこと）

- [ ] **Step 9: 実際に画像を生成して目視確認する**

```bash
python3 generate_thumbnail.py 1 "Claudeって何？ChatGPTと何が違うの？" /tmp/day01_check.png
```

Expected: `✅ サムネイル生成: /tmp/day01_check.png` と出力され、既存の初級オレンジ配色のまま生成される（`topics.yaml` の day1 には tier フィールドがまだ無いため `_resolve_tier` のデフォルト `"初級"` が適用される）。

- [ ] **Step 10: コミット**

```bash
git add generate_thumbnail.py tests/test_generate_thumbnail.py
git commit -m "Add tier-based color palettes to thumbnail generation"
```

---

## Task 3: 中級編（day31〜50）のトピックをtopics.yamlに追加する

**Files:**
- Modify: `topics.yaml`

**Interfaces:**
- Consumes: なし
- Produces: `topics.yaml` の `topics` リストに day31〜50 の20エントリ（`tier: "中級"`, `is_paid: false`, `price: null`）

- [ ] **Step 1: day30のエントリの直後に以下20エントリを追記する**

`topics.yaml` の `- day: 30` エントリ（`summary: "API・Claude Code..."` で終わる）の直後、`schedule:` セクションの直前に挿入:

```yaml
  - day: 31
    tier: "中級"
    title: "Projectsって何？チャットとは違う「まとめる」機能"
    keywords: ["Projects", "プロジェクト機能", "中級", "整理"]
    tone: "新機能を紹介するワクワク感で"
    length: "1400-1700"
    summary: "単発チャットとProjectsの違い、何のためにある機能かを実例で紹介"
    is_paid: false
    price: null

  - day: 32
    tier: "中級"
    title: "Projectsにファイルを入れてナレッジベースを作ってみた"
    keywords: ["ナレッジベース", "ファイル管理", "Projects", "活用"]
    tone: "実験・発見を共有する感じで"
    length: "1400-1700"
    summary: "資料や過去のやり取りをProjectsに集約し、自分専用の知識源にする方法"
    is_paid: false
    price: null

  - day: 33
    tier: "中級"
    title: "プロジェクトのカスタム指示で「専属アシスタント」を作る"
    keywords: ["カスタム指示", "Projects", "パーソナライズ", "活用"]
    tone: "具体的な設定例を見せながら"
    length: "1400-1700"
    summary: "プロジェクトごとにカスタム指示を設定し、用途特化のアシスタントを作る方法"
    is_paid: false
    price: null

  - day: 34
    tier: "中級"
    title: "プロジェクトを一週間使ってみてわかった向き不向き"
    keywords: ["Projects", "レビュー", "1週間", "使い分け"]
    tone: "正直で等身大の振り返り"
    length: "1300-1600"
    summary: "Projectsが向くタスク・単発チャットのままでいいタスクを実体験から整理"
    is_paid: false
    price: null

  - day: 35
    tier: "中級"
    title: "毎回同じ指示を書くのが面倒→カスタム指示に登録してみた"
    keywords: ["カスタム指示", "効率化", "設定", "活用"]
    tone: "あるある共感から入る"
    length: "1300-1600"
    summary: "毎回入力していた前置きをカスタム指示に登録し、手間を減らした体験"
    is_paid: false
    price: null

  - day: 36
    tier: "中級"
    title: "よく使うプロンプトをテンプレ化してみた"
    keywords: ["プロンプトテンプレート", "効率化", "ストック", "活用"]
    tone: "実用的でそのまま使えるノウハウ"
    length: "1400-1700"
    summary: "議事録・要約・添削などよく使うプロンプトをテンプレとしてストックする方法"
    is_paid: false
    price: null

  - day: 37
    tier: "中級"
    title: "定型業務をClaudeに任せる、を一歩進めてみる"
    keywords: ["定型業務", "自動化", "業務効率化", "実践"]
    tone: "実践レポート風"
    length: "1400-1700"
    summary: "単発の作業依頼から、複数ステップの定型業務を任せる工夫へ発展させる"
    is_paid: false
    price: null

  - day: 38
    tier: "中級"
    title: "「毎日やること」をClaudeと一緒に仕組み化する"
    keywords: ["ルーティン", "仕組み化", "習慣", "活用"]
    tone: "気づきを共有するトーン"
    length: "1400-1700"
    summary: "日々のルーティン業務をClaudeとの対話パターンとして仕組み化した話"
    is_paid: false
    price: null

  - day: 39
    tier: "中級"
    title: "ClaudeのWeb検索機能を使ってみた"
    keywords: ["Web検索", "最新情報", "コネクタ", "活用"]
    tone: "実験・発見を共有する感じで"
    length: "1400-1700"
    summary: "Web検索機能をオンにして、最新情報を踏まえた回答をもらう体験"
    is_paid: false
    price: null

  - day: 40
    tier: "中級"
    title: "Googleカレンダーと連携させてみた"
    keywords: ["Googleカレンダー", "コネクタ", "連携", "スケジュール管理"]
    tone: "ステップバイステップで丁寧に"
    length: "1400-1700"
    summary: "Googleカレンダーのコネクタを設定し、予定確認や調整をClaudeに任せる方法"
    is_paid: false
    price: null

  - day: 41
    tier: "中級"
    title: "Gmailと連携させてみた"
    keywords: ["Gmail", "コネクタ", "連携", "メール処理"]
    tone: "ステップバイステップで丁寧に"
    length: "1400-1700"
    summary: "Gmailのコネクタを設定し、メールの下書き作成や整理を任せてみた体験"
    is_paid: false
    price: null

  - day: 42
    tier: "中級"
    title: "コネクタを組み合わせて「秘書」っぽく使ってみた"
    keywords: ["コネクタ", "組み合わせ", "秘書化", "活用"]
    tone: "実験レポート風で楽しく"
    length: "1400-1700"
    summary: "カレンダーとメールのコネクタを組み合わせ、秘書のように使ってみた実践例"
    is_paid: false
    price: null

  - day: 43
    tier: "中級"
    title: "資料のたたき台をClaudeに作ってもらう"
    keywords: ["資料作成", "たたき台", "ビジネス文書", "活用"]
    tone: "実用的でそのまま使えるノウハウ"
    length: "1400-1700"
    summary: "企画書や提案資料の構成案・たたき台をClaudeに作らせるコツ"
    is_paid: false
    price: null

  - day: 44
    tier: "中級"
    title: "簡単なデータをClaudeに分析してもらった"
    keywords: ["データ分析", "簡易分析", "ビジネス", "活用"]
    tone: "発見や驚きを共有するトーン"
    length: "1400-1700"
    summary: "アンケート結果や売上データなど簡単なデータをClaudeに読み込ませて分析させた話"
    is_paid: false
    price: null

  - day: 45
    tier: "中級"
    title: "表計算とClaudeを組み合わせてみる"
    keywords: ["表計算", "スプレッドシート", "連携", "活用"]
    tone: "実践レポート風"
    length: "1400-1700"
    summary: "スプレッドシートのデータをClaudeに渡して集計・整形を手伝わせる方法"
    is_paid: false
    price: null

  - day: 46
    tier: "中級"
    title: "会議前の準備をClaudeに手伝ってもらう"
    keywords: ["会議準備", "業務効率化", "実例", "活用"]
    tone: "具体的でそのまま真似できる内容"
    length: "1400-1700"
    summary: "アジェンダ作成や論点整理など、会議前の準備をClaudeと一緒に進める方法"
    is_paid: false
    price: null

  - day: 47
    tier: "中級"
    title: "中級編を振り返って、変わったこと"
    keywords: ["振り返り", "中級編", "まとめ", "変化"]
    tone: "正直で等身大の振り返り"
    length: "1300-1600"
    summary: "中級編で学んだ機能を振り返り、初級編との違いや使い方の変化をまとめる"
    is_paid: false
    price: null

  - day: 48
    tier: "中級"
    title: "Claude Codeってプロジェクト機能と何が違うの？"
    keywords: ["Claude Code", "Projects", "違い", "比較"]
    tone: "フラットで実用的な比較"
    length: "1400-1700"
    summary: "チャット上のProjectsとClaude Codeの役割の違いを初心者目線で整理"
    is_paid: false
    price: null

  - day: 49
    tier: "中級"
    title: "Claude Codeで最初の一歩を踏み出してみる"
    keywords: ["Claude Code", "入門", "開発", "挑戦"]
    tone: "初めて触れる人目線で率直に"
    length: "1400-1700"
    summary: "Claude Codeを使って初めての簡単な作業を試した体験レポート"
    is_paid: false
    price: null

  - day: 50
    tier: "中級"
    title: "次は「作る」側へ。上級編の入り口で"
    keywords: ["上級編", "次のステップ", "開発", "予告"]
    tone: "前向きで背中を押すトーン"
    length: "1300-1600"
    summary: "中級編のまとめと、開発・自動化を扱う上級編への橋渡し"
    is_paid: false
    price: null

```

- [ ] **Step 2: YAML構文が壊れていないことを確認する**

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
python3 -c "import yaml; d = yaml.safe_load(open('topics.yaml')); print(len(d['topics']), 'topics loaded')"
```

Expected: `50 topics loaded`

- [ ] **Step 3: day31〜50が連番かつtierが正しいことを確認する**

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('topics.yaml'))
mid = [t for t in d['topics'] if 31 <= t['day'] <= 50]
print(len(mid), 'entries')
print(all(t['tier'] == '中級' for t in mid))
print([t['day'] for t in mid] == list(range(31, 51)))
"
```

Expected: `20 entries` / `True` / `True`

- [ ] **Step 4: コミット**

```bash
git add topics.yaml
git commit -m "Add day31-50 intermediate tier topics"
```

---

## Task 4: 上級編（day51〜70）のトピックをtopics.yamlに追加する

**Files:**
- Modify: `topics.yaml`

**Interfaces:**
- Consumes: なし
- Produces: `topics.yaml` の `topics` リストに day51〜70 の20エントリ（`tier: "上級"`, `is_paid: true`, `price: 380`）

- [ ] **Step 1: day50のエントリの直後に以下20エントリを追記する**

`topics.yaml` の `- day: 50` エントリの直後、`schedule:` セクションの直前に挿入:

```yaml
  - day: 51
    tier: "上級"
    title: "Claude Codeで小さなツールを作ってみる"
    keywords: ["Claude Code", "開発", "実践", "上級"]
    tone: "実践レポート風、手を動かした過程を丁寧に"
    length: "1600-2000"
    summary: "Claude Codeで簡単なツールを実際に一つ作り上げるまでの過程を解説"
    is_paid: true
    price: 380

  - day: 52
    tier: "上級"
    title: "サブエージェントって何？役割分担させてみた"
    keywords: ["サブエージェント", "Claude Code", "役割分担", "実践"]
    tone: "実験・発見を共有する感じで"
    length: "1600-2000"
    summary: "サブエージェント機能を使い、タスクを役割ごとに分担させた実践例"
    is_paid: true
    price: 380

  - day: 53
    tier: "上級"
    title: "スキルを自作して、いつもの作業を型にする"
    keywords: ["スキル", "自作", "Claude Code", "型化"]
    tone: "具体的な手順を見せながら"
    length: "1600-2000"
    summary: "繰り返し行う作業をスキルとして自作し、再利用できる形にする方法"
    is_paid: true
    price: 380

  - day: 54
    tier: "上級"
    title: "エラーが出たときClaudeとどう向き合うか"
    keywords: ["デバッグ", "エラー対応", "Claude Code", "実践"]
    tone: "正直な試行錯誤を見せる"
    length: "1600-2000"
    summary: "開発中に出たエラーをClaudeと一緒に切り分けて解決した実例"
    is_paid: true
    price: 380

  - day: 55
    tier: "上級"
    title: "一週間開発してみてわかったこと"
    keywords: ["開発", "1週間", "振り返り", "上級"]
    tone: "正直で等身大の振り返り"
    length: "1500-1800"
    summary: "Claude Codeで一週間開発してみて感じた向き不向きや学びを振り返る"
    is_paid: true
    price: 380

  - day: 56
    tier: "上級"
    title: "このnote自動化システム、実は自分で作った"
    keywords: ["自動化", "自作", "note", "公開"]
    tone: "種明かしをするような楽しいトーン"
    length: "1600-2000"
    summary: "本シリーズの記事・サムネイル自動生成システム自体の全体像を公開する"
    is_paid: true
    price: 380

  - day: 57
    tier: "上級"
    title: "スケジュールタスクを設計するときに考えたこと"
    keywords: ["スケジュールタスク", "設計", "自動化", "実践"]
    tone: "設計判断の理由を丁寧に説明する"
    length: "1600-2000"
    summary: "定期実行タスクを組む上で考えた設計上の判断ポイントを解説"
    is_paid: true
    price: 380

  - day: 58
    tier: "上級"
    title: "記事とサムネイルを自動生成する仕組みを解説する"
    keywords: ["自動生成", "画像処理", "仕組み", "解説"]
    tone: "技術解説を噛み砕いて"
    length: "1700-2000"
    summary: "記事執筆とサムネイル画像生成を自動化する仕組みの中身を具体的に解説"
    is_paid: true
    price: 380

  - day: 59
    tier: "上級"
    title: "自動化システムのハマりどころと直し方"
    keywords: ["トラブルシューティング", "自動化", "実例", "対処法"]
    tone: "失敗談を正直に共有する"
    length: "1600-2000"
    summary: "自動化を組む中で実際にハマった問題とその直し方を具体例で紹介"
    is_paid: true
    price: 380

  - day: 60
    tier: "上級"
    title: "自動化を仕組み化してわかった「任せる」ということ"
    keywords: ["自動化", "振り返り", "仕組み化", "気づき"]
    tone: "気づきを共有するトーン"
    length: "1500-1800"
    summary: "自動化を作る過程で得た「何を任せ、何を自分で見るか」の判断軸を振り返る"
    is_paid: true
    price: 380

  - day: 61
    tier: "上級"
    title: "MCPサーバーって自分で作れるの？"
    keywords: ["MCP", "サーバー自作", "拡張", "入門"]
    tone: "疑問から入って解き明かすトーン"
    length: "1600-2000"
    summary: "MCPサーバーを自作する際に必要な考え方の基礎を解説"
    is_paid: true
    price: 380

  - day: 62
    tier: "上級"
    title: "簡単なMCPサーバーを作ってみた"
    keywords: ["MCP", "サーバー自作", "実践", "上級"]
    tone: "実践レポート風、手を動かした過程を丁寧に"
    length: "1700-2000"
    summary: "実際に簡単なMCPサーバーを一つ作り上げる過程を実況形式で紹介"
    is_paid: true
    price: 380

  - day: 63
    tier: "上級"
    title: "独自コネクタを設計するときの考え方"
    keywords: ["コネクタ", "設計", "MCP", "実践"]
    tone: "設計判断の理由を丁寧に説明する"
    length: "1600-2000"
    summary: "独自コネクタを設計する際に考慮すべきポイントを整理して解説"
    is_paid: true
    price: 380

  - day: 64
    tier: "上級"
    title: "外部ツールとClaudeをつなぐときの注意点"
    keywords: ["外部連携", "注意点", "セキュリティ", "実践"]
    tone: "真面目だけど難しくなりすぎない"
    length: "1600-2000"
    summary: "外部ツールとの連携で気をつけたい権限管理やセキュリティ上の注意点"
    is_paid: true
    price: 380

  - day: 65
    tier: "上級"
    title: "MCPを作ってみて感じた可能性と限界"
    keywords: ["MCP", "振り返り", "可能性", "限界"]
    tone: "正直で等身大の振り返り"
    length: "1500-1800"
    summary: "MCPサーバーを作ってみた経験から見えた可能性と、現状の限界を整理"
    is_paid: true
    price: 380

  - day: 66
    tier: "上級"
    title: "Claudeで副業を始めてみた話"
    keywords: ["副業", "収益化", "実例", "体験談"]
    tone: "正直で等身大の体験談"
    length: "1600-2000"
    summary: "Claudeを活用して副業を始めた実体験と、そこで得た学びを共有する"
    is_paid: true
    price: 380

  - day: 67
    tier: "上級"
    title: "仕事にClaudeを本格導入するときの進め方"
    keywords: ["業務導入", "本格活用", "進め方", "実例"]
    tone: "実用的でそのまま使えるノウハウ"
    length: "1600-2000"
    summary: "個人利用から仕事での本格導入へ移行する際の進め方を実例で紹介"
    is_paid: true
    price: 380

  - day: 68
    tier: "上級"
    title: "チームにClaudeを広めるときにぶつかった壁"
    keywords: ["チーム展開", "導入", "課題", "実例"]
    tone: "正直な試行錯誤を見せる"
    length: "1600-2000"
    summary: "チームや周囲にClaude活用を広める際に直面した課題とその乗り越え方"
    is_paid: true
    price: 380

  - day: 69
    tier: "上級"
    title: "有料記事を書くようになって変わったこと"
    keywords: ["有料化", "note", "マネタイズ", "振り返り"]
    tone: "正直で等身大の振り返り"
    length: "1500-1800"
    summary: "記事を有料化してから執筆スタンスや読者との関係がどう変わったかを共有"
    is_paid: true
    price: 380

  - day: 70
    tier: "上級"
    title: "上級編、ここまでの振り返りとこれから"
    keywords: ["振り返り", "上級編", "まとめ", "今後"]
    tone: "前向きで背中を押すトーン"
    length: "1500-1800"
    summary: "上級編前半の振り返りと、この先扱っていきたいテーマの予告"
    is_paid: true
    price: 380

```

- [ ] **Step 2: YAML構文が壊れていないことを確認する**

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
python3 -c "import yaml; d = yaml.safe_load(open('topics.yaml')); print(len(d['topics']), 'topics loaded')"
```

Expected: `70 topics loaded`

- [ ] **Step 3: day51〜70が連番かつtier/is_paid/priceが正しいことを確認する**

```bash
python3 -c "
import yaml
d = yaml.safe_load(open('topics.yaml'))
adv = [t for t in d['topics'] if 51 <= t['day'] <= 70]
print(len(adv), 'entries')
print(all(t['tier'] == '上級' and t['is_paid'] is True and t['price'] == 380 for t in adv))
print([t['day'] for t in adv] == list(range(51, 71)))
"
```

Expected: `20 entries` / `True` / `True`

- [ ] **Step 4: コミット**

```bash
git add topics.yaml
git commit -m "Add day51-70 advanced tier topics (paid)"
```

---

## Task 5: サムネイル配色の動作確認

コードとデータの両方が揃った状態で、中級・上級それぞれのサムネイルが意図した配色で生成されることを実際に目視確認する。

**Files:**
- なし（確認のみ、成果物はコミットしない）

**Interfaces:**
- Consumes: `generate_thumbnail.py` の `create_thumbnail(day, title, output_path)`（Task 2で実装済み）、`topics.yaml` の day31/day51 エントリ（Task 3, 4で追加済み）

- [ ] **Step 1: 初級（day1）が従来通りオレンジで生成されることを確認する**

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
python3 generate_thumbnail.py 1 "Claudeって何？\nChatGPTと何が違うの？" /tmp/check_day01.png
```

Expected: オレンジ系（`#E8630A`背景）で生成される

- [ ] **Step 2: 中級（day31）が青系で生成されることを確認する**

```bash
python3 generate_thumbnail.py 31 "Projectsって何？\n「まとめる」機能" /tmp/check_day31.png
```

Expected: 青系（`#1E5FA8`背景）で生成される。ロボットの目・口も背景メインカラーと同じ青になっている。

- [ ] **Step 3: 上級（day51）が紫系で生成されることを確認する**

```bash
python3 generate_thumbnail.py 51 "Claude Codeで\n小さなツールを作ってみる" /tmp/check_day51.png
```

Expected: 紫系（`#4B2E83`背景）で生成される

- [ ] **Step 4: 3枚を並べて目視確認する（Readツールで画像を開く）**

`/tmp/check_day01.png`, `/tmp/check_day31.png`, `/tmp/check_day51.png` を確認し、以下をチェックする:
- 3枚とも背景色以外のレイアウト（ロボット位置・Day番号・タイトル配置）が同一であること
- ロボットの目・口の色が各背景のメインカラーと一致していること
- フォント・ロボットの形状が3枚とも同一であること

- [ ] **Step 5: 確認用の一時ファイルを削除する**

```bash
rm /tmp/check_day01.png /tmp/check_day31.png /tmp/check_day51.png
```

（このタスクはコミット不要 — Task 2, 3, 4 のコードとデータの動作確認のみ）

---

## Task 6: ルーチンの指示文を更新する

Claude.ai の「Claude学習note記事の自動生成」ルーチン（`https://claude.ai/code/routines/trig_01WMmby2zbXuYzUqUvv2QFM6`）の指示文に、中級・上級の執筆トーン補足を追記する。ブラウザ操作で行う。

**Files:**
- なし（Claude.ai UI上の設定変更）

**Interfaces:**
- Consumes: なし
- Produces: ルーチンの「指示」テキストが更新された状態

- [ ] **Step 1: ルーチン編集画面を開く**

ブラウザで `https://claude.ai/code/routines/trig_01WMmby2zbXuYzUqUvv2QFM6` を開き、指示文の編集モードに入る。

- [ ] **Step 2: 既存の指示文の末尾に以下を追記する**

```
【難易度別の執筆トーン補足】
- tier が "中級"（day31〜50）の場合: 初級で基礎を学んだ読者向けに、実際に手を動かして試す実践的なトーンで書く。「まだ使ったことはないけど存在は知っている機能」を試す体験談として書く。
- tier が "上級"（day51〜）の場合: 開発・自動化・収益化など、有料記事として読む価値のある踏み込んだ内容にする。手順だけでなく「なぜそうしたか」の判断理由も書く。
- topics.yamlの該当dayエントリに is_paid: true がある場合、その記事は有料記事の対象であることを念頭に置いて執筆する（実際のnote上での価格設定・公開は引き続き手動で行う）。
```

- [ ] **Step 3: 保存する**

編集内容を保存し、保存後のページを再読み込みして指示文が反映されていることを確認する。

- [ ] **Step 4: ルーチンの一時停止ステータスについてユーザーに確認する**

現在「一時停止中」のままにするか、再開するかをユーザーに確認する（本タスクでは変更しない — 別途ユーザーの意思決定が必要）。

---

## 全タスク完了後: リモートへのpush

全タスクのコミットが完了したら、ユーザーに確認した上で `git push origin main` を実行する。push前に以下を確認する:

```bash
cd /Users/y-shingo/Desktop/claude-study/note/claude-note-auto-post
git log --oneline origin/main..HEAD
git status
```

コミット内容に意図しない変更（特に認証情報等）が含まれていないことを確認してからpushする。
