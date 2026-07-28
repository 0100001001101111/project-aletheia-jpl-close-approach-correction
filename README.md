# Eight JPL close-approach records corrected

Project Aletheia found eight NASA/JPL asteroid close-approach records whose
numbers contradicted one another. JPL investigated the private report and
confirmed an issue affecting pathological cases with close approaches to
multiple bodies within a short time window. JPL fixed the example record and
said the others should be fixed as well; Aletheia then verified all eight.

## The simple version

Each record contained a best-estimate distance and an allowed distance range.
The best estimate sat outside its own range.

The asteroid encounters were real. The defect was in how fields were assembled
into a record when an object passed near Earth and the Moon close together in
time.

## Reported objects

- 367943
- 2019 DP
- 2019 XN3
- 2021 VH2
- 2022 NJ
- 2018 QE
- 2016 SW3
- 2020 OO1

## Reproduce the post-fix check

Requires Python 3 and internet access:

```bash
python3 verify_live_fix.py
```

Expected result:

```text
PASS: 8 of 8 reported objects have zero distance-order violations
```

The script performs read-only requests to the official JPL CAD API. It checks
whether every complete row obeys:

```text
dist_min <= dist <= dist_max
```

## Included evidence

- `preregistration.json`: frozen test definition.
- `pre_fix_audit.json`: the preserved audit of the affected records before the
  provider correction.
- `pre_fix_download_receipt.json`: source, capture date, and checksum for the
  preserved pre-fix API snapshot.
- `post_fix_receipt.json`: the dated result after correction.
- `verify_live_fix.py`: a compact independent live checker.

The frozen candidate list contained a ninth object, 2017 VR12. Its live row was
already internally consistent when the pre-fix snapshot was captured, so it
was retained in the audit as a negative comparison and was not one of the
eight records reported to JPL.

## Claim boundary

Aletheia identified eight internally inconsistent JPL close-approach records.
JPL confirmed an issue affecting pathological cases with close approaches to
multiple bodies within a short time window. Aletheia then verified that the
eight reported records were corrected.

This was a data-generation defect, not a new asteroid, an orbit error, or
evidence of anomalous asteroid motion.

Full public finding: https://projectaletheia.org/findings?view=supported

Official API documentation:
https://ssd-api.jpl.nasa.gov/doc/cad.html
