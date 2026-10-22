# 西ヨーロッパ：行政区・道路・番地の補強（2026-10-22）

全行政区・全道路・全番地の完全網羅は未完了。配達可能性は対象外。従来版の11か国を維持し、M49西欧9か国と北欧に属するGB・IEを区別する。既存の2026-10-17版を残し、今回の原典を補強版として追加する。

## 今回の収録

| 国 | 公式住所レコード | 独立した道路名簿のレコード |
|---|---:|---:|
| オーストリア | 2,529,222 | 138,112 |
| ベルギー | 7,178,121 | 157,906 |
| スイス | 3,306,620 | 224,629 |
| フランス | 25,288,623 | BAN住所行に道路名あり。独立名簿は未取込 |
| リヒテンシュタイン | 12,966 | 1,237 |
| ルクセンブルク | 248,634 | 9,963 |

公式住所は合計 **38,564,186レコード**。フランスはコルシカを含む96県のファイルを全件読込・再照合。歴史・廃止・計画・暫定・公認外の記録を含み、現存する一意の配達先数ではない。ベルギーの box_number、スイスの番地なし・official=false も原典どおり保持。道路名簿の件数は実道路の本数ではなく、ベルギーでは郵便番号により同じ道路IDが複数回現れる場合がある。

補助としてモナコ周辺のOSM抽出も保持：道路way 3,625、番地タグ観測474、行政境界タグ観測61。これらはモナコ国内だけの総数ではない。元PBFとタグ・参照・点/way座標の投影を保持。版・時刻は元PBFに残し、軽量投影には復号しない。関係の面形状は未組立。

既存のGeoNames基盤は11か国・344,143行を再検証し、構造エラー0。これは最新の全行政区を保証しない。Eurostat/GeoNames/CACLR/BEV等を名前一致だけで同一の自治体に統合しない。LUの13件のcanton_referenceには特別・旧来のコードを含み、現在の法定カントン数としない。

## 残る不足

- DE・GB・IE・NL：今回の全国住所の追加取込は未完了。取得先・条件・次の作業は source-review.json / coverage.csv。
- 全11か国：独立した現行の全階層名簿、無名道・私道・無番地道路を含む全物理道路、付番機関の総台帳との比較が残る。
- CH・BE・FR等：他資料との行政・道路IDの全件結合は未検証。今回の参照検証はAT内部およびLU複合コードの参照が中心。
- 住所が原典にあること、公認・現存・使用許可・配達可能性は同義ではない。配達判定の処理は追加していない。

## 復元と利用

分割書庫は通常のZIP。すべて同じ新しいフォルダに展開すると `western-europe/raw/` に原典が揃う。コードは [rei-k/world-localities の西欧補強ブランチ](https://github.com/rei-k/world-localities/tree/codex/western-europe-evidence-20261022) の今回の変更を使用する。

```bash
python3 scripts/western_europe_sources.py inventory
python3 scripts/western_europe_sources.py search --data-root /path/to/western-europe/raw --country LI --kind address --number 9 --limit 5
python3 scripts/hierarchy_cli.py --region western-europe --data-root /path/to/western-europe/raw -- search --country LU --kind street --text Luxembourg --limit 5
python3 scripts/western_europe_sources.py replay --data-root /path/to/western-europe/raw --accepted releases/hierarchy/western-europe/validation.json
```

データが一部だけ必要な場合は `--country` で限定する。`search --current-only` は明示的な current/real の記録だけを返す。状態フラグを持たないATやBANまで現存認定して含めるものではない。番地は文字列で照合し、接尾辞やベルギーのboxは別フィールドに残す。

原典107ファイル（96県＋11台帳）をSHA-256で固定。読み込み結果を全行2回生成し、正規化行ハッシュと件数を照合。ZIP CRC / gzipトレーラーも検証。小さなPBF投影も全件再作成し同じハッシュを確認。標準ライブラリで利用でき、CIでは国範囲・破損・先頭ゼロ・言語・状態・座標系・海外領の混入等を検証する。

詳細は official-sources.json、validation.json、coverage.csv、NOTICE.md、archive.json を参照。全国完全性の分母が未確定のため、達成率は計算しない。
