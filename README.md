# ツール名: promp (読み方: プロンプ)

## このツールは何？ (目的)
* LLMのWeb UIをコーディングエージェントとして活用するための支援機能を提供する。

---

## インストール

### 前提条件

- Python 3.10以上
- `uv` pythonパッケージマネージャー（pipを使うなら必要ありません）
- `git` githubからモジュールを取得（curlを使うなら必要ありません）

### リモートインストール

```bash
uv tool install git+https://github.com/mas-matsushitax/promp.git
```

### ローカルインストール

```bash
curl -L https://github.com/mas-matsushitax/promp/archive/refs/heads/main.zip --output promp-main.zip
unzip promp-main.zip
uv tool install ./promp-main
```

### pipを使用する場合

```bash
pip install git+https://github.com/mas-matsushitax/promp.git
```

または

```bash
curl -L https://github.com/mas-matsushitax/promp/archive/refs/heads/main.zip --output promp-main.zip
unzip promp-main.zip
pip install ./promp-main
```

### （参考）prompのアンインストール

prompが必要なくなったら、以下のコマンドでアンインストールできます。

```sh
uv tool uninstall promp
```

または

```sh
pip uninstall promp
```

---

## コマンド仕様

### 基本コマンド: 
`promp [sub_command] [arguments] --options`

---

### 初期化
カレントフォルダにprompで使用するファイルやフォルダを追加する

* **コマンド:** `promp init`
* **引数 (Arguments):**
    * なし
* **オプション (Options):**
    * なし
* **実行例:**
    ```sh
    # 基本的なファイル／フォルダを作成
    promp init
    ```
* **仕様:**

    カレントフォルダに以下のフォルダ／ファイルを配置します。
    
    (D)-> フォルダ (F)-> ファイル
    ```
    .promp-template(D)
    L default.txt(F)
    L spec.txt(F)
    .gitignore(F)
    ```

    .gitignoreの中身は以下。既存の.gitignoreがあれば、以下の行を追記します。
    ```
    # for promp
    .promp-out
    .promp-in
    ```

    すでにカレントフォルダに一つ以上のファイルやフォルダが存在する場合は、作成・追記対象を表示し、ユーザーに処理続行の確認を求めます。

---

### 出力
プロンプトを出力する

* **コマンド:** `promp out ["既存ファイルパス" ...]`
* **引数 (Arguments):**
    * `"既存ファイルパス"`: プロンプトに加えたいファイルパス。複数可、ワイルドカード可。省略可。
* **オプション (Options):**
    * `-t, --template <テンプレート名>`: (任意) プロンプト作成時のテンプレート名を指定（デフォルト: `default`）。
    * `-e, --exclude <パターン>`: (任意, 複数指定可) 除外するファイルパターンを指定。ワイルドカード可。
* **実行例:**
    ```sh
    # カレント配下のすべての.pyファイルをプロンプトに加える
    promp out ./**/*.py

    # 特定テンプレートを使用し、node_modules配下は除外
    promp out ./src/**/*.ts -t mytemplate -e "**/node_modules/**"
    ```
* **仕様:**
    
    - テンプレートは `.promp-template/<テンプレート名>.txt` を使用します。存在しない場合はエラーになります。
    - 引数が指定されていない場合、既存ファイルの埋め込みは行わず、テンプレートのみで出力します（注意メッセージを表示）。
    - パターン展開後の対象ファイルから、以下を除外します。
        1. `.gitignore` のルールで無視されるファイル
        2. `-e/--exclude` で指定したパターンに一致するファイル
    - 各ファイルは以下のヘッダー付きで埋め込みます（相対パス）。
        ```
        ---- パス/to/file ----
        ファイルの内容
        ```
    - 出力先: `.promp-out/out-YYYYMMDD-HHMMSS.txt`
    - 同時に、LLMの出力を貼り付ける空ファイルを作成: `.promp-in/in-YYYYMMDD-HHMMSS.txt`

---

### 適用
LLMが出力した**JSON差分形式**のファイルをカレントフォルダに適用する

* **コマンド:** `promp apply ["LLMからの出力ファイルパス"]`
* **引数 (Arguments):**
    * `"LLMからの出力ファイルパス"`: (任意) LLMが出力したファイル。省略時は`.promp-in/`内の最新ファイルを自動選択。
* **オプション (Options):**
    なし
* **実行例:**
    ```sh
    # 最新のLLMの出力を自動で適用する
    promp apply

    # 特定のファイルを指定して適用する
    promp apply .promp-in/in-20250927-190721.txt
    ```
* **仕様:**
    
    - 指定（または自動選択）したファイルを読み込み、以下の手順でJSONを抽出します。
        1. まず ```json ～ ``` のコードブロックがあれば、その内部のみを抽出。
        2. なければファイル全体をJSONとして解釈。
    - ノーブレークスペース（U+00A0）を通常のスペース（U+0020）に置換してからJSONを解析します。
    - `{"changes": [...]}` の配列を走査し、各変更を一覧表示してユーザーに最終確認後、順に適用します。
        - `operation: create` 新規作成（親ディレクトリが無ければ作成）。既存の場合はスキップ。
        - `operation: update` 上書き更新（ファイルが無ければ警告の上で新規作成）。
        - `operation: delete` 削除（存在しなければ警告）。

#### JSON差分形式（適用対象フォーマット）

以下の形式で出力されたJSONを適用します。`content` はファイル全文を文字列として格納してください（改行は `\n`）。

```json
{
  "changes": [
    {
      "file_path": "src/new_feature.py",
      "operation": "create",
      "content": "def new_function():\n    pass\n"
    },
    {
      "file_path": "main.py",
      "operation": "update",
      "content": "import src.new_feature\n\nsrc.new_feature.new_function()\n"
    },
    {
      "file_path": "docs/old_spec.txt",
      "operation": "delete"
    }
  ]
}
```

---

### クリーンアップ
一時ディレクトリを削除する

* **コマンド:** `promp clear`
* **引数/オプション:** なし
* **仕様:**
    - `.promp-in` と `.promp-out` ディレクトリを削除対象として検出し、対象が存在する場合のみ一覧表示して確認後に削除します。

---

## 使用技術
* **環境:** uvで構築
* **言語:** python

---

## 参考情報

### uvのインストール

**uv**は、以下のコマンドでインストールできます。

Windowsの場合PowerShellで以下コマンドを実行
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
````

Linuxの場合Bash等で以下コマンドを実行
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 開発時の一時インストール方法

※※注意：以下はpromp本体開発時の備忘録です。prompをツールとして使うだけなら関係ありません※※

promp本体を開発時にはvenv環境に入り、-eオプションをつけてインストールする必要がある

```sh
# 仮想環境を作成する（初回実行時）
uv venv

# 仮想環境の有効化（環境によって3通りある）
# Windows コマンドプロンプトの場合
.venv\Scripts\activate

# Windows powershellの場合
.venv\Scripts\Activate.ps1

# Linuxの場合
source .venv/bin/activate

# 仮想環境にインストール（編集可能オプション付き）
uv tool install -e .

# この後はprompツールを使えるようになる

# 仮想環境からぬける（仮想環境から抜けるとprompは使えなくなる）
deactivate
```
