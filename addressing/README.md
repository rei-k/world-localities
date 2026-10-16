# Worldwide address compatibility layer

This package keeps country and language-specific rendering separate from factual
address verification. It accepts structured components in any mapping order,
normalizes aliases without discarding the original semantics, and renders them
with a pinned country profile.

The compiled profiles cover 251 country and territory codes and 16 source locale
variants from OpenCageData/address-formatting. Reviewed East, Southeast and
Southern Asia extensions bring runtime coverage to 64 locale profiles. They contain 48 new
locale profiles and 34 reviewed replacements, including Southeast and Southern
Asian base-country templates with explicit Address2/subpremise placement. Those
templates target display compatibility. They are not proof that a postal operator accepts an address,
that a street or premise exists, or that a shipment is deliverable.

Verification levels are separate: format, parsed components, locality, postal,
street, premise, subpremise and carrier/postal-operator deliverability. A higher
claim may only be emitted when evidence for that level is available.

```bash
python -m addressing verify
python -m addressing east-asia
python -m addressing southeast-asia
python -m addressing south-asia
python -m addressing profile --country JP --language ja
python -m addressing render --country JP --language ja \
  --components-json '{"country":"日本","postcode":"1000005","state":"東京都","city":"千代田区","neighbourhood":"丸の内","house_number":"1-1"}'
```

## East Asia native and English output

`east_asia_profiles.json` covers CN, HK, JP, KP, KR, MN, MO and TW. Every
country/area has one default native-language profile and an English profile;
Macao additionally supports Portuguese, while Mongolia keeps Cyrillic and
traditional Mongolian script values distinct. Language-dependent values are supplied
explicitly so that an unverified transliteration cannot silently become an
"English official name". Numeric fields such as postcodes and house numbers are
shared safely. Strict mode refuses output when a required English value is
missing or contains non-Latin letters.

```bash
python -m addressing render-bilingual --country JP --components-json \
  '{"postcode":"1000005","state":{"ja":"東京都","en":"Tokyo"},"city":{"ja":"千代田区","en":"Chiyoda-ku"},"road":{"ja":"丸の内","en":"Marunouchi"},"house_number":"1-1"}'
```

The extension records postal-authority sources and a romanization policy per
country. KP remains explicitly `provisional`; the system does not present that
profile as postal-operator verified. Automatic machine translation is not used
as address evidence.

## Southeast Asia native and English output

`southeast_asia_profiles.json` covers BN, KH, ID, LA, MY, MM, PH, SG, TH, TL
and VN. It provides 14 domestic-language variants and an explicit English
profile for every country. Singapore separates Malay, Simplified Chinese and
Tamil; Timor-Leste separates Tetum and Portuguese. Latin-script domestic values
such as Malay, Indonesian, Filipino and Vietnamese still require an explicit
`en` value and are never relabelled as English merely because the script is
compatible.

Address2 is rendered through the country template. Structured block, entrance,
floor and unit fields are combined into the same subpremise line without being
reported as dropped. Myanmar and Timor-Leste remain `provisional` because the
reviewed public operator material did not expose a complete current bilingual
country template.

```bash
python -m addressing render-southeast-asia --country TH --components-json \
  '{"postcode":"12130","state":{"th":"ปทุมธานี","en":"Pathum Thani"},"road":{"th":"ถนนรังสิต-นครนายก 4","en":"Rangsit-Nakhon Nayok 4 Road"},"house_number":"491"}'
```

The shared localized engine rejects cross-script fallback, missing English
components and non-Latin text labelled as English. Automatic translation or
romanization may propose a candidate in a separate workflow, but it cannot
promote that candidate to verified address evidence.

## Southern Asia native and English output

`south_asia_profiles.json` covers AF, BD, BT, IN, IR, LK, MV, NP and PK. It
provides 11 nationwide domestic-language variants and an explicit English
profile for all nine countries. Afghanistan separates Dari and Pashto; Sri
Lanka separates Sinhala and Tamil. The India profile currently represents the
Union-level Hindi and English path rather than claiming separate coverage for
every state language.

The shared engine validates Arabic, Bengali, Devanagari, Sinhala, Tamil,
Thaana and Tibetan scripts for native-language fields. It also rejects Unicode
bidirectional embedding, override and isolate controls that could disguise an
RTL address value. Numeric house numbers and postcodes remain safely shareable.

```bash
python -m addressing render-south-asia --country IN --components-json \
  '{"postcode":"110003","state":{"hi":"दिल्ली","en":"Delhi"},"city":{"hi":"नई दिल्ली","en":"New Delhi"},"road":{"hi":"अमृता शेरगिल मार्ग","en":"Amrita Shergill Road"},"house_number":"4"}'
```

Nepal remains `provisional`: the public postal material shows a 2025 migration
to federal local-level and ward-level codes, while the older international
country sheet still documents the legacy five-digit form. The renderer keeps
the supplied current code but does not silently convert or certify a legacy one.

`profiles.json` is generated by `scripts/compile_address_profiles.py`. The
source commit and SHA-256 are embedded in the generated file. Runtime use is
standard-library only; refreshing the profiles requires PyYAML.

## Source and license

The formatting profiles are derived from
<https://github.com/OpenCageData/address-formatting>, copyright 2020 OpenCage
GmbH, under the MIT License; the required notice is preserved in
`LICENSE.address-formatting.txt`. The source project describes the templates as
consumer-facing geographic address formatting and explicitly excludes some
postal-mail concerns such as apartment numbers and PO boxes. This package
therefore adds loss-avoidance warnings and keeps Address2/subpremise support as
an explicit compatibility layer rather than claiming source verification.
