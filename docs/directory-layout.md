# ディレクトリ移行ガイド

ルート直下に並んでいた地域台帳を `regions/` に集約しました。国別のデータ形式・ID・圧縮方式・内部相対パスは変更していません。
旧ルートへの互換コピーやsymlinkは作りません。コマンド・スクリプトのパスを以下へ変更してください。

| 旧パス | 新パス |
|---|---|
| africa-registry/ | regions/africa/gazetteer/ |
| asia-registry/ | regions/asia/gazetteer/ |
| europe-registry/ | regions/europe/gazetteer/ |
| europe-registry/eurostat-lau/ | regions/europe/official/eurostat-lau/ |
| europe-registry/eurostat.py | regions/europe/official/eurostat.py |
| europe-registry/requirements-build.txt | regions/europe/official/requirements-build.txt |
| oceania-registry/ | regions/oceania/gazetteer/ |
| central-america-registry/ | regions/americas/central/gazetteer/ |
| caribbean-registry/ | regions/americas/caribbean/gazetteer/ |
| south-america-registry/ | regions/americas/southern/gazetteer/ |
| official-registry/US/・CA/ | regions/americas/northern/official/US/・CA/ |
| official-registry/MX/ | regions/americas/central/official/MX/ |
| official-registry/BR/ | regions/americas/southern/official/BR/ |
| official-registry/americas-provenance/ | regions/americas/official/provenance/ |
| official-registry/americas-snapshot-schema.json | regions/americas/official/schema.json |
| official-registry/AMERICAS_SNAPSHOTS.md | regions/americas/official/README.md |
| official-registry/ のJP・TW・残る共通ファイル | regions/asia/official/ |

機械可読の先頭一致ルールは [directory-migration.json](directory-migration.json)、現在の入口は [../catalog.json](../catalog.json) です。
米州の地理フォルダ名はNorthern America / Central America / Caribbean / South Americaに対応します。Mexicoはcentralです。

## データを変えないための境界

- 原典・CSV・gzip・ZIP・分割片・Base64パック・ライセンス本文のGit blobをそのまま再利用します
- 米州公式source-mapのdestination_pathのみ新配置へ更新し、source_path・原典URL・Git/SHA-256ハッシュは変えません
- 以前のmigration.jsonやupstream/の記録は当時の移行履歴です。そこに残る旧destinationパスは本ガイドで読み替えます
- パックや分割マニフェストはパッケージ内部の相対パスを維持し、再圧縮しません
- USのPuerto Rico行は原典パッケージ内に維持し、カリブのPR GeoNamesと統合しません
- オセアニア内のAU公式資料も、元の国別パック内部の独立レイヤーとして維持します
- 未収録の国を、この移動によって収録済みにしません

## 実行位置

ルートからは `python regions/…/query.py` の形で実行します。各パッケージへ `cd` して既存の `python query.py` を実行する方法も使えます。
GeoNamesや公式postalのPython関数の引数・返却スキーマは維持します。Eurostatスクリプトのデフォルトrootは移動先の `regions/europe/official/` です。
`from build import …` などの短いモジュール名は各パッケージ内で使い、別地域を同一Pythonプロセスで読み込む場合は明示した別モジュール名を使ってください。

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s regions/europe/gazetteer -p 'test_europe.py' -v
python -m unittest discover -s regions/africa/gazetteer -p 'test_africa.py' -v
python -m unittest discover -s regions/oceania/gazetteer/tests -p 'test_region_names.py' -v
python -m unittest discover -s regions/americas/central/gazetteer -p 'test_*.py' -v
python -m unittest discover -s regions/americas/caribbean/gazetteer -p 'test_*.py' -v
python -m unittest discover -s regions/americas/southern/gazetteer -p 'test_*.py' -v
```

各コマンドは別プロセスで実行します。国別のquery・verify例と必要な展開手順は各READMEを参照してください。
