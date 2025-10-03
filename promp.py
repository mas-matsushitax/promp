import os
import glob
import datetime
from pathlib import Path
import click
import re
import pathspec
import json

# --- 定数定義 ---
TEMPLATE_DIR = ".promp-template"
INPUT_DIR = ".promp-in"
OUTPUT_DIR = ".promp-out"
SPEC_FILE = "SPEC.md"
GITIGNORE_FILE = ".gitignore"

DEFAULT_TEMPLATE_CONTENT = """あなたは、エクスパートプログラマーです。
以下の「ユーザーの指示」と「既存ファイル」を参考に、変更内容を「JSON差分形式」で出力してください。
※コード中のコメントは日本語で作成してください。

==== JSON差分形式のルール ====

* 変更内容は、単一のJSONオブジェクトとして出力し、必ず```json コードブロックで囲んでください。
* JSONオブジェクトには、changesというキーを持たせ、その値は変更点を記述したオブジェクトの配列とします。
* 各変更オブジェクトには、以下のキーを含めてください。
  * file_path: (文字列) 対象となるファイルのパス。
  * operation: (文字列) 操作の種類。create (新規作成), update (上書き更新), delete (削除) のいずれかを指定。
  * content: (文字列) createまたはupdateの場合に、ファイルの新しい内容全体を記述。JSON文字列として正しくエスケープしてください（改行は`\\n`など）。
* 重要: JSONコードブロック以外の説明文は不要です。

---- 出力例 ----

```json
{
  "changes": [
    {
      "file_path": "src/new_feature.py",
      "operation": "create",
      "content": "def new_function():\\n    pass)\\n"
    },
    {
      "file_path": "main.py",
      "operation": "update",
      "content": "import src.new_feature\\n\\nsrc.new_feature.new_function()\\n"
    },
    {
      "file_path": "docs/old_spec.txt",
      "operation": "delete"
    }
  ]
}
```

==== ユーザーの指示 ====

※※ ここに指示を書いて、LLMサイトにコピペしてください。※※

==== 既存ファイル ====
{existing_files}
"""

SPEC_TEMPLATE_CONTENT = """# ツール名: （ここにツール名を書く）

## このツールは何？ (目的)
* (例：指定したディレクトリ内の画像を一括でリサイズするツール)
* (例：定型文のスニペットを管理し、簡単にコピーできるようにするツール)

---

## コマンド仕様

### 基本コマンド: `(command_name) [sub_command] [arguments] --options`

---

### (機能名1)
(例：タスクを追加する)

* **コマンド:** `todo add "新しいタスク"`
* **引数 (Arguments):**
    * `"タスク内容"`: (必須) 追加したいタスクを文字列で指定。
* **オプション (Options):**
    * `-p, --priority <レベル>`: (任意) 優先度を1〜3で指定。デフォルトは2。
* **実行例:**
    ```sh
    # 優先度を指定してタスクを追加
    todo add "ドキュメントを書く" --priority 1
    ```

---

### (機能名2)
(例：タスクを一覧表示する)

* **コマンド:** `todo list`
* **引数 (Arguments):**
    * なし
* **オプション (Options):**
    * `--all`: (任意) 完了済みのタスクも全て表示する。
* **実行例:**
    ```sh
    # 未完了のタスクを一覧表示
    todo list
    ```

---

### (機能名3)
(必要に応じてセクションをコピーして追記)

---

## 使用技術
* **言語:** (例: Python, Go, Rust, Node.js)
* **主要ライブラリ:** (例: argparse, click, cobra)
"""

GITIGNORE_CONTENT = """
# for promp
.promp-out
.promp-in
"""

# --- CLIの定義 ---
@click.group()
def promp():
    """LLMのWeb AIをコーディングエージェントとして使うための便利ツール"""
    pass

@promp.command()
@click.option("-s", "--spec", is_flag=True, help="SPEC.mdファイルを出力します。")
def init(spec):
    """カレントフォルダにprompで使用するファイルやフォルダを追加する"""
    click.echo("prompの初期化を開始します。")

    # フォルダ内のファイル存在チェック
    if any(os.scandir('.')):
        click.echo(
            click.style(
                "警告: カレントフォルダには既にファイルまたはフォルダが存在します。", fg="yellow"
            )
        )
        # 作成対象のリストを動的に作成
        created_items = [f"{TEMPLATE_DIR}/", GITIGNORE_FILE]
        if spec:
            created_items.append(SPEC_FILE)
        click.echo(f"以下のファイル/フォルダを作成・追記します: {', '.join(created_items)}")

        if not click.confirm("処理を続行しますか？"):
            click.echo("処理を中断しました。")
            return

    # 1. .promp-template ディレクトリとテンプレートファイルの作成
    template_path = Path(TEMPLATE_DIR)
    template_path.mkdir(exist_ok=True)
    (template_path / "default.txt").write_text(DEFAULT_TEMPLATE_CONTENT, encoding="utf-8")
    (template_path / "spec.txt").write_text(SPEC_TEMPLATE_CONTENT, encoding="utf-8")
    click.echo(f"✅ フォルダ '{TEMPLATE_DIR}' とテンプレートファイルを作成しました。")

    # 2. .gitignore の作成または追記
    gitignore_path = Path(GITIGNORE_FILE)
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if GITIGNORE_CONTENT.strip() not in content:
            with gitignore_path.open("a", encoding="utf-8") as f:
                f.write(GITIGNORE_CONTENT)
            click.echo(f"✅ '{GITIGNORE_FILE}' に設定を追記しました。")
        else:
            click.echo(f"ℹ️ '{GITIGNORE_FILE}' には既に設定が存在します。")
    else:
        gitignore_path.write_text(GITIGNORE_CONTENT.strip(), encoding="utf-8")
        click.echo(f"✅ '{GITIGNORE_FILE}' を作成しました。")

    # 3. SPEC.md の作成 (オプションが指定された場合のみ)
    if spec:
        Path(SPEC_FILE).write_text(SPEC_TEMPLATE_CONTENT, encoding="utf-8")
        click.echo(f"✅ '{SPEC_FILE}' を作成しました。")

    click.echo(click.style("初期化が完了しました。", fg="green"))


@promp.command()
@click.argument("file_patterns", nargs=-1, required=True)
@click.option("-t", "--template", default="default", help="プロンプト作成時のテンプレート名を指定します。")
@click.option("-e", "--exclude", multiple=True, help="除外するファイルパターンを指定します。ワイルドカード使用可。")
def out(file_patterns, template, exclude):
    """指定されたファイルを埋め込んだプロンプトを出力する"""
    # 0. テンプレートファイルのパスを解決
    template_file = Path(TEMPLATE_DIR) / f"{template}.txt"
    if not template_file.exists():
        click.echo(click.style(f"エラー: テンプレート '{template_file}' が見つかりません。", fg="red"))
        return

    # 1. ワイルドカードを展開して、対象ファイルリストを収集
    all_files = []
    for pattern in file_patterns:
        # globでワイルドカードに一致するファイルを探す
        matched_files = glob.glob(pattern, recursive=True)
        all_files.extend(matched_files)

    # 重複を除外してソート
    unique_files = sorted(list(set(all_files)))

    # 2. .gitignoreと--excludeオプションでファイルを除外
    # .gitignoreの内容でフィルタリング
    gitignore_path = Path(GITIGNORE_FILE)
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            # GitWildMatchPatternの代わりに 'gitwildmatch' を文字列として渡す
            gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
            ignored_files = set(gitignore_spec.match_files(unique_files))
            if ignored_files:
                click.echo(f"ℹ️ .gitignore に基づき {len(ignored_files)} 個のファイルを除外します。")
                unique_files = [f for f in unique_files if f not in ignored_files]

    # --exclude オプションで指定されたパターンでフィルタリング
    if exclude:
        # GitWildMatchPatternの代わりに 'gitwildmatch' を文字列として渡す
        exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude)
        excluded_files_by_opt = set(exclude_spec.match_files(unique_files))
        if excluded_files_by_opt:
            click.echo(f"ℹ️ --exclude オプションに基づき {len(excluded_files_by_opt)} 個のファイルを除外します。")
            unique_files = [f for f in unique_files if f not in excluded_files_by_opt]

    if not unique_files:
        click.echo(click.style("エラー: 指定されたパターンに一致するファイルが見つかりませんでした。", fg="red"))
        return
    
    click.echo(f"ℹ️ {len(unique_files)}個のファイルを処理対象とします。内容を読み込みます...")

    # 3. 各ファイルの内容をヘッダー付きでリストに格納
    existing_files_content_list = []
    for file_path_str in unique_files:
        file_path = Path(file_path_str)
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8")
                # カレントディレクトリからの相対パスを使用
                relative_path = file_path.as_posix()
                header = f"---- {relative_path} ----"
                # ヘッダーとファイル内容を結合してリストに追加
                existing_files_content_list.append(f"{header}\n{content}")
                click.echo(f"  - 読み込み成功: {relative_path}")
            except Exception as e:
                click.echo(click.style(f"  - 読み込み失敗: {relative_path} ({e})", fg="yellow"))

    # 4. テンプレートにファイル内容を埋め込む
    template_content = template_file.read_text(encoding="utf-8")
    
    # ファイル間の区切りとして改行を2つ入れる
    files_as_string = "\n\n".join(existing_files_content_list)
    
    final_prompt = template_content.replace("{existing_files}", files_as_string)

    # 5. 結果を出力ファイルと入力ファイル（空）に書き込む
    # タイムスタンプを生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # .promp-out フォルダと出力ファイルの準備
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    output_filename = f"out-{timestamp}.txt"
    output_path = Path(OUTPUT_DIR) / output_filename
    output_path.write_text(final_prompt, encoding="utf-8")
    click.echo(click.style(f"\nプロンプトを '{output_path}' に出力しました。", fg="green"))

    # .promp-in フォルダと入力用の空ファイルの準備
    Path(INPUT_DIR).mkdir(exist_ok=True)
    input_filename = f"in-{timestamp}.txt"
    input_path = Path(INPUT_DIR) / input_filename
    # 空ファイルを作成
    input_path.write_text("", encoding="utf-8")
    click.echo(click.style(f"LLMの出力を貼り付けるための空ファイル '{input_path}' を作成しました。", fg="green"))

def _find_latest_input_file():
    """'.promp-in' ディレクトリ内の最新の入力ファイルを検索するヘルパー関数"""
    input_dir_path = Path(INPUT_DIR)
    if not input_dir_path.is_dir():
        click.echo(click.style(f"エラー: '{INPUT_DIR}' ディレクトリが見つかりません。", fg="red"))
        return None

    in_files = sorted(list(input_dir_path.glob("in-*.txt")), reverse=True)
    if not in_files:
        click.echo(click.style(f"エラー: '{INPUT_DIR}' 内に適用対象のファイルが見つかりません。", fg="red"))
        return None
        
    return in_files[0]

@promp.command()
@click.argument("apply_file", type=click.Path(dir_okay=False), required=False)
def apply(apply_file):
    """LLMが出力したJSON差分ファイルを適用する"""
    target_file_path = None

    if apply_file is None:
        click.echo(f"ℹ️ ファイルが指定されていないため、'{INPUT_DIR}/' 内の最新ファイルを検索します...")
        target_file_path = _find_latest_input_file()
        if not target_file_path:
            return
        click.echo(click.style(f"✅ 最新ファイル '{target_file_path}' を適用対象とします。", fg="green"))
    else:
        target_file_path = Path(apply_file)

    if not target_file_path.exists():
        click.echo(click.style(f"エラー: ファイル '{target_file_path}' が見つかりません。", fg="red"))
        return
    
    click.echo(f"📖 ファイル '{target_file_path}' を読み込んで差分情報を解析します...")
    
    try:
        content = target_file_path.read_text(encoding="utf-8")
        # LLM出力の```json ... ```ブロックからJSON部分を抽出
        match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # ブロックがない場合は、ファイル全体をJSONとして解釈しようと試みる
            json_str = content
        
        data = json.loads(json_str)
        changes = data.get("changes", [])
    except json.JSONDecodeError:
        click.echo(click.style("エラー: ファイルのJSON形式が正しくありません。", fg="red"))
        return
    except Exception as e:
        click.echo(click.style(f"エラー: ファイルの読み込み中に予期せぬ問題が発生しました: {e}", fg="red"))
        return

    if not changes:
        click.echo(click.style("警告: 適用する変更がJSON内に見つかりませんでした。", fg="yellow"))
        return

    click.echo("\n以下の変更が適用されます：")
    for change in changes:
        op = change.get('operation', '不明').upper()
        path = change.get('file_path', 'パス不明')
        if op == "CREATE":
            click.echo(click.style(f"  [CREATE] {path}", fg="green"))
        elif op == "UPDATE":
            click.echo(click.style(f"  [UPDATE] {path}", fg="yellow"))
        elif op == "DELETE":
            click.echo(click.style(f"  [DELETE] {path}", fg="red"))

    if not click.confirm("\n処理を続行しますか？"):
        click.echo("処理を中断しました。")
        return

    click.echo("\nパッチの適用を開始します...")
    for change in changes:
        op = change.get('operation')
        path_str = change.get('file_path')
        
        if not op or not path_str:
            click.echo(click.style("  - スキップ: 'operation'または'file_path'が不正です。", fg="yellow"))
            continue

        file_path = Path(path_str)
        
        try:
            if op == "create":
                if file_path.exists():
                    click.echo(click.style(f"  - 警告: 作成予定のファイル {path_str} は既に存在するためスキップします。", fg="yellow"))
                    continue
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(change.get("content", ""), encoding="utf-8")
                click.echo(click.style(f"  ✅ [CREATE] {path_str} を作成しました。", fg="green"))
            
            elif op == "update":
                if not file_path.exists():
                    click.echo(click.style(f"  - 警告: 更新予定のファイル {path_str} が見つからないため新規作成します。", fg="yellow"))
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(change.get("content", ""), encoding="utf-8")
                click.echo(click.style(f"  ✅ [UPDATE] {path_str} を更新しました。", fg="green"))

            elif op == "delete":
                if file_path.exists():
                    file_path.unlink()
                    click.echo(click.style(f"  ✅ [DELETE] {path_str} を削除しました。", fg="green"))
                else:
                    click.echo(click.style(f"  - 警告: 削除予定のファイル {path_str} は存在しません。", fg="yellow"))
            
            else:
                click.echo(click.style(f"  - 警告: 未知の操作 '{op}' のためスキップします。", fg="yellow"))

        except Exception as e:
            click.echo(click.style(f"  ❌ [{op.upper()}] {path_str} の処理中にエラーが発生しました: {e}", fg="red"))

    click.echo(click.style("\nパッチの適用が完了しました。", fg="green"))


if __name__ == '__main__':
    promp()
