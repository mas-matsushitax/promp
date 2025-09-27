import os
import glob
import subprocess
import datetime
from pathlib import Path
import click

# --- 定数定義 ---
TEMPLATE_DIR = ".promp-template"
OUTPUT_DIR = ".promp-out"
SPEC_FILE = "PROMP-SPEC.md"
GITIGNORE_FILE = ".gitignore"

DEFAULT_TEMPLATE_CONTENT = """あなたは、エクスパートプログラマーです。
以下の「既存ファイル」を参考に、下記の「ユーザーの指示」に従って、コードを作成して、説明と差分ファイル（Unified形式）を作成してください。
差分ファイルは、一発でコピーできるようにしてください。
※説明と差分ファイル中のコメントは日本語で作成してください。

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
"""

# --- CLIの定義 ---
@click.group()
def promp():
    """LLMのWeb AIをコーディングエージェントとして使うための便利ツール"""
    pass

@promp.command()
def init():
    """カレントフォルダにprompで使用するファイルやフォルダを追加する"""
    click.echo("prompの初期化を開始します。")

    # フォルダ内のファイル存在チェック
    if any(os.scandir('.')):
        click.echo(
            click.style(
                "警告: カレントフォルダには既にファイルまたはフォルダが存在します。", fg="yellow"
            )
        )
        click.echo(f"以下のファイル/フォルダを作成・追記します: {TEMPLATE_DIR}/, {GITIGNORE_FILE}, {SPEC_FILE}")
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

    # 3. PROMP-SPEC.md の作成
    Path(SPEC_FILE).write_text(SPEC_TEMPLATE_CONTENT, encoding="utf-8")
    click.echo(f"✅ '{SPEC_FILE}' を作成しました。")
    click.echo(click.style("初期化が完了しました。", fg="green"))


@promp.command()
@click.argument("file_patterns", nargs=-1, required=True)
@click.option("-t", "--template", default="default", help="プロンプト作成時のテンプレート名を指定します。")
def out(file_patterns, template):
    """指定されたファイルを埋め込んだプロンプトを出力する"""
    # テンプレートファイルのパスを解決
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

    if not unique_files:
        click.echo(click.style("エラー: 指定されたパターンに一致するファイルが見つかりませんでした。", fg="red"))
        return
    
    click.echo(f"ℹ️ {len(unique_files)}個のファイルが見つかりました。内容を読み込みます...")

    # 2. 各ファイルの内容をヘッダー付きでリストに格納
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

    # 3. テンプレートにファイル内容を埋め込む
    template_content = template_file.read_text(encoding="utf-8")
    
    # ファイル間の区切りとして改行を2つ入れる
    files_as_string = "\n\n".join(existing_files_content_list)
    
    final_prompt = template_content.replace("{existing_files}", files_as_string)

    # 4. 結果を出力ファイルに書き込む
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_filename = f"out-{timestamp}.txt"
    output_path = Path(OUTPUT_DIR) / output_filename
    output_path.write_text(final_prompt, encoding="utf-8")

    click.echo(click.style(f"\nプロンプトを '{output_path}' に出力しました。", fg="green"))


@promp.command()
@click.argument("patch_file", type=click.Path(exists=True))
def patch(patch_file):
    """Unified形式の差分ファイルをカレントフォルダに適用する"""
    click.echo(f"差分ファイル '{patch_file}' を適用します...")
    try:
        # patchコマンドを実行。-p1でディレクトリ階層を一つ無視する
        result = subprocess.run(
            ["patch", "-p1"], 
            stdin=open(patch_file, 'r'), 
            capture_output=True, 
            text=True,
            check=True
        )
        click.echo(click.style("パッチの適用に成功しました。", fg="green"))
        if result.stdout:
            click.echo("---出力---")
            click.echo(result.stdout)
    except FileNotFoundError:
        click.echo(click.style("エラー: 'patch' コマンドが見つかりません。システムにインストールされているか確認してください。", fg="red"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style("エラー: パッチの適用に失敗しました。", fg="red"))
        click.echo("---エラー内容---")
        click.echo(e.stderr)

if __name__ == '__main__':
    promp()