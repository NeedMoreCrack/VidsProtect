# 🔐 VidProtect

> **Multilingual Video Protection Tool** | 影片加密保護工具 | 動画保護ツール

A Python-based video encryption tool that splits video files into AES-256-GCM encrypted shards. Decryption requires both the correct password **and** the correct shard order — providing dual-layer protection against unauthorized access.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Encryption Workflow](#encryption-workflow)
- [Decryption Workflow](#decryption-workflow)
- [Order String Format](#order-string-format)
- [Security Notes](#security-notes)
- [Important Notes](#important-notes)
- [Recommended Usage](#recommended-usage)
- [繁體中文說明](#繁體中文說明)
- [日本語ガイド](#日本語ガイド)

---

## Overview

**VidProtect** protects video content by:

- ✂️ Splitting video files into multiple encrypted shards
- 🔒 Encrypting each shard with **AES-256-GCM**
- 🔑 Requiring **both** the correct password **and** the correct shard order for decryption
- 📁 Automatically restoring the decrypted video into a target folder

**Use cases:**
- Protecting video content from unauthorized access
- Delivering encrypted video shards to authorized users only
- Reducing the risk of unauthorized video restoration

---

## Project Structure

```
VidProtect/
├── dist/
│   └── video_tool.exe       # Packaged executable for end users
├── encrypt_video.py         # Encrypts video files
├── decrypt_video.py         # Decrypts encrypted shards
├── video_tool.py            # Main entry point (encrypt / decrypt)
├── README.md
└── .gitignore
```

---

## Encryption Workflow

### Before Encryption

Place the videos you want to encrypt in the **same folder** as `video_tool.exe`:

```
📁 working folder/
├── video_tool.exe
├── movie1.mp4
└── movie2.mkv
```

### How to Run

1. Double-click `video_tool.exe`
2. Select **`1 = Encrypt`**
3. Enter an encryption password
4. Re-enter the password for confirmation
5. Enter the number of shards *(default: 10)*

### Encryption Result

The tool will automatically:

- Scan video files in the same folder as `video_tool.exe`
- Create an `Output/` folder if it does not exist
- Save encrypted shards into `Output/`
- Generate `author_order.txt` for the encryptor to keep safe

```
📁 Output/
├── Movie1/
│   ├── shard_xxx.enc
│   └── shard_yyy.enc
├── Movie2/
│   ├── shard_aaa.enc
│   └── shard_bbb.enc
└── author_order.txt       ← Keep this file secure!
```

---

## Decryption Workflow

### Before Decryption

Place the following files in the **same folder** as `video_tool.exe`:

```
📁 working folder/
├── video_tool.exe
├── shard_a.enc
├── shard_b.enc
└── shard_c.enc
```

### How to Run

1. Double-click `video_tool.exe`
2. Select **`2 = Decrypt`**
3. Paste the correct shard order string provided by the author
4. Enter the correct password
5. *(Optional)* Specify a custom output path — defaults to `DeVids/`

### Decryption Result

The tool will:

- Read **only** the shard files listed in the provided order string
- Ignore other `.enc` files in the same folder
- Verify password, shard order, and file integrity
- Restore the video into the `DeVids/` folder on success

```
📁 DeVids/
└── recovered_movie1.mp4
```

---

## Order String Format

The shard order string uses comma-separated filenames:

```
shard_a.enc,shard_b.enc,shard_c.enc,shard_d.enc
```

> ⚠️ **Important:**
> - Filenames must be separated by **commas** (no spaces)
> - The order must be **exactly correct**
> - Missing, extra, or incorrectly ordered shard names **will cause decryption to fail**

---

## Security Notes

| Component | Detail |
|-----------|--------|
| Encryption | AES-256-GCM |
| Key Derivation | scrypt |

**Decryption will fail if any of the following occur:**

- ❌ The password is incorrect
- ❌ The shard order is incorrect
- ❌ A shard file is missing
- ❌ A shard file was modified or corrupted
- ❌ Shards from different videos are mixed together

---

## Important Notes

> 💾 **Keep the password and shard order secure at all times.**

- If the password is lost, the video **usually cannot be restored**
- If one or more shards are missing, **full decryption is impossible**
- Do **not** rename or modify shard files
- It is recommended to remove unrelated `.enc` files before decryption to avoid confusion

---

## Recommended Usage

### For Encryptors

- ✅ Keep `author_order.txt` secure
- ✅ Only provide shard files and order information to **authorized users**
- ❌ Do **not** expose the password or correct shard order publicly

### For Users

- ✅ Put all shard files and `video_tool.exe` in the **same folder**
- ✅ Make sure the password and order string are **exactly correct**
- ✅ After decryption, check the restored video in the `DeVids/` folder

---

---

## 繁體中文說明

### 1. 工具簡介

VidProtect 是一個以 Python 製作的影片保護工具，提供以下功能：

- 將影片檔案切割成多個加密分片
- 每個分片使用 **AES-256-GCM** 加密
- 解密時必須同時提供：
  - 正確的密碼
  - 正確的分片順序
- 可將解密後的影片自動輸出到指定資料夾

**本工具適合用於：**
- 保護影片內容
- 將影片分片後再交付給使用者
- 降低未授權使用者直接還原影片的可能性

---

### 2. 工具結構

```
VidProtect/
├── dist/
│   └── video_tool.exe       # 打包後供一般使用者直接執行的版本
├── encrypt_video.py         # 負責加密影片
├── decrypt_video.py         # 負責解密影片
├── video_tool.py            # 主入口工具，可選擇加密或解密
├── README.md
└── .gitignore
```

---

### 3. 加密流程

#### 加密前準備

請將要加密的影片放在 `video_tool.exe` **同一層目錄**：

```
📁 工作資料夾/
├── video_tool.exe
├── movie1.mp4
└── movie2.mkv
```

#### 執行方式

1. 雙擊 `video_tool.exe`
2. 選擇 **`1 = Encrypt`**
3. 輸入加密密碼
4. 再次輸入密碼確認
5. 輸入分片數量（預設為 10）

#### 加密結果

程式會：
- 自動掃描與 `video_tool.exe` 同層的影片檔案
- 建立 `Output/` 資料夾（若不存在）
- 將每部影片加密後輸出到 `Output/` 內
- 產生 `author_order.txt` 供加密者保存

```
📁 Output/
├── Movie1/
│   ├── shard_xxx.enc
│   └── shard_yyy.enc
├── Movie2/
│   ├── shard_aaa.enc
│   └── shard_bbb.enc
└── author_order.txt       ← 請妥善保存此檔案！
```

---

### 4. 解密流程

#### 解密前準備

請將下列檔案放在 `video_tool.exe` **同一層目錄**：

```
📁 工作資料夾/
├── video_tool.exe
├── shard_a.enc
├── shard_b.enc
└── shard_c.enc
```

#### 執行方式

1. 雙擊 `video_tool.exe`
2. 選擇 **`2 = Decrypt`**
3. 貼上作者提供的正確分片順序字串
4. 輸入正確密碼
5. 若不指定輸出路徑，程式會自動輸出到 `DeVids/` 資料夾

#### 解密結果

程式會：
- 只根據你輸入的順序字串讀取對應的 shard 檔案
- 忽略同層其他未列在順序中的 `.enc` 檔案
- 驗證密碼、分片順序、檔案完整性
- 成功後將影片輸出到 `DeVids/` 資料夾

```
📁 DeVids/
└── recovered_movie1.mp4
```

---

### 5. 順序字串格式

```
shard_a.enc,shard_b.enc,shard_c.enc,shard_d.enc
```

> ⚠️ **注意：**
> - 檔名之間以**逗號**分隔（不含空格）
> - 順序必須**完全正確**
> - 少一個、多一個、順序錯誤，都可能導致解密失敗

---

### 6. 安全性說明

| 元件 | 說明 |
|------|------|
| 加密算法 | AES-256-GCM |
| 金鑰派生 | scrypt |

**發生以下情況，解密會失敗：**

- ❌ 密碼錯誤
- ❌ 分片順序錯誤
- ❌ 分片檔案缺少
- ❌ 分片內容遭修改
- ❌ 提供了不屬於同一影片的分片

---

### 7. 注意事項

> 💾 **請妥善保存密碼與正確順序。**

- 若密碼遺失，影片通常**無法還原**
- 若分片缺失，影片**無法完整解密**
- 請勿任意**修改 shard 檔案名稱或內容**
- 建議解密時將**無關的 `.enc` 檔案移開**，以免混淆

---

### 8. 建議使用方式

#### 對加密者

- ✅ 保存 `author_order.txt`
- ✅ 只將需要的 shard 檔案與順序資訊提供給**授權使用者**
- ❌ 不要將密碼與分片順序**公開給未授權對象**

#### 對使用者

- ✅ 將所有 shard 檔案與 `video_tool.exe` 放在**同一層**
- ✅ 確認密碼與順序字串**正確**
- ✅ 解密完成後到 `DeVids/` 內查看還原影片

---

---

## 日本語ガイド

### 1. 概要

VidProtect は Python ベースの動画保護ツールです。主な機能は以下の通りです：

- 動画ファイルを複数の暗号化シャードに分割
- 各シャードを **AES-256-GCM** で暗号化
- 復号には以下の**両方**が必要：
  - 正しいパスワード
  - 正しいシャード順序
- 復号後の動画を指定フォルダへ自動出力

**このツールは以下の用途に適しています：**
- 動画コンテンツの保護
- 正規ユーザーへの暗号化済みシャード配布
- 無許可での動画復元を困難にすること

---

### 2. 構成ファイル

```
VidProtect/
├── dist/
│   └── video_tool.exe       # 一般ユーザー向け実行ファイル
├── encrypt_video.py         # 動画暗号化
├── decrypt_video.py         # 動画復号
├── video_tool.py            # 暗号化・復号のメイン入口
├── README.md
└── .gitignore
```

---

### 3. 暗号化の流れ

#### 暗号化前の準備

暗号化したい動画を `video_tool.exe` と**同じフォルダ**に置いてください：

```
📁 作業フォルダ/
├── video_tool.exe
├── movie1.mp4
└── movie2.mkv
```

#### 実行方法

1. `video_tool.exe` をダブルクリック
2. **`1 = Encrypt`** を選択
3. 暗号化パスワードを入力
4. 確認のため再入力
5. シャード数を入力（デフォルト：10）

#### 暗号化結果

ツールは以下を行います：
- `video_tool.exe` と同じフォルダ内の動画を自動検出
- `Output/` フォルダがなければ自動作成
- 暗号化シャードを `Output/` に保存
- 暗号化者用に `author_order.txt` を生成

```
📁 Output/
├── Movie1/
│   ├── shard_xxx.enc
│   └── shard_yyy.enc
├── Movie2/
│   ├── shard_aaa.enc
│   └── shard_bbb.enc
└── author_order.txt       ← このファイルは安全に保管してください！
```

---

### 4. 復号の流れ

#### 復号前の準備

以下を `video_tool.exe` と**同じフォルダ**に置いてください：

```
📁 作業フォルダ/
├── video_tool.exe
├── shard_a.enc
├── shard_b.enc
└── shard_c.enc
```

#### 実行方法

1. `video_tool.exe` をダブルクリック
2. **`2 = Decrypt`** を選択
3. 作成者から受け取った正しい順序文字列を貼り付け
4. 正しいパスワードを入力
5. 出力先を指定しない場合、復元動画は `DeVids/` フォルダに保存されます

#### 復号結果

ツールは以下を行います：
- 入力された順序文字列に含まれる shard のみを読み込む
- 同じフォルダ内の他の `.enc` ファイルは無視する
- パスワード・順序・ファイル整合性を検証する
- 成功時は `DeVids/` フォルダへ動画を復元する

```
📁 DeVids/
└── recovered_movie1.mp4
```

---

### 5. 順序文字列の形式

```
shard_a.enc,shard_b.enc,shard_c.enc,shard_d.enc
```

> ⚠️ **注意点：**
> - ファイル名は**カンマ**で区切ってください（スペースなし）
> - 順序は**完全に正しく**なければなりません
> - 欠落・余分・順序違いがあると復号に失敗する可能性があります

---

### 6. セキュリティについて

| コンポーネント | 詳細 |
|----------------|------|
| 暗号化方式 | AES-256-GCM |
| 鍵導出 | scrypt |

**次の場合、復号は失敗します：**

- ❌ パスワードが間違っている
- ❌ シャード順序が間違っている
- ❌ シャードが不足している
- ❌ シャード内容が改変されている
- ❌ 同じ動画に属さない shard を混在させている

---

### 7. 注意事項

> 💾 **パスワードと正しい順序は安全に保管してください。**

- パスワードを紛失すると、通常は動画を**復元できません**
- シャードが不足している場合、**完全復号はできません**
- shard ファイル名や内容を**変更しないでください**
- 復号時は混乱を避けるため、**不要な `.enc` ファイルを別の場所へ移す**ことを推奨します

---

### 8. 推奨される使い方

#### 暗号化する側

- ✅ `author_order.txt` を安全に保管する
- ✅ shard ファイルと順序情報は**認可された相手のみ**に渡す
- ❌ パスワードや正しい順序を**公開しない**

#### 利用者側

- ✅ すべての shard ファイルと `video_tool.exe` を**同じフォルダ**に置く
- ✅ パスワードと順序文字列が**正しいことを確認**する
- ✅ 復号後は `DeVids/` フォルダ内の復元動画を確認する

---

*VidProtect — Protect your video content with layered encryption.*
