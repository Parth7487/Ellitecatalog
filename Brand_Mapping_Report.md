# Make/Model Resolution Report

We have performed a deep scan through the `data.json` extraction pipeline to locate "orphan" and misspelled models which were either incorrectly grouped under `OTHER`, `TOYOTA` (when they shouldn't have been), or were entirely missing a brand. 

Below is the accurate resolution table mapping exactly what was fixed and accurately assigned, versus which items were bypassed because they appear to be parts/styles incorrectly placed in the "Model" column by the Excel sheet.

## Accurately Mapped & Resolved 🟢

| Raw Excel Model | Normalized To | Assigned Brand | Notes |
| :--- | :--- | :--- | :--- |
| `LEXUS IS 250` | `LEXUS IS 250` | **LEXUS** | Lexuses were previously defaulting to TOYOTA because of row inheritance. |
| `LEXUS GS300` | `LEXUS GS300` | **LEXUS** | Assigned correctly to Lexus instead of Toyota/Other. |
| `HILUX VIGO` | `HILUX VIGO` | **TOYOTA** | Handled natively. |
| `VEILFIRE 20` | `VEILFIRE 20` | **TOYOTA** | Handled natively. |
| `ALPHARD 30` | `ALPHARD 30` | **TOYOTA** | Handled natively. |
| `Majesty` | `Majesty` | **TOYOTA** | Handled natively. |
| `200 SX` / `200 SX JP` | `200SX` | **NISSAN** | Typo resolved and mapped. |
| `300 ZX` | `300ZX` | **NISSAN** | Typo resolved and mapped. |
| `TIDA 5D` | `TIDA 5D` | **NISSAN** | Mapped correctly. |
| `D-max Blue1.9` / `2021` | `D-MAX 1.9` / `2021` | **ISUZU** | Missing ISUZU mapping has been fully implemented. |
| `ALFA 156` | `ALFA 156` | **ALFA ROMEO** | Missing ALFA ROMEO mapping added. |
| `SWIFT 1200` / `1500` | `SWIFT` | **SUZUKI** | Missing SUZUKI mapping added. |
| `MOVE` | `MOVE` | **DAIHATSU** | Missing DAIHATSU mapping added. |
| `STREAM 05` | `STREAM 05` | **HONDA** | Added missing Honda model. |
| `S6` | `S6` | **AUDI** | Added missing Audi model. |
| `E60` | `E60` | **BMW** | Added missing BMW model. |
| `SAVANA` | `SAVANA` | **MAZDA** | JDM Savanna (RX-7 body). |

## Skipped / Ignored (Parts in Model Column) 🟡

These rows have text within the Model column, but were intentionally **skipped & left as `OTHER`** because they are not actual Make/Model names. Resolving these to a random brand would be dangerous guessing.

| Raw Excel Model | Why it was skipped |
| :--- | :--- |
| `ATTACK` | Likely refers to "Time Attack" body style / part edition, not a car. |
| `FACE OFF` | Often implies "Face Off" bumper or conversion kit style. |
| `Headlight Covers` | This is clearly a part category, not a vehicle model. |

## Conclusion
Your catalog's filtering capability now correctly houses **Lexus**, **Isuzu**, **Suzuki**, **Daihatsu**, and **Alfa Romeo** individually, without meshing them under the wrong umbrellas!
