# ツール名: promp (読み方: プロンプ)

## このツールは何？ (目的)
* LLMのWeb AIをコーディングエージェントとして使うための便利機能を提供する

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
    # カレントフォルダでprompを使えるようにする
    promp init
    ```
* **仕様:**

    カレントフォルダに以下のフォルダ／ファイルを配置する
    
    (D)-> フォルダ (F)-> ファイル
    ```
    .promp-template(D)
    L default.txt(F)
    L spec.txt(F)
    .gitignore(F)
    PROMP-SPEC.md(F)
    ```

    .gitignoreの中身は以下。既存の.gitignoreがあれば、以下の行を加える
    ```
    # for promp
    .promp-out
    ```

    default.txtとspec.txtの内容は「ファイルの内容」
    
    PROMP-SPEC.mdの中身は.promp-template/spec.txtと同じ

    すでにカレントフォルダに一つ以上のファイルやフォルダが存在する場合は、どのような作用があるか説明して、ユーザーから許可を取るようにする

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
    
    .promp-template/default.txtを読み取って、.promp-out/out-XXXXXXXX.txtに出力
    
    XXXXXXXXは現在日時をyyyymmdd-hhmmss形式にする（例：out-20250927-190721.txt）
    
    出力時に、引数で指定されたファイルを読み取って{existing_files}に埋め込む
      
      埋め込み時はファイル毎に以下のようにヘッダーをつけること
        ---- ファイルパス（カレントからの相対パス）----
        ファイルの内容
    
    オプションでテンプレート名が指定された場合は、.promp-template/<テンプレート名>.txtをテンプレートとする


### 適用
LLMから出力された「ブロック置換形式」のファイルをカレントフォルダに適用する

* **コマンド:** `promp apply "LLMからの出力ファイルパス"`
* **引数 (Arguments):**
    * `"LLMからの出力ファイルパス"`: LLMが出力したファイル。
* **オプション (Options):**
    なし
* **実行例:**
    ```sh
    # LLMの出力を保存した `llm-output.txt` を適用する
    promp apply llm-output.txt
    ```
* **仕様:**
    
    引数で指定されたファイルを読み取り、「ブロック置換形式」として解釈して、ファイルを上書きする。

    ブロック置換形式は、ファイル全体をそのまま置き換えるためのシンプルな形式。
    
---

## 使用技術
* **環境:** uvで構築
* **言語:** python

---
