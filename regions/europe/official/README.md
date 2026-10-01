# Eurostat公式LAU対応表

[eurostat-lau/](eurostat-lau/) に32か国・104,687行を収録しています。配布版はLAU 2025 / NUTS 2024、データ行のPERIODは2024です。
GeoNames基礎地名は [../gazetteer/](../gazetteer/README.md) に別置きしています。自動統合・同名による対応付けはしません。

- [国別マニフェスト](eurostat-lau/manifest.json)
- [出典](eurostat-lau/source.json)
- [検証記録](eurostat-lau/verification.json)
- [定義](../gazetteer/SCHEMA.md) / [利用条件と帰属表示](../gazetteer/NOTICE.md)

リポジトリのルートから検証します。

```bash
python regions/europe/official/eurostat.py verify
```

原典Excelからの再構築には追加の依存パッケージが必要です。

```bash
pip install -r regions/europe/official/requirements-build.txt
python regions/europe/official/eurostat.py build --inputs /path/to/source-cache
```

セルビアの原典コア項目は未検証、リヒテンシュタインの空シートは収録件数に含めません。
統計上のNUTS親参照を行政上の親と混同しません。現在の法的自治体台帳や公式英訳の全面認定ではありません。
