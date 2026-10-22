# ドイツ：行政区・道路・番地の原典取込（2026-10-22）

全国完全網羅は未完了。配達可能性は対象外。16州すべてのGV100行政参照を取得し、12州の住所 **14,248,259原典観測行**、BE/BB・THの独立道路名簿 **89,709行**、全国DLM250道路軸 **358,992行**を取り込んだ。原典バイト列、全解析行、自治体コード参照を2回照合した結果は [validation.json](validation.json)。

## 16州の台帳

| 州 | 名称 | GV自治体 | 住所観測行 | 取得区分 | GVとコード一致の住所あり自治体 |
|---|---|---:|---:|---|---:|
| SH | Schleswig-Holstein | 1,104 | 953,360 | 公式形式の第三者ミラー | 1104 |
| HH | Hamburg | 1 | 284,575 | 公式過去版 | 1 |
| NI | Niedersachsen | 939 | 2,562,473 | 第三者派生表 | 照合不能 |
| HB | Bremen | 2 | 176,374 | 公式直接 | 2 |
| NW | Nordrhein-Westfalen | 396 | 4,509,543 | 公式直接 | 396 |
| HE | Hessen | 421 | 1,630,801 | 公式直接 | 421 |
| RP | Rheinland-Pfalz | 2,300 | 1,406,086 | 公式直接 | 2300 |
| BW | Baden-Württemberg | 1,101 | 0 | 未取得 | 未取得 |
| BY | Bayern | 2,056 | 0 | 未取得 | 未取得 |
| SL | Saarland | 52 | 335,623 | 第三者派生表 | 52 |
| BE | Berlin | 1 | 394,933 | 公式直接 | 1 |
| BB | Brandenburg | 413 | 867,290 | 公式形式の第三者ミラー | 413 |
| MV | Mecklenburg-Vorpommern | 724 | 516,150 | 第三者派生表 | 照合不能 |
| SN | Sachsen | 418 | 0 | 未取得 | 未取得 |
| ST | Sachsen-Anhalt | 218 | 0 | 未取得 | 未取得 |
| TH | Thüringen | 601 | 611,051 | 公式直接 | 575 |

公式直接 8,728,788行、公式過去版HH 284,575行、ミラー 1,820,650行、派生表 3,414,246行を分ける。住所観測は現存する一意の住所数ではない。州間で基準日が異なり、行政改編前のコードが現行GVと一致しない場合もある。自治体別の未照合コード・名称・原典内の日付・番地欠損は [coverage.json](coverage.json) / [coverage.csv](coverage.csv) を参照。

ベルリンHKは原典のGemeinde欄に区のコード・名称を持つ。原典コード・区名をborough_code/borough_nameにも保持し、全国GV照合用のベルリン市コード・名称と分ける。

NI/MVには自治体コード・原登録IDがない。MVのcityは地籍名・地域名の可能性があり、現在自治体の名称と断定しない。この2表の住所が各GV自治体に存在するかは、名前だけで照合しない。「コード一致の住所なし」は、そこで実際の住所が欠落しているという判定ではない。

## 行政区と道路の範囲

GV100は2026-09-30時点の15,984レコード。州16、地域区分29、計画地域12、郡区分401レコード、自治体連合等4,583レコード、自治体レベル10,943（自治体10,747・自治体に属さない区域196）を保持する。地域区分には統計上の区分を含む。自治体連合等の4,583レコードには、text_code=50の連合に属さない自治体等3,381レコードを含み、すべてを複数自治体の連合数とは扱わない。401レコードを現在の固有の法定郡総数と断定しない。親参照の未解決は0。

GVの2つの特殊な自治体連合コードは、共同DE/LU領域・MV沿岸水域の原典区分として、明記した規則で州へ結び付ける。領有権の判断ではない。全国のStadtbezirk・Ortsteil等の全細分名簿・境界は未照合。

独立道路名簿はBB 42,192・BE 11,547・TH 35,970行。Gazetteerの原応答ポリゴン、THの参照名・言語・名前属性は原本に保持する。住所内の道路キー数は住所から派生した集計として別に記録し、無番地道路の母数としない。

BKG DLM250のAX_Strassenachse全358,992公開オブジェクトを72ページから取得した。縮尺1:250,000に一般化された道路軸で、私道・細街路・無名道等の全物理道路ではない。道路形状は原GeoJSONに残し、検索結果は元ページと行番号を返す。州への空間帰属は計算していないため、道路軸を検索するときは `--state` を付けない。

## 原典と残る取得条件

- NW/RP/HE/BE/HBは公式配布を直接取得。NW Gebrefは道路名・番地・行政コード・座標を含み、396自治体の原典内件数表と4,509,543行が一致した。郵便属性の省略は、配達可能性を対象外とする今回の住所観測を除外する理由ではない。
- HHは公式2026-04-03過去版。7月配布先がこのセッションでHTTP 504のため、最新と表示しない。
- BB/SHは公開OpenAddressesアップロードの公式形式ミラー。元配布先との独立したバイト一致は未確認。
- NI/MV/SLは第三者のALKIS派生表・書き出し。原ALKIS全体を取得したとの主張はしない。SLは原ID・行政コード・原座標と変換後座標を保持する。
- THは公式INSPIRE WFSのAddress 611,051・ThoroughfareName 35,970・AdminUnitName 889を別々のhits総数と比較。GetFeatureのnumberMatchedはCOUNT適用後の値なので分母に使わない。Capabilitiesはpaging=falseと記載するため、STARTINDEXの実応答に加えて全IDの重複0・全タイプ件数・取得前後hits一致を検査した。複数ページの原子的な同時点スナップショットまでは証明しない。THの住所では253の原典自治体コード（105,602住所観測行）が現在のGVに存在せず、コード一致で住所を確認できるのは現行601自治体中575。残る26自治体と原典側の名称・件数を [reference-gap-review.json](reference-gap-review.json) に記録する。住所の現実の欠落を断定せず、後継自治体を名前だけで推測しない。
- BY：[公式HK WFS](https://geodatenonline.bayern.de/geodatenonline/seiten/wfs_hauskoor)は利用契約・認証情報が必要。申請・契約・購入は行っていない。
- BW/SN/ST：公開配布先を確認したが、このセッションでは503・Bad Gateway等により原本未取得。一般に公開データが存在しないという意味ではない。URL・エラー記録はcoverage.jsonと証拠ZIPに残す。

実際の全付番に対する独立した全国分母は未取得。番地の範囲・接尾字・先頭ゼロ・0という未付番値を保持し、範囲から番地を生成しない。現存・公認・居住・配達可能性を推定しない。

## 復元・検索・再照合

データ原本はGitに含めない。[payloads.json](payloads.json)の各ファイルを、ファイル名を変えず同じ新しいフォルダへ置く。州ZIPを展開せず、そのフォルダを `--data-root` とする。オランダや従来8書庫とは別のデータルートである。BKG/THのZIPとGazetteer gzipは原HTTP本文を損失なく保存するためにローカルで構成したもの。提供機関がそのZIP/gzipを配布したという主張ではない。小さな正規化済み行政参照 `DE_Administration_20260930.jsonl.gz` も付属する。

```bash
python3 scripts/hierarchy_cli.py --region western-europe -- inventory --country DE
python3 scripts/germany_sources.py acquire --data-root /path/to/de-data
python3 scripts/hierarchy_cli.py --region western-europe -- search --country DE --data-root /path/to/de-data --state NW --kind address --number 9 --limit 5
python3 scripts/germany_sources.py search --data-root /path/to/de-data --kind road_segment --limit 5
python3 scripts/germany_sources.py administration --data-root /path/to/de-data --output /path/to/de-administration.json
python3 scripts/germany_sources.py replay --data-root /path/to/de-data --accepted releases/hierarchy/western-europe/germany/validation.json --temp-dir /path/with/free/space --output /path/to/de-replay.json
```

`acquire` は既存原本をまず検証し、同名の異なるバイト列や既存途中ファイルを上書きしない。最新URLの内容が変われば新しいpinが必要。ローカル構成品・過去版等は保存済み原本を復元する。検索のnumberは原典文字列と完全一致し、number_additionは別属性で返す。元の行政コード・名前・スキーマもrawに残す。

全解析行のcanonical SHA-256、元ファイルのSHA-256、ZIP CRC・gzip復号後の原HTTP SHA-256、行政親参照、自治体コードを検査した。同じmanifestと全読込実装のハッシュで実際に再解析し、source_row_replay=PASSを確認した。取得時の失敗は受入済み観測行に加算しない。
