# JASS Real Ownership Calculator v2.0.0

## Purpose

This version is designed around the Haryana/Punjab-style Jamabandi distinction between:

- **Khana Milkiyat / Owner column** — recorded ownership and ownership fraction.
- **Khana Kasht / Cultivation column** — the person occupying/cultivating a specific holding; in Haryana, historical "Khana Kasht" / special-number entries could remain in the cultivation column after a share was sold without first updating the ownership column.

Current reporting from Sirsa describes this exact historical arrangement: a co-sharer could sell part of a holding to a third party, the buyer could be entered in column 5 as a special-number/Khana Kasht entry, and the original ownership record could remain unchanged until partition/correction. Haryana reporting in January 2026 also describes the resulting mismatch and a process to move such buyers into the ownership column after verification.

## Calculation principle

For an owner:

**Real ownership area = Recorded ownership area − confirmed sold/deducted area**

and:

**Real ownership fraction = Real ownership area ÷ total area**

The application does **not** assume that every cultivator is a purchaser. It extracts the Khana Kasht entries separately.

Only deductions that are explicitly checked and assigned to a seller-owner are subtracted.

If the source does not establish which owner sold a specific holding, the app leaves that deduction **unassigned** rather than guessing.

## Main output

| Owner Name | Recorded Fraction | Recorded Share | Sold / Deducted | Real Ownership | Real Fraction |
|---|---|---|---|---|---|

All areas are displayed as **Kanal-Marla-Sarsahi**, rounded to whole Sarsahi and normalized.

## Secondary ledger

The **Khana Kasht / Specific Numbers** tab extracts:
- Khatoni
- Cultivator / Buyer
- Fraction
- Khasra No.
- Area
- Deduct checkbox
- Owner to Deduct From

The user can review the source and assign a deduction to the relevant seller.

## Why this cautious approach is necessary

The Jamabandi distinguishes ownership and cultivation columns, but a cultivation entry alone does not always prove which recorded co-owner sold the parcel. A legal ownership conclusion may require the mutation/deed record.

The application is therefore an **arithmetic and record-analysis tool**, not a legal determination.

## Run

```bash
pip install -r requirements.txt
python main.py
```
