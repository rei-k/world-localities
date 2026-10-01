# World Localities

世界の自治体・行政区画・地名を、公的コード・親子関係・出典付きで管理するリポジトリです。

## 収録済みデータ

| 地域 | 行政区画・地名 | 別出典の公式対応表 | 取得日 |
|---|---:|---:|---|
| [ヨーロッパ](europe-registry/README.md) | 57か国・地域、1,161,589件 | Eurostat LAU: 32か国、104,687行 | 2026-09-29 |
| [オセアニア](oceania-registry/README.md) | 29か国・地域、46,594件 | AU ABS公式コード567件。GeoNames直接ID郵便対応262行は別レイヤー | 2026-09-26～29 |
| [アジア＋ロシア全域補足](asia-registry/README.md) | 52国・地域、3,277,921件 | [JP・TWの公式名称・郵便対応](official-registry/README.md)を追加。全面対応は未完了 | 国別メタデータ参照 |

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

オセアニアは国別62分割パックに、言語付き名称37,236件と限定的な郵便番号対応を収録しました。地域IDを保持した名称選択と国別展開に対応します。全公用語・郵便番号の完全網羅ではありません。原典と検証結果は [オセアニア台帳](oceania-registry/README.md) を参照してください。
