# リポジトリ構成

このリポジトリは、データを地域別に保ちながら、地域に依存しない処理だけを
`localities/` に集約します。既存の利用者が参照している地域別パスは安定した公開入口です。

## ディレクトリの責務

| パス | 責務 |
|---|---|
| `localities/` | GeoNames変換、分割ファイル復元、構成検証などの共有コード |
| `*-registry/` | 地域・出典固有のデータ、規則、メタデータ、CLI、互換入口 |
| `official-registry/` | 国別の公式コード・公式名称・郵便対応を扱う追加レイヤー |
| `americas-registry/` | アメリカ4地域を横断する監査・品質サイクル |
| `tests/` | 複数地域またはリポジトリ全体にまたがる回帰テスト |
| `scripts/` | リリース検証などの運用コマンド |
| `docs/` | 横断設計、品質方針、更新計画 |

地域別ディレクトリの一覧と共有コードの利用関係は
[`localities/registry_catalog.json`](../localities/registry_catalog.json)を正とします。
次のコマンドで、登録済みディレクトリ、README、共有モジュール、互換入口の存在を検証できます。

```bash
python -m localities.layout
```

## 互換性方針

- 地域別の `query.py`、`build.py`、`materialize.py` など既存の入口は維持します。
- 共通化したファイルは薄い互換入口にし、地域ディレクトリから直接実行しても動作させます。
- データファイルの移動は、既存のマニフェスト、チェックサム、利用者の相対パスを壊すため、
  コード整理と同じ変更では実施しません。
- 出典固有の意味や品質判定は、見た目が似ていても無理に共通化しません。

## 共有化の基準

共有コードへ移すのは、複数地域で同じ入出力契約と安全条件を持つ処理です。
現在は次の2種類を共有しています。

1. `localities.geonames`: GeoNamesのA/P行を、出典IDと親候補を保持した共通行へ変換する処理
2. `localities.materialize`: 分割済み大容量ファイルを、サイズとSHA-256を検証して原子的に復元する処理

国別公式データの照合、郵便番号の意味、言語選択、公開範囲は地域・出典ごとの差が大きいため、
各レジストリに残します。

## 変更時の確認

共有コードを変更した場合は、最低限、構成テストと3地域の回帰テストを実行します。

```bash
python -m unittest discover -s tests -p 'test_repository_layout.py' -v
python caribbean-registry/test_materialize.py -v
python central-america-registry/test_materialize.py -v
python south-america-registry/test_materialize.py -v
python caribbean-registry/test_caribbean.py -v
python central-america-registry/test_registry.py -v
python south-america-registry/test_registry.py -v
```
