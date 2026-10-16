# World Localities

世界の自治体・行政区画・地名を、公的コード・親子関係・出典付きで管理するリポジトリです。

## 収録済みデータ

| 地域 | 行政区画・地名 | 別出典の公式対応表 | 取得日 |
|---|---:|---:|---|
| [ヨーロッパ](europe-registry/README.md) | 57か国・地域、1,161,589件 | Eurostat LAU: 32か国、104,687行 | 2026-09-29 |
| [オセアニア](oceania-registry/README.md) | 29か国・地域、46,594件 | AU ABS公式コード567件。GeoNames直接ID郵便対応262行は別レイヤー | 2026-09-26～29 |
| [アジア＋ロシア全域補足](asia-registry/README.md) | 52国・地域、3,277,921件 | [JP・TWの公式名称・郵便対応](official-registry/README.md)を追加。全面対応は未完了 | 国別メタデータ参照 |
| [南米](south-america-registry/README.md) | M49の16/16国・地域、272,379件 | GeoNames出典付き台帳。公式自治体完全性・郵便配達可能性は未検証。BRのIBGE公式台帳とは別レイヤー | 2026-10-01・03 |

地域台帳間にも同じ `gn:` IDの重複があります。アジアと欧州、GeoNamesとEurostatの件数を単純に合算しません。
企業名簿・法人情報は収録対象に含めません。

国別の分割CSV、原典コード、確認できた親子関係、出典・ライセンス、検証結果を収録しています。
未確定の親子関係は明示しています。公式の名称・郵便番号対応は国別の追加レイヤーに収録します。
Address1・境界ポリゴン、全公用語の翻訳は含まれません。

日本は公式コードで1,892市区町村・区と郵便番号124,526行を接続しました。
日本語・カナ・原典ローマ字を区別し、295,029項目のローマ字を共通アルゴリズムで省略保存しています。
台湾は郵便当局の中英対照371組と3桁郵便区域コードを接続しました。完全6桁番号は未収録です。
詳細と未対応範囲は [公式対応レイヤー](official-registry/README.md) を参照してください。

## 利用

Python 3.11以降の標準ライブラリで地名の読み込み・検索・構造検証ができます。

```bash
cd europe-registry
python query.py --country AT --level 1
python query.py --country PL --text Krak --limit 10
python build.py verify
```

詳細は[欧州データのREADME](europe-registry/README.md)、
[スキーマ](europe-registry/SCHEMA.md)、[利用条件](europe-registry/NOTICE.md)を参照してください。

## 由来

欧州データは、[rei-k/world-address PR #406](https://github.com/rei-k/world-address/pull/406)の
コミット`9071ff08548bbc6b449e6c30e8eae2adad025d46`から収録しました。
取得済みデータの内容と検証結果を保ち、配置場所に関する案内だけを更新しています。

アジアは [world-address の保存済みスナップショット](https://github.com/rei-k/world-address/tree/8e30ef141e40769fa932adeb2f901505023bfd1e/address-foundation/asia-registry) を収録しています。
移行の照合結果は [migration.json](asia-registry/migration.json)、公式情報の拡充順序は
[追加設計](docs/enrichment-plan-ja.md) を参照してください。

学習対象・強化学習の報酬と評価方法は [アジア学習計画](docs/asia-learning-plan-ja.md) に収録しました。
モデルの学習や精度改善の実証は未実行です。

次のコマンドはリポジトリのルートから実行します。

```bash
python asia-registry/package.py unpack --country JP
python asia-registry/build.py verify --country JP
python -m unittest discover -s tests -p 'test_asia_package.py' -v
```

## コードとデータの構成

地域別データと出典固有の処理は従来どおり各 `*-registry/` に置き、複数地域で
同じ契約を持つGeoNames変換と分割ファイル復元だけを `localities/` に共通化しています。
地域固有の `build.py` と `query.py` は維持し、重複していた内部ラッパーは廃止しました。

構成の正本は [`localities/registry_catalog.json`](localities/registry_catalog.json)、
責務と変更方針は[リポジトリ構成](docs/repository-layout.md)を参照してください。
構成・同名コード検証は `python -m localities layout` で実行できます。

## 世界住所フォーム互換レイヤー

[`addressing/`](addressing/README.md) は、251の国・地域プロファイルと46の言語別変種を
固定出典・ハッシュ付きで収録し、入力フィールドの順番に依存しない共通住所要素から
国内向け・国際向け表示を生成します。これは表示互換レイヤーであり、街路・番地・建物の
実在や郵便配達可能性を証明するものではありません。検証結果は形式、地名、郵便、街路、
建物、Address2、配達可能性を別レベルで返す契約にしています。

東アジア8国・地域は母国語10変種と英語を明示的に分離し、言語付き住所要素から二言語を
同時生成できます。英語値の欠落や非ラテン文字混入を厳格モードで拒否し、機械翻字を
公式英語名として扱いません。北朝鮮の形式は未検証状態を保持して出力します。

東南アジア11か国は母国語14変種と英語を分離しました。シンガポールはマレー語・
簡体字中国語・タミル語、東ティモールはテトゥン語・ポルトガル語を個別に選択できます。
Address2と棟・入口・階・部屋を配送行へ保持し、母国語がラテン文字でも英語値へ自動流用しません。
公開資料が限定的なミャンマーと東ティモールは `provisional` のまま出力します。

```bash
python -m addressing verify
python -m addressing southeast-asia
python -m addressing profile --country JP --language ja
```

オセアニアは国別62分割パックに、言語付き名称37,236件と限定的な郵便番号対応を収録しました。地域IDを保持した名称選択と国別展開に対応します。全公用語・郵便番号の完全網羅ではありません。原典と検証結果は [オセアニア台帳](oceania-registry/README.md) を参照してください。

## アメリカ大陸（北部アメリカから順次強化）

[アメリカ大陸の統合品質監査](americas-registry/README.md)は、国連M49の4地域を
**北部アメリカ → 中央アメリカ → カリブ海 → 南アメリカ**の順に扱い、
既存の国別データを再コピーせず参照します。

[北部アメリカ](north-america-registry/README.md)は米国・カナダの公式データ
（米国68,744行、カナダ5,054行）を読み込み、プエルトリコのM49境界を
別扱いにします。カナダNova Scotia州名の出典付き表示補正と、
BM/GL/PMの**18件の行政区画名シード**も追加しました。
シードは完全な地名台帳や住所・郵便番号の検証結果ではありません。

検証: `python americas-registry/audit.py --mode audit`
 / `python americas-registry/audit.py --mode plan`
 / `python americas-registry/audit.py --mode cycle --rounds 3`

アメリカ大陸の地域別の**出典付き国・地域レイヤーは53/57**です。
この数値は全住所・自治体・全公用語の網羅を意味しません。

## 中央アメリカの追加強化（2026-10-15）

[中央アメリカ強化記録](central-america-registry/ENRICHMENT_20261015.md)に、
コスタリカ6,465地名・行政地物と6,182言語付き名称の追加、政府公開84カントンコード表、
8か国共通検索、全ペイロード検査を整理した。国別出典レイヤーは中央アメリカ8/8、
アメリカ大陸53/57。住所・郵便番号・全自治体の完全網羅ではない。

新しい入口は `python central-america-registry/query_enriched.py --country CR --text 'San Jose' --language es`、
実データ検査は `python central-america-registry/quality.py`。
