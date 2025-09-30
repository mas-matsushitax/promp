# ツール名: promp (読み方: プロンプ)

## このツールは何？ (目的)
* LLMのWeb AIをコーディングエージェントとして使うための便利機能を提供する

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
    * `-s, --spec`: (任意) コマンドの仕様を記述するための`SPEC.md`ファイルを出力します。
* **実行例:**
    ```sh
    # 基本的なファイルのみ作成
    promp init

    # 仕様書ファイルも一緒に作成
    promp init --spec
    ```
* **仕様:**

    カレントフォルダに以下のフォルダ／ファイルを配置します。
    
    (D)-> フォルダ (F)-> ファイル
    ```
    .promp-template(D)
    L default.txt(F)
    L spec.txt(F)
    .gitignore(F)
    SPEC.md(F)      <-- --spec オプション指定時のみ
    ```

    .gitignoreの中身は以下。既存の.gitignoreがあれば、以下の行を加える
    ```
    # for promp
    .promp-out
    .promp-in
    ```

    `--spec` オプションが指定された場合、`.promp-template/spec.txt` と同じ内容で `SPEC.md` が作成されます。

    すでにカレントフォルダに一つ以上のファイルやフォルダが存在する場合は、どのような作用があるか説明して、ユーザーから許可を取るようにします。

---

### 出力
プロンプトを出力する

* **コマンド:** `promp out "既存ファイルパス"`
* **引数 (Arguments):**
    * `"既存ファイルパス"`: プロンプトに加えたいファイルパス。複数可、ワイルドカード可。
* **オプション (Options):**
    * `-t, --template <テンプレート名>`: (任意) プロンプト作成時のテンプレートを指定する
* **実行例:**
    ```sh
    # カレントフォルダ配下のすべての.pyファイルをプロンプトに加える
    promp out ./**/*.py
    ```
* **仕様:**
    
    .promp-template/default.txtを読み取って、.promp-out/out-XXXXXXXX.txtに出力する。
    同時に、LLMからの出力を貼り付けるための空ファイルとして .promp-in/in-XXXXXXXX.txt を作成する。
    
    XXXXXXXXは現在日時をyyyymmdd-hhmmss形式にする（例：out-20250927-190721.txt）
    
    出力時に、引数で指定されたファイルを読み取って{existing_files}に埋め込む
     
      埋め込み時はファイル毎に以下のようにヘッダーをつけること
        ---- ファイルパス（カレントからの相対パス）----
        ファイルの内容
    
    オプションでテンプレート名が指定された場合は、.promp-template/<テンプレート名>.txtをテンプレートとする


### 適用
LLMから出力された「ブロック置換形式」のファイルをカレントフォルダに適用する

* **コマンド:** `promp apply ["LLMからの出力ファイルパス"]`
* **引数 (Arguments):**
    * `["LLMからの出力ファイルパス"]`: (任意) LLMが出力したファイル。省略した場合、`.promp-in/` ディレクトリ内のタイムスタンプが最も新しいファイルが自動的に選択されます。
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
    
    引数で指定されたファイルを読み取り、「ブロック置換形式」として解釈して、ファイルを上書きする。
    引数が省略された場合は、`.promp-in/` 内の最新のファイルが対象となります。

    ブロック置換形式は、ファイル全体をそのまま置き換えるためのシンプルな形式。
    
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
