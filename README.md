# World Localities

世界の自治体・行政区画・地名を、公的コード・親子関係・出典付きで管理するリポジトリです。

## 収録済みデータ

| 地域 | 行政区画・地名 | 別出典の公式対応表 | 取得日 |
|---|---:|---:|---|
| [ヨーロッパ](europe-registry/README.md) | 57か国・地域、1,161,589件 | Eurostat LAU: 32か国、104,687行 | 2026-09-29 |
| [アジア＋ロシア全域補足](asia-registry/README.md) | 52国・地域、3,277,921件 | 公式対訳・郵便番号の全面対応は未収録 | 国別メタデータ参照 |

地域台帳間にも同じ `gn:` IDの重複があります。アジアと欧州、GeoNamesとEurostatの件数を単純に合算しません。
企業名簿・法人情報は収録対象に含めません。

国別の分割CSV、原典コード、確認できた親子関係、出典・ライセンス、検証結果を収録しています。
未確定の親子関係は明示しています。基礎台帳には郵便番号の対応・Address1・境界ポリゴン、
全公用語の翻訳は含まれません。

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

## 地図連携の学習実験

[欧州地図学習](europe-map-learning/README.md)では、AT・DE・CHの4,899地点を
実際の51行政区画の境界に照合し、小型判定モデルを強化学習しました。
学習済み重み・評価結果・地点を選べる地図・再現コードを収録しています。
境界は2017〜2022年のスナップショットです。LLMの追加学習ではなく、
地図と台帳の一致・矛盾・保留を判定する限定的な実験です。

## 由来

欧州データは、[rei-k/world-address PR #406](https://github.com/rei-k/world-address/pull/406)の
コミット`9071ff08548bbc6b449e6c30e8eae2adad025d46`から収録しました。
取得済みデータの内容と検証結果を保ち、配置場所に関する案内だけを更新しています。

アジアは [world-address の保存済みスナップショット](https://github.com/rei-k/world-address/tree/8e30ef141e40769fa932adeb2f901505023bfd1e/address-foundation/asia-registry) を収録しています。
移行の照合結果は [migration.json](asia-registry/migration.json)、公式情報の拡充順序は
[追加設計](docs/enrichment-plan-ja.md) を参照してください。

次のコマンドはリポジトリのルートから実行します。

```bash
python asia-registry/package.py unpack --country JP
python asia-registry/build.py verify --country JP
python -m unittest discover -s tests -p 'test_asia_package.py' -v
```
