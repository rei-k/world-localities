# World Localities

世界の自治体・行政区画・地名を、公的コード・親子関係・出典付きで管理するリポジトリです。

## 収録済みデータ

| 地域 | 行政区画・地名 | 別出典の公式対応表 | 取得日 |
|---|---:|---:|---|
| [ヨーロッパ](europe-registry/README.md) | 57か国・地域、1,161,589件 | Eurostat LAU: 32か国、104,687行 | 2026-09-29 |

GeoNamesとEurostatは重複する対象を含むため、件数を合算しません。
企業名簿・法人情報は収録対象に含めません。

国別の分割CSV、原典コード、確認できた親子関係、出典・ライセンス、検証結果を収録しています。
未確定の親子関係は明示しています。この版には郵便番号の対応・Address1・境界ポリゴン、
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

## 由来

欧州データは、[rei-k/world-address PR #406](https://github.com/rei-k/world-address/pull/406)の
コミット`9071ff08548bbc6b449e6c30e8eae2adad025d46`から収録しました。
取得済みデータの内容と検証結果を保ち、配置場所に関する案内だけを更新しています。
