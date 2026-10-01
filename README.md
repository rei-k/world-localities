# World Localities

世界の行政区画・都市・集落と、別出典の公式コード・名称・郵便関連を、出典付きで管理します。
データはすべて `regions/` にまとめ、地域ごとに基礎地名パッケージ `gazetteer/` と公式資料 `official/` を区別します。
国別のスキーマ、ID、取得時点、未解決の所属、利用条件はそのまま保持しています。

## ディレクトリ

```text
regions/
├── africa/gazetteer/
├── asia/
│   ├── gazetteer/
│   └── official/                 # JP・TW
├── europe/
│   ├── gazetteer/
│   └── official/eurostat-lau/
├── oceania/gazetteer/            # 元の国別パックを維持
└── americas/
    ├── northern/official/       # US・CA
    ├── central/
    │   ├── gazetteer/           # BZ・GT・HN・NI・PA・SV
    │   └── official/MX/
    ├── caribbean/gazetteer/
    ├── southern/
    │   ├── gazetteer/
    │   └── official/BR/
    └── official/                # 米州公式台帳の共通スキーマ・出典
scripts/                         # 地域横断の検証
tests/                          # 地域横断の回帰テスト
docs/                            # 設計・移行ガイド
training/                        # 学習計画（学習自体は未実行）
```

機械可読の入口は [catalog.json](catalog.json)、旧パスとの対応は [移行ガイド](docs/directory-layout.md) です。
米州の `northern` はUN M49の **Northern America（021）**、`central` は **Central America（013）**、
`caribbean` は **Caribbean（029）**、`southern` は **South America（005）** を表すフォルダ名です。
メキシコは `central` に配置します。分類は [UN M49](https://unstats.un.org/unsd/methodology/m49/) に従い、領有権や法的地位を判定しません。
欧州・アジアの既存の広域スコープは、重複を含めて維持しています。

## 現在の収録範囲

| 地域 | 基礎地名パッケージ | 公式資料・対応表 |
|---|---|---|
| [アフリカ](regions/africa/gazetteer/README.md) | 56か国・地域、388,038件。CD・MA・MG・NGは未移行 | 未収録 |
| [アジア＋ロシア全域](regions/asia/gazetteer/README.md) | 52プロファイル、3,277,921件 | [JP・TW](regions/asia/official/README.md)の公式名称・郵便関連。アジア全面対応ではない |
| [ヨーロッパ](regions/europe/gazetteer/README.md) | 57か国・地域、1,161,589件 | [Eurostat LAU](regions/europe/official/README.md)：32か国、104,687行 |
| [オセアニア](regions/oceania/gazetteer/README.md) | 29か国・地域、46,594件、名称37,236件 | 同梱の別レイヤーにAU ABS公式コード567件。GeoNames直接ID郵便対応262行は公式郵便台帳ではない |
| [米州・北部](regions/americas/northern/README.md) | GeoNamesパッケージは未収録 | US 68,744行・CA 5,054行の保存済み公式資料。地域全面対応ではない |
| [中央アメリカ](regions/americas/central/gazetteer/README.md) | 8対象中6か国、53,257件。CR・MXのGeoNamesは未収録 | MX 2,478行の公式資料を別収録 |
| [カリブ](regions/americas/caribbean/gazetteer/README.md) | 28対象中27か国・地域、50,581件。CUは未収録 | Puerto RicoのUS公式資料はUSの原典パッケージ内に維持 |
| [南アメリカ](regions/americas/southern/gazetteer/README.md) | 16対象中14か国・地域、241,514件。AR・PYは未収録 | BR 5,571行の公式資料を別収録 |

件数は各原典のレコード数です。GeoNames・公式自治体・統計上の区域を足して自治体数にしません。
米州公式4か国の詳細・制約は [共通ガイド](regions/americas/official/README.md) にあります。
USのCensusパッケージにはPuerto Ricoが含まれます。原典内の `address_country=PR` を保持し、
カリブのPR GeoNamesパッケージとの同一地物判定や自動統合はしません。

取得日・版・ハッシュは各国メタデータを確認してください。内部検証の合格は現在の法的行政階層、
公式英訳、全自治体の網羅、郵便配達可否の認定ではありません。Address1・企業名簿・境界ポリゴンは対象外です。

## 利用と検証

Python 3.11以降。読み込み・検索・構造検証は標準ライブラリで実行できます。
以下はリポジトリのルートから実行します。

```bash
python regions/europe/gazetteer/query.py --country AT --level 1
python regions/africa/gazetteer/query.py --country KE --level 1
python regions/asia/gazetteer/package.py unpack --country JP
python regions/asia/gazetteer/build.py verify --country JP
python regions/asia/official/query.py --country JP --postal-code 0600000 --language ja-Latn
python regions/asia/official/query.py --country TW --postal-code 300 --language en --include-prefix
python regions/americas/central/gazetteer/query.py --country BZ --level 1
python regions/americas/caribbean/gazetteer/query.py --country AG --level 1
python regions/americas/southern/gazetteer/query.py --country UY --text Montevideo --limit 10
python scripts/verify_americas_snapshots.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

オセアニアはパック読み込み用のコマンドを使います。

```bash
cd regions/oceania/gazetteer
python -m addresskit.region_names --pack . label country:NZ --mode local --locale mi
python -m unittest discover -s tests -p test_region_names.py -v
```

今回の配置変更の検証結果と未実施範囲は [directory-validation.json](docs/directory-validation.json) に記録しています。
各地域のREADMEに再構築・検証方法があります。分割ファイルは、付属の展開・materialize処理で
元のハッシュを検査して読み込みます。パッケージ内部の相対パスと圧縮データのバイト列は維持しています。
名前空間と原典が異なるIDを同名だけで結合せず、共有 `gn:` IDも版と出典を確認して扱ってください。

## 出典・利用条件と設計

出典URL・ライセンス・帰属表示は各パッケージに同梱しています。コードのライセンスをデータへ適用しません。
[欧州の移行元](https://github.com/rei-k/world-address/pull/406)、
[アジアの固定スナップショット](https://github.com/rei-k/world-address/tree/8e30ef141e40769fa932adeb2f901505023bfd1e/address-foundation/asia-registry)、
[公式情報の拡充設計](docs/enrichment-plan-ja.md)、[アジア学習計画](docs/asia-learning-plan-ja.md) も参照してください。
モデル学習・精度改善の実証は未実行です。
