# Phase 4: Receipt Attachment Integrity, HMRC Digital Links (Notice 700/22), and Audit Compliance
**Role:** UK Chartered Accountant Lead (ICAEW / ACCA)  
**Status:** Definitive Engineering & Regulatory Specification  
**Governing Authorities:** HMRC VAT Notice 700/22, VAT Notice 700 §19, VATA 1994 Sch 11, VAT Regulations 1995 (SI 1995/2518), TMA 1970 s12B, FA 1998 Sch 18, FA 2008 Sch 36, Xero Accounting API Documentation.

---

## 1. Statutory Digital Record-Keeping & Digital Links

### 1.1 The Exact Legal Requirement for Digital Links (VAT Notice 700/22 §3.3 & §4)
There is a fundamental legal distinction between **Making Tax Digital (MTD) Digital Links** and **Statutory Input Tax Deductibility Evidence**:

1. **The MTD Digital Link Boundary (VAT Notice 700/22 §3.3.3 & §4.2):**
   - Under Making Tax Digital for VAT regulations, HMRC mandates that data transferred between different software applications or components forming the "functional compatible software" must flow via automated, electronic **digital links** (e.g., API calls, database links, automated formula links, direct file imports). Manual rekeying or copy-and-pasting of summary figures is strictly unlawful.
   - **Crucial Statutory Clarification (Notice 700/22 §3.3.3):** HMRC explicitly specifies that **there is no legal requirement under MTD to maintain an electronic digital link between a scanned image/photo of a source document (receipt/invoice) and the digital records**. The MTD digital chain legally begins at the moment transaction data is captured into functional compatible software and continues through to the submission of the 9-box VAT return via HMRC's API.

2. **The Input Tax Deductibility Mandate (VATA 1994 s24–s26 & VAT Regs 1995 SI 1995/2518 Reg 29(2)):**
   - Under Regulation 29(2) of the VAT Regulations 1995, a taxable person claiming input tax deduction (Box 4 of the VAT Return) **must hold a valid VAT invoice** issued by the supplier at the time the claim is made.
   - If an expense is entered into Xero without a valid attached receipt or invoice, HMRC has statutory authority under **VATA 1994 s73** to disallow the deduction, raise an assessment clawing back the VAT, charge commercial restitution interest (s74), and levy penalties under **FA 2007 Sch 24**.
   - **Conclusion:** While MTD Notice 700/22 does not strictly require the image itself to be linked via the MTD chain, substantive tax law makes an immutable, verifiable link between the Xero Draft Bill and the digital receipt image the **sole legal defense** against input tax clawback during an HMRC compliance check.

---

### 1.2 Statutory Retention Period (VATA 1994 Sch 11 & TMA 1970 s12B)

All business and VAT records must be preserved for the following statutory durations:

| Tax Regime / Business Structure | Governing Statutory Authority | Minimum Retention Period |
| :--- | :--- | :--- |
| **VAT Records & Tax Invoices** | VATA 1994 Sch 11 para 6(3) & VAT Notice 700 §19.2 | **6 years** from the date of the record/transaction |
| **Corporation Tax (Limited Companies)** | FA 1998 Sch 18 para 21 & Companies Act 2006 s388 | **6 years** from the end of the relevant accounting period |
| **Income Tax Self Assessment (ITSA)** | TMA 1970 s12B(2)(a) (Sole Traders & Partnerships) | **5 years from 31 January** following the year of assessment (~5 years 10 months) |
| **Capital Goods Scheme (CGS)** | Value Added Tax Regulations 1995 Part XV & Notice 706/2 | **10 years** for land/buildings; **5 years** for computer equipment costing £50,000+ |
| **Open HMRC Compliance Check / Enquiry** | TMA 1970 s12B(3) & FA 1998 Sch 18 para 21(3) | **Indefinitely** until formal closure notice or final determination |
| **Suspected Deliberate Tax Evasion / Fraud** | VATA 1994 s77(4) & TMA 1970 s36(1A) | **Up to 20 years** (HMRC assessment discovery window) |

---

### 1.3 Digital Photos as Primary Tax Evidence & Paper Destruction

Can physical receipts be discarded after photographing? **YES.**

- **Statutory Authority:**
  - HMRC VAT Notice 700 §19.7 ("Can I store records on an electronic system?").
  - HMRC Compliance Handbook Manuals **CH13100** ("Record keeping: General") and **CH13400** ("Optical imaging").
  - Former Inland Revenue **Tax Bulletin Issue 21** (February 1996) and **Tax Bulletin Issue 37** (October 1998) (historically cited alongside Statement of Practice SP 1/95 principles).

- **The Four Statutory Conditions for Discarding Paper Receipts:**
  HMRC permits businesses to destroy physical paper receipts immediately following digitization provided that:
  1. **Complete & Unaltered Reproduction:** The electronic copy captures an exact, complete image of the original document. If the paper receipt has handwritten notes, itemized breakdowns, or terms on the reverse, **both front and back** must be photographed.
  2. **Legibility:** The digital copy can be reproduced in a legible, readable format on screen and printed upon request by an HMRC visiting officer.
  3. **Tamper-Evident Integrity:** The storage architecture ensures that the image cannot be modified, edited, replaced, or degraded over time.
  4. **Immediate Accessibility:** Records must be readily retrievable during an HMRC audit for the full 6-year retention period.

- **Statutory Exceptions (Physical Paper Must Still Be Kept):**
  - Customs export/import documentation with original physical rubber stamps or wet endorsements (CH13300).
  - Specific paper certificates of tax deduction where primary legislation specifies original physical vouchers.
  - Standard trade and business expense receipts (fuel, hardware, software, subsistence, transport) **do not** require paper retention and can be discarded once digitized.

---

### 1.4 Evidential & Forensic Metadata Preserved with Digital Images

To satisfy the evidentiary requirements under the **Civil Evidence Act 1995 s8**, the **Police and Criminal Evidence Act 1984 s69**, and **VAT Regulations 1995 Regs 14 & 16**, every stored receipt image must be permanently bound to the following metadata ledger:

```
+---------------------------------------------------------------------------------------------------+
|                                  RECEIPT METADATA LEDGER                                          |
+---------------------------------------------------------------------------------------------------+
| 1. Cryptographic Hash:   SHA-256 (64 hex characters computed at raw ingestion before upload)      |
| 2. Ingestion Timestamp:  ISO 8601 / RFC 3339 UTC timestamp (e.g., 2026-10-12T14:32:00.123456Z)    |
| 3. Channel Provenance:   Source identifier (Twilio Message SID, WhatsApp Sender ID, User UUID)    |
| 4. Technical Attributes: File size (bytes), original file extension, detected MIME type          |
| 5. Statutory Tax Data:   Supplier Legal Name, UK VAT Reg No (9 digits), Tax Point Date (VATA s6)  |
| 6. Financial Ledger:     Net Amount, VAT Rate (20%/5%/0%/Exempt), VAT Amount, Gross Amount       |
| 7. Accounting Linkage:   Xero InvoiceID (GUID), Xero AttachmentID (GUID), Sync Timestamp         |
| 8. Verification Status:  Mathematical checksum: |(Net + VAT) - Gross| <= 0.01                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Receipt Attachment Requirements in Xero & Accounting Best Practices

### 2.1 Xero API Constraints & Supported File Formats

When attaching files via the Xero Accounting API (`PUT /api.xro/2.0/{Endpoint}/{Guid}/Attachments/{Filename}`):

- **Payload & Endpoint Mechanism:**
  - The HTTP request body must contain the **raw binary byte stream** of the file (not JSON, not form-data).
  - The `Content-Type` header must accurately reflect the file MIME type (e.g., `image/jpeg`, `image/png`, `application/pdf`).
- **File Size Limit:**
  - **Strictly 10 MB per individual file** (Xero API request limit). Files exceeding 10 MB trigger HTTP `413 Payload Too Large` or `500 Server Error`.
- **Maximum Attachments:**
  - Up to **10 attachments** per invoice/bill.
- **Accepted Formats:**
  - **Documents:** PDF (`application/pdf`), DOC/DOCX, XLS/XLSX, CSV, TXT, RTF.
  - **Images:** JPEG/JPG (`image/jpeg`), PNG (`image/png`), GIF (`image/gif`), BMP (`image/bmp`), TIFF (`image/tiff`).
- **The iOS HEIC Trap & Transcoding Requirement:**
  - Apple iPhones capture photos in HEIC/HEIF format (`image/heic`).
  - Xero’s Accounting API attachments endpoint does not reliably render or support native HEIC files in the Xero web previewer.
  - **Requirement:** Any incoming HEIC payload must be detected and transcoded to high-resolution JPEG (`image/jpeg`) prior to calling Xero's attachment endpoint.

---

### 2.2 Failure Isolation Pattern: Corrupted, Zero-Byte & Failed Attachments

**Fundamental Accounting Axiom:** *The Financial Ledger Must Never Be Compromised by Media Failure.*

If a receipt image is zero-byte, corrupted, or if the attachment API upload fails:
**DO NOT DROP, DELETE, OR ROLL BACK THE DRAFT BILL IN XERO.**

#### Rationale:
1. The creation of an `ACCPAY` Draft Bill in Xero reflects an actual commercial liability to a supplier and an incurred business transaction.
2. If the draft bill is dropped, incoming bank feed transactions cannot be matched/reconciled, creating unreconciled bank balances, obscured liabilities, and risk of duplicate manual entry.
3. However, claiming input tax on a transaction that lacks supporting evidence exposes the business to HMRC penalties.

#### Architecture of the Failure Isolation Pattern:
```
           +-------------------------------------------------------------+
           | Phase 1: Create ACCPAY Draft Bill in Xero                   |
           | (Persist external_bill_id in hmrc_ledger immediately)       |
           +-------------------------------------------------------------+
                                          |
                                          v
           +-------------------------------------------------------------+
           | Pre-Flight Attachment Checks:                               |
           | 1. len(bytes) > 0 (Zero-byte check)                         |
           | 2. Magic byte check (JPEG \xFF\xD8\xFF, PNG, PDF)           |
           | 3. Size <= 10MB (Compress if > 10MB)                        |
           +-------------------------------------------------------------+
                        /                                \
                 [VALID]                                  [FAILED / CORRUPTED]
                    /                                              \
                   v                                                v
+------------------------------------+             +------------------------------------+
| Phase 2a: Upload to Xero           |             | Phase 2b: Isolate Failure          |
| -> PUT Invoices/{id}/Attachments   |             | 1. Keep Draft Bill in Xero         |
| -> Set attachment_status='UPLOADED'|             | 2. Append [RECEIPT FAILED] to Ref  |
| -> Store Xero Attachment GUID      |             | 3. Set status='ATTACHMENT_FAILED'  |
+------------------------------------+             | 4. Alert user: "Re-send receipt"   |
                                                   | 5. Freeze approval from Box 4 VAT  |
                                                   +------------------------------------+
```

---

### 2.3 The HMRC VAT Inspection Protocol (Box 4 Audit Drill-Down)

When an HMRC Officer conducts a compliance check under **Finance Act 2008 Schedule 36**, they systematically execute the following 5-pillar verification procedure:

```
HMRC VAT Audit Step-by-Step Drilldown:
  1. Box 4 Audit Sampling (VAT Detail Report filtered by high value, electronics, meals, travel)
     └─> 2. Open Xero Draft / Approved Bill
           └─> 3. Click attached receipt document
                 ├─> Pillar 1: Valid Supplier VAT Registration No. (Validated on HMRC VAT database)
                 ├─> Pillar 2: Tax Point Alignment (Receipt date falls strictly inside VAT period)
                 ├─> Pillar 3: Calculation & Rate Integrity (Standard 20% vs Zero-rated items separated)
                 ├─> Pillar 4: Business Purpose & Statutory Exclusions (No client entertainment / private use)
                 └─> Pillar 5: Simplified vs Full Tax Invoice Thresholds:
                       • If Gross <= £250: Simplified Invoice rules (Reg 16)
                       • If Gross > £250: Full Invoice rules (Reg 14) requiring Customer Name & Address
```

#### Detailed Breakdown of the 5 Pillars:
1. **Pillar 1: Supplier VAT Credential:** The officer extracts the 9-digit VAT number from the receipt and queries HMRC’s internal database. If the supplier was cancelled or unregistered at the tax point date, input tax is disallowed.
2. **Pillar 2: Tax Point Alignment (VATA 1994 s6 & Reg 29(1)):** Verifies that the date on the receipt matches the transaction date on the bill and falls within the audited VAT quarter. Reclaiming input tax on an out-of-period receipt without statutory bad debt or late recovery rules triggers an adjustment.
3. **Pillar 3: Mixed-Rate Supermarket / Retail Invoices:** The officer inspects itemized line items on till receipts. For example, on a Sainsbury's/Tesco receipt, food items (bread, fruit) are 0% zero-rated, whereas cleaning supplies are 20%. The system must not apply 20% across the entire gross sum.
4. **Pillar 4: Statutory Deductibility Exclusions:**
   - *Client Entertainment Exclusion:* Under **The Value Added Tax (Input Tax) Order 1992 (SI 1992/3222) Article 4**, VAT incurred on entertaining clients, suppliers, or non-employees is **strictly barred from recovery**, even if incurred wholly for business promotion.
   - *Private Consumption:* Personal items or domestic utilities without business split apportionment are disqualified.
5. **Pillar 5: Simplified vs. Full VAT Invoice Threshold (£250 Rule):**
   - **Under £250 (Inclusive of VAT) — Regulation 16 (Simplified Invoice):** Requires only the supplier’s name, address, VAT registration number, tax point date, description of goods/services, total payable including VAT, and rate of VAT charged. The customer's name is **not** legally required.
   - **Over £250 (Inclusive of VAT) — Regulation 14 (Full VAT Invoice):** Must include a unique sequential invoice number, customer's full trading name and address, unit price excluding VAT, net total, and itemized VAT total. **Crucial Audit Vulnerability:** If a founder buys a £1,400 MacBook Pro at Currys or Apple and only obtains an anonymous retail till slip without the business name, an HMRC officer can legally disallow the entire £233.33 input tax claim!

---

## 3. Definitive Phase 4 Engineering Specification

### 3.1 Database Schema Extensions

To establish full digital links, audit compliance, and attachment failure isolation, the PostgreSQL schema must be upgraded with the following structures:

```sql
-- 1. Receipt Attachments Audit Table
CREATE TABLE IF NOT EXISTS receipt_attachments (
    id SERIAL PRIMARY KEY,
    ledger_id INTEGER NOT NULL REFERENCES hmrc_ledger(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    storage_uri TEXT NOT NULL,
    attachment_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    xero_attachment_id VARCHAR(100) NULL,
    error_details TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_receipt_attachments_ledger_id ON receipt_attachments(ledger_id);
CREATE INDEX IF NOT EXISTS idx_receipt_attachments_sha256 ON receipt_attachments(sha256_hash);

-- 2. Ledger Table Enhancements
ALTER TABLE hmrc_ledger 
ADD COLUMN IF NOT EXISTS attachment_status VARCHAR(50) DEFAULT 'NO_ATTACHMENT',
ADD COLUMN IF NOT EXISTS receipt_sha256 CHAR(64) NULL,
ADD COLUMN IF NOT EXISTS attachment_error TEXT NULL;
```

---

### 3.2 Pre-Flight Validation & Media Transformation Engine

```python
import hashlib
import io
from PIL import Image

def validate_and_normalize_receipt(file_bytes: bytes, original_url: str) -> tuple[bytes, str, str, str]:
    """
    Validates, transcodes, and calculates cryptographic hash for receipt attachment.
    Returns: (normalized_bytes, filename, mime_type, sha256_hash)
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("ZERO_BYTE_FILE: Ingested receipt is 0 bytes.")

    if len(file_bytes) > 10 * 1024 * 1024:
        # File exceeds 10MB Xero API hard limit: compress image
        file_bytes = compress_image_under_limit(file_bytes, target_max_bytes=9 * 1024 * 1024)

    # Magic Bytes Signature Verification
    if file_bytes.startswith(b"%PDF"):
        mime_type = "application/pdf"
        ext = "pdf"
    elif file_bytes.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
        ext = "jpg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
        ext = "png"
    elif file_bytes[4:12] in (b"ftypheic", b"ftypmif1", b"ftypheix", b"ftypmsf1"):
        # HEIC format: transcode to JPEG for Xero previewer compatibility
        file_bytes = transcode_heic_to_jpeg(file_bytes)
        mime_type = "image/jpeg"
        ext = "jpg"
    else:
        # Fallback inspection via PIL
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                out_io = io.BytesIO()
                img.convert("RGB").save(out_io, format="JPEG", quality=88)
                file_bytes = out_io.getvalue()
                mime_type = "image/jpeg"
                ext = "jpg"
        except Exception as e:
            raise ValueError(f"UNSUPPORTED_MEDIA_TYPE: Corrupted or unrecognized file signature: {e}")

    # Compute SHA-256 Digest
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    filename = f"receipt_{sha256_hash[:12]}.{ext}"

    return file_bytes, filename, mime_type, sha256_hash
```

---

### 3.3 Worker Decoupled Two-Phase Execution Pipeline

```python
# worker.py Phase 4 Implementation Structure

async def upload_receipts_with_failure_isolation(client, invoice_id: str, ledger_item: dict):
    """
    Uploads attachments to Xero draft bill with failure isolation.
    Guarantees draft bill is never dropped or rolled back on attachment failure.
    """
    media_urls = ledger_item.get("media_urls") or []
    if isinstance(media_urls, str):
        try:
            import json
            media_urls = json.loads(media_urls)
        except Exception:
            media_urls = [media_urls] if media_urls.startswith("http") else []

    if not media_urls:
        await update_ledger_attachment_status(ledger_item["id"], "NO_ATTACHMENT")
        return

    async with httpx.AsyncClient(timeout=30.0) as dl_client:
        for idx, m_url in enumerate(media_urls):
            try:
                # 1. Download raw media
                resp = await dl_client.get(m_url)
                if resp.status_code != 200:
                    raise Exception(f"Failed to download media: HTTP {resp.status_code}")
                
                # 2. Validate, transcode, and compute SHA-256
                clean_bytes, filename, mime, sha256 = validate_and_normalize_receipt(resp.content, m_url)

                # 3. Upload to Xero Accounting API
                upload_res = await client.upload_attachment(
                    invoice_id=invoice_id,
                    filename=filename,
                    file_bytes=clean_bytes,
                    mime_type=mime
                )
                
                # 4. Record successful attachment in DB
                await record_attachment_success(
                    ledger_id=ledger_item["id"],
                    file_name=filename,
                    mime_type=mime,
                    file_size=len(clean_bytes),
                    sha256=sha256,
                    xero_attachment_id=upload_res.get("Attachments", [{}])[0].get("AttachmentID")
                )
                
            except Exception as att_err:
                # Failure Isolation: Log error, record status, DO NOT drop draft bill!
                logger.error("Attachment upload failed", ledger_id=ledger_item["id"], error=str(att_err))
                await record_attachment_failure(
                    ledger_id=ledger_item["id"],
                    error_msg=str(att_err)
                )
                # Annotate Xero draft bill reference with audit alert
                await client.annotate_invoice_audit_warning(
                    invoice_id=invoice_id,
                    warning_tag="[AUDIT ALERT: Receipt attachment failed - re-upload required]"
                )
```

---

### 3.4 Summary Checklist for Phase 4 Acceptance

- [x] **Notice 700/22 Compliance:** Clear documentation of MTD software digital link boundary vs. Regulation 29(2) input tax invoice evidence mandate.
- [x] **6-Year Statutory Retention:** Comprehensive statutory table mapping VATA 1994, TMA 1970 s12B, FA 1998, and CGS 10-year rules.
- [x] **Paper Receipt Destruction Protocol:** Established 4-point rule under Notice 700 §19.7 and CH13100 allowing destruction of original paper receipts once digitized.
- [x] **Evidential Metadata:** SHA-256 hashing, timestamps, supplier VAT numbers, tax points, and mathematical checksum validation.
- [x] **Xero API Compliance:** 10 MB payload ceiling, raw byte stream delivery, and mandatory HEIC-to-JPEG transcoding.
- [x] **Failure Isolation Pattern:** Mathematical separation of draft bill persistence from attachment upload; zero-byte rejection without rolling back financial bills.
- [x] **HMRC Audit Protocol:** Forensic 5-pillar verification process simulating an official HMRC Schedule 36 compliance visit.
