# Worldwide address compatibility layer

This package keeps country and language-specific rendering separate from factual
address verification. It accepts structured components in any mapping order,
normalizes aliases without discarding the original semantics, and renders them
with a pinned country profile.

The compiled profiles cover 251 country and territory codes and 16 source locale
variants from OpenCageData/address-formatting. Reviewed East, Southeast,
Southern, Central and Western Asia extensions bring runtime coverage to 117
locale profiles. They contain 101 new locale profiles and 57 reviewed
replacements, including Southeast, Southern, Central and Western Asian
base-country templates with explicit Address2/subpremise placement. Those
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
python -m addressing central-asia
python -m addressing western-asia
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

## Central Asia native and English output

`central_asia_profiles.json` covers KG, KZ, TJ, TM and UZ. It provides nine
script-qualified domestic-language variants and a separate English profile for
all five countries. Kyrgyzstan, Kazakhstan and Tajikistan keep their national
language and Russian values distinct even where both use Cyrillic. Uzbekistan
supports explicit `uz-Latn` and `uz-Cyrl` inputs through the same national line
ordering, while Turkmen Latin values still cannot silently populate English.

The shared engine validates Cyrillic letters and permits the modifier-letter
apostrophes used in Uzbek Latin without weakening mixed-script rejection.
QazPost's seven-character building postcode and the transitional six-digit
numeric code are both preserved; no conversion is attempted. Kyrgyzstan,
Tajikistan and Uzbekistan keep their six-digit code before the locality, while
Turkmenistan keeps its six-digit code on a separate line after locality and
province information.

```bash
python -m addressing render-central-asia --country UZ --components-json \
  '{"postcode":"100123","city":{"uz-Latn":"Toshkent","uz-Cyrl":"Тошкент","en":"Tashkent"},"road":{"uz-Latn":"Amir Temur koʻchasi","uz-Cyrl":"Амир Темур кўчаси","en":"Amir Temur Street"},"house_number":"4"}'
```

Every Central Asia profile carries operator or UPU provenance. The profiles
validate representation and line order only; street, premise, Address2 and
deliverability claims still require evidence at their corresponding validation
level.

## Western Asia native and English output

`western_asia_profiles.json` covers AE, AM, AZ, BH, CY, GE, IL, IQ, JO, KW,
LB, OM, PS, QA, SA, SY, TR and YE. It provides 22 domestic-language variants
and a separate English profile for all 18 countries and areas. Cyprus separates
Greek and Turkish, Iraq separates Arabic and Kurdish, Israel separates Hebrew
and Arabic, and Lebanon separates Arabic and French.

Arabic, Armenian, Greek, Georgian, Hebrew and Latin scripts are validated.
Languages sharing a script remain separate: Iraqi Arabic cannot fill Kurdish,
and Lebanese French or Turkish cannot silently become English. Address2 is
explicit in every national template.

The profiles preserve materially different postal systems: Azerbaijan's
`AZ`-prefixed code, Cyprus's inbound `CY-` prefix, Israel's seven digits,
Palestine's current P-prefixed eight-character code, Oman's standalone
three-digit line, Saudi Arabia's National Address order, and countries whose
reviewed public templates do not use a postcode. AE, IQ, JO, KW, SY and YE are
marked `provisional` because their public country sheets are old, incomplete,
or unavailable; output from those profiles always carries a warning.

```bash
python -m addressing render-western-asia --country SA --components-json \
  '{"postcode":"12643","city":{"ar":"الرياض","en":"Riyadh"},"road":{"ar":"طريق الملك عبدالعزيز","en":"King Abdulaziz Road"},"house_number":"8228","address2":{"ar":"الوحدة 18","en":"Unit 18"}}'
```

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
