# PHASE 3 SPECIFICATION: ACCOUNTANT TRIAGE & REVIEW GATEWAYS
## UK Chartered Accountant (ICAEW/ACCA) Technical Architecture & Compliance Specification

---

### Executive Summary & Regulatory Grounding
This specification establishes the mandatory accounting logic, statutory compliance rules, and architectural design for **Phase 3: Accountant Triage & Review Gateways** of the *Invisible Accountant* platform.

This document enforces zero tolerance for artificial intelligence hallucination and guarantees full compliance with:
- **Capital Allowances Act 2001 (CAA 2001)**
- **Corporation Tax Act 2009 (CTA 2009)** & **Income Tax (Trading and Other Income) Act 2005 (ITTOIA 2005)**
- **UK GAAP (FRS 102 Section 17 & FRS 105 Section 12)**
- **Value Added Tax Act 1994 (VATA 1994)** & **The VAT Regulations 1995 (SI 1995/2518)**
- **HMRC VAT Notice 700 (The VAT Guide)** & **VAT Notice 700/22 (Making Tax Digital for VAT)**
- **Xero Developer API Standards & UK Standard Chart of Accounts Architecture**

---

## 1. Capital Allowances & Fixed Asset Triage (HMRC CAA 2001 & UK GAAP FRS 102/105)

### 1.1 Statutory Rules vs. Practice Conventions: The De-Minimis Threshold
#### Statutory Position
In UK statutory tax law (**CAA 2001**, **CTA 2009**, and **ITTOIA 2005**), there is **no statutory monetary de-minimis threshold** below which an item of capital expenditure is automatically classified as a deductible revenue expense. 

The statutory distinction between **capital expenditure** and **revenue expenditure** is rooted in binding UK case law:
1. ***British Insulated and Helsby Cables Ltd v Atherton (1925) 10 TC 155***: Expenditure incurred *"with a view to bringing into existence an asset or an advantage for the enduring benefit of a trade"* is capital expenditure.
2. ***Vallambrosa Rubber Co v Farmer (1910) 5 TC 529***: Capital expenditure is made "once and for all", whereas revenue expenditure is recurring day-to-day operational expenditure.
3. ***Odeon Associated Theatres Ltd v Jones (1971) 48 TC 257***: The tax treatment of expenditure follows recognized principles of commercial accounting, unless displaced by statutory rule.

Under **CTA 2009 s46** (for companies) and **ITTOIA 2005 s25** (for unincorporated businesses), the profits of a trade must be calculated in accordance with **UK Generally Accepted Accounting Practice (UK GAAP)**:
- **FRS 102 Section 17.2** and **FRS 105 Section 12.2** define **Property, Plant and Equipment (PPE)** as tangible assets held for use in the supply of goods or services, rental, or administrative purposes, and expected to be used during **more than one accounting period**.
- **Materiality & Accounting Policy**: UK GAAP acknowledges that financial reporting must balance precision with materiality. Commercial entities are permitted—and expected—to establish a documented, board-approved **Capitalisation De-Minimis Threshold** (conventionally **£500** for micro/small businesses, **£1,000** for medium enterprises, and higher for large corporates). Under this policy, purchases of assets that would otherwise meet the definition of PPE, but whose unit acquisition cost falls below the threshold, are expensed immediately to the Profit & Loss (P&L) account as revenue expenses (e.g., minor office equipment, peripherals, stationery).
- **HMRC Acceptance (BIM35300 & CA21230)**: HMRC's *Business Income Manual* explicitly accepts the accounting write-off of minor capital items directly to P&L, provided that:
  - The business consistently applies its stated accounting policy from year to year;
  - The threshold is realistic relative to the scale of the business; and
  - The practice presents a "true and fair view" without distorting taxable trading profits.

---

### 1.2 Xero UK Standard Chart of Accounts: Fixed Asset Nominal Structure
Xero UK’s baseline Chart of Accounts dedicates the **`700–799` nominal range** to Fixed Assets. Every capital asset account is paired with a corresponding Accumulated Depreciation contra-asset account:

| Account Code | Account Name | Account Type | Default Tax Code | Paired Depreciation Account | Depreciation Code Name |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **710** | **Office Equipment** | `FIXED` | `INPUT` (20% VAT on Expenses) | **711** | Less Accumulated Depreciation on Office Equipment |
| **720** | **Computer Equipment** | `FIXED` | `INPUT` (20% VAT on Expenses) | **721** | Less Accumulated Depreciation on Computer Equipment |
| **760** | **Motor Vehicles** | `FIXED` | `INPUT` (or `NONE` for cars) | **761** | Less Accumulated Depreciation on Motor Vehicles |
| **764** | **Plant & Machinery** | `FIXED` | `INPUT` (20% VAT on Expenses) | **765** | Less Accumulated Depreciation on Plant and Machinery |
| **770** | **Intangibles** | `FIXED` | `NONE` (No VAT) | **771** | Less Accumulated Amortisation on Intangibles |

*Note on custom codes*: While codes `710`, `720`, `760`, and `764` are native Xero defaults, firms frequently configure **`730`** or **`740`** as **Fixtures & Fittings** (paired with `731`/`741`). 
In contrast, operating expense accounts reside in the **`400–499` range** (e.g., `420` Printing & Stationery, `429` General Expenses, `489` Repairs & Maintenance).

---

### 1.3 Why an AI System Must NEVER Automatically Post a £1,200 MacBook to Account 420 or 429
Routing a £1,200 laptop directly to **Account 420 (Printing & Stationery)** or **Account 429 (General Expenses)** constitutes professional negligence and tax non-compliance:

```
                                  £1,200 MacBook Purchase
                                             │
             ┌───────────────────────────────┴───────────────────────────────┐
             ▼                                                               ▼
   [CORRECT TRIAGE GATEWAY]                                        [NAIVE AUTO-POSTING BUG]
Posted to Account 720 (Fixed Asset)                               Posted to Account 420 (P&L Expense)
             │                                                               │
    Balance Sheet Capitalisation                                     Immediate P&L Write-Off
             │                                                               │
   Depreciation Added Back                                          No Depreciation to Add Back
             │                                                               │
Statutory Claim: AIA / Full Expensing                              Illegal Revenue Deduction:
(CAA 2001 s38A / s45S)                                             CTA 2009 s53 / ITTOIA 2005 s33 Breach
             │                                                               │
100% Tax Relief Fully Legitimised                                  HMRC Discovery Enquiry (TMA 1970 s9A / FA 1998)
             │                                                               │
  Audited Asset Register Active                                    • Disallowance from Allowable Expenses
                                                                   • Double Loss: Capital Allowance Time-Barred
                                                                   • Penalties under FA 2007 Sch 24 (15%-70%)
```

#### Detailed Legal and Tax Implications
1. **Breach of UK GAAP & Companies Act 2006 (s393/s396)**:
   A £1,200 MacBook has an enduring useful economic life of 3 to 5 years and clearly exceeds standard small-business de-minimis thresholds (£500). Expensing it directly into the P&L falsifies the operating results and balance sheet, failing to present a true and fair view.
2. **Statutory Prohibition of Capital Deductions (CTA 2009 s53 / ITTOIA 2005 s33)**:
   UK statute explicitly disallows capital expenditure as a deduction in computing trading profits. Account 420/429 feeds directly into the taxable trading profit calculation. Taking a revenue deduction for a capital asset is illegal.
3. **Sole Trader Tax Return Distortions (HMRC Self-Assessment SA100 / SA103)**:
   - On **SA103S** (Short Pages), revenue expenses are declared in **Box 11** (*Phone, fax, stationery and other office costs*). Wrongly including the £1,200 reduces **Box 21 (Net Profit)** or inflates **Box 22 (Net Loss)**.
   - On **SA103F** (Full Pages), it inflates **Box 17** (*Admin costs*).
   - In an HMRC compliance check under **Taxes Management Act 1970 (TMA 1970) s9A**, HMRC will disallow the £1,200 from Box 11/17, raising an assessment for unpaid Income Tax and Class 4 NIC plus statutory interest under **TMA 1970 s86**.
4. **Permanent Forfeiture of Capital Allowances (AIA / Full Expensing Time-Bar)**:
   - Capital Allowances are **statutory reliefs that must be formally claimed**, not automatic deductions.
   - Under **CAA 2001 s38A (Annual Investment Allowance - AIA)** or **CAA 2001 s45S (Full Expensing 100% First-Year Allowance for companies)**, qualifying plant and machinery can receive 100% tax relief in Year 1.
   - However, claims are subject to strict statutory time limits: **12 months from the statutory filing deadline** under **Finance Act 1998 Schedule 18 Paragraph 57** (for Corporation Tax) and **TMA 1970 s42** (for Income Tax).
   - If HMRC opens an enquiry after the amendment window has closed, the £1,200 revenue deduction is disallowed, and the taxpayer is **time-barred from substituting a late Capital Allowance claim**. The taxpayer loses tax relief on the asset entirely.
5. **Inaccuracy Penalties (Finance Act 2007 Schedule 24)**:
   Mischaracterising capital items as revenue costs constitutes an inaccuracy in a tax return. HMRC assesses penalties:
   - **Careless action**: 15% to 30% of the potential lost revenue.
   - **Deliberate inaccuracy**: 30% to 70%.
6. **Destruction of the Fixed Asset Register & Disposal Tracking**:
   When a company sells or disposes of the MacBook in the future, **CAA 2001 s61** requires a **Balancing Charge** or disposal value adjustment. If the asset was buried in Account 420, it is absent from the Fixed Asset Register, causing balancing charges to be overlooked on disposal.

---

### 1.4 Exact Choices Presented to the Accountant in the Triage Gateway
When an expense exceeds the de-minimis threshold (e.g., > £500.00) or contains keywords signifying tangible equipment (laptop, MacBook, server, machinery, furniture), the gateway must halt automated processing and present four structured options:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [GATEWAY 1] CAPITAL ASSET & DE-MINIMIS REVIEW                                                  │
│ Receipt: Apple Store (£1,200.00 Gross, £200.00 VAT)                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ ] OPTION A: CAPITALISE AS FIXED ASSET (Recommended per FRS 102 / CAA 2001)                    │
│     Asset Nominal Code: [ 720 - Computer Equipment                       ▼ ]                    │
│     Tax Allowance Claim: [ 100% AIA / Full Expensing (CAA 2001 s38A/s45S) ▼ ]                   │
│     [x] Register as Draft Asset in Xero Fixed Asset Register                                    │
│                                                                                                 │
│ [ ] OPTION B: WRITE-OFF TO REVENUE EXPENSE (Requires Justification Reason)                      │
│     Nominal Code:       [ 420 - Printing & Stationery                    ▼ ]                    │
│     Statutory Reason:   [ De-minimis policy applied (per company manual) ▼ ]                    │
│                           - De-minimis policy applied (per company manual)                      │
│                           - Short useful economic life (< 12 months)                            │
│                           - Software license / SaaS consumable, not hardware                    │
│                           - Repairs and maintenance of existing asset (BIM35450)                │
│                                                                                                 │
│ [ ] OPTION C: COMPOSITE / MULTI-LINE SPLIT                                                      │
│     Line 1: [ £1,150.00 Net ] -> [ 720 Computer Equipment ] (Hardware Asset)                    │
│     Line 2: [    £50.00 Net ] -> [ 420 Stationery         ] (Dongles & Paper Consumables)       │
│                                                                                                 │
│ [ ] OPTION D: PRIVATE USE / DUALITY APPORTIONMENT (ITTOIA 2005 s34)                             │
│     Business Use Proportion: [ 80 ] %                                                           │
│     Allowable Business Cost: £960.00 -> Account 720 (Eligible for Capital Allowances)           │
│     Private Portion:         £240.00 -> Account 830 (Director's Loan / Drawings)                │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Currency Receipt Handling (VATA 1994 s88, VAT Notice 700 §7.6/§17, HMRC Guidance)

### 2.1 Cross-Border Transactions: UK Business Practices
UK businesses routinely incur foreign currency expenses falling into two distinct tax classes:

#### Class 1: Cross-Border B2B Digital Services (e.g., AWS, Google Workspace, Zoom, Figma in USD/EUR)
- **Place of Supply**: Under **VATA 1994 s7A** and the General B2B Rule, the place of supply of services supplied by an overseas supplier to a UK business customer is the **United Kingdom**.
- **Reverse Charge Mechanism**: Under **VATA 1994 s8**, the recipient business must self-account for VAT as if they were the supplier:
  - Output VAT is declared in **Box 1** (20% of net converted to GBP).
  - Input VAT is simultaneously reclaimed in **Box 4** (subject to ordinary input tax recovery rules).
  - The net GBP value is recorded in **Box 6** (Total value of sales) and **Box 7** (Total value of purchases).
- **Xero Implementation**: Requires the native Xero tax rate code **`Reverse Charge Expenses (20%)`**.

#### Class 2: Overseas Travel, Accommodation, and Meals (e.g., Hotel in Paris in EUR, Taxi in New York in USD)
- **Place of Supply**: Under **VATA 1994 Schedule 4A**, services relating to land/hotels and passenger transport are supplied where physically performed (outside the UK).
- **Scope of UK VAT**: These supplies are entirely **outside the scope of UK VAT**. Local foreign sales taxes (e.g., US state tax, French TVA, German MwSt) are not UK taxes.

---

### 2.2 Input VAT Reclaim Prohibition on Foreign Transactions
#### Statutory Rule
Under **VATA 1994 s24(1)**, **Input Tax** is strictly defined as VAT charged on the supply of goods or services by a person who is a **taxable person in the United Kingdom**.

1. An overseas supplier with no UK VAT registration cannot charge UK VAT.
2. Foreign sales taxes, US state taxes, or overseas VAT (TVA/IVA/MwSt) are **NOT UK VAT**.
3. Under no circumstances may foreign VAT or sales tax be entered into **Box 4 (VAT reclaimed)** of a UK VAT Return.
4. Claiming foreign taxes in Box 4 constitutes an unlawful claim, subject to assessment, interest, and penalties under **Schedule 24 Finance Act 2007**.
5. Overseas VAT on foreign travel cannot be recovered through HMRC; it must either be reclaimed via the **13th VAT Directive** refund procedure (for non-EU claimants) or expensed in full as part of the gross cost in P&L.

#### Mandatory Tax Type in Xero
- For overseas expenses (non-reverse charge), the tax rate must be **`NONE`** (*No VAT / 0% on Expenses*).
- Box 4 impact is exactly **£0.00**.
- The full gross converted amount (including any foreign local taxes) is charged to the relevant P&L expense nominal.

---

### 2.3 Xero API Failure Mechanics: Foreign Currency on Standard UK Plans
When integrating with the Xero API (`POST /api.xro/2.0/Invoices`):
1. **Plan Restrictions**: Standard Xero UK subscriptions (Starter and Standard plans) **do not include Multi-Currency**. Multi-Currency is restricted to Premium / Ultimate tiers.
2. **API Response**: If a bill payload specifies `CurrencyCode: "USD"` for a tenant without multi-currency, the Xero API returns **HTTP 400 Bad Request** with validation error:
   ```json
   {
     "ErrorNumber": 10,
     "Type": "ValidationException",
     "Message": "A validation exception occurred",
     "Elements": [
       {
         "ValidationErrors": [
           {
             "Message": "The currency rate cannot be set on an organisation without multi-currency enabled."
           }
         ]
       }
     ]
   }
   ```
3. **Currency Activation Prerequisite**: Even on multi-currency plans, if the currency code (e.g., `USD`) has not been activated via the Xero UI or `PUT /Currencies`, the API rejects the bill with: `"The CurrencyCode [USD] is not valid for this organisation."`
4. **Pipeline Impact**: Attempting to post raw foreign currency bills without pre-conversion crashes automated workflows, causing fatal webhook failures or dead-letter queue stalls.

---

### 2.4 Commercial Platform Pre-Accounting Architecture (Dext & AutoEntry)
Leading pre-accounting engines (Dext, AutoEntry) resolve this using a **Base Currency Conversion Engine**:

```
[Foreign Currency Receipt (e.g. AWS $120.00 USD)]
                       │
                       ▼
           [Tenant Capability Check]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[Multi-Currency Active & Toggled]   [Standard Plan / Multi-Currency Disabled]
• Posts in original Currency (USD)  • Base Currency Auto-Conversion (GBP)
• Populates CurrencyRate (or XE)    • Fetches Official Rate on Receipt Date
• Xero balances FX revaluations     • Converts Line Items into GBP Net/Gross
                                    • Tags with Tax Rate: REVERSE CHARGE or NONE
                                    • Embeds Foreign Currency Audit Trail in Reference
                                    • Publishes Bill cleanly in GBP!
```

#### Conversion Rate Standards (HMRC VAT Notice 700 §7.6)
Under **VAT Notice 700 Section 7.6** (which has the force of law under **VATA 1994 Schedule 6 Paragraph 11**), currency conversions for VAT purposes must use one of two permitted methods:
1. **The UK Market Selling Rate**: The spot exchange rate on the date of supply (invoice date), sourced from recognized financial feeds (Fixer.io, XE.com, European Central Bank).
2. **HMRC Period Rates of Exchange**: The official monthly exchange rates published by HMRC for customs and VAT.

#### Digital Audit Embedding
When publishing in base currency (GBP), platforms must preserve the complete transaction trail within Xero:
- **`Reference` field**: `"USD 120.00 @ 1.2500 (HMRC Monthly Rate)"`
- **`LineItem.Description`**: `"AWS Cloud Infrastructure (USD $120.00 @ FX 1.2500 = £96.00 GBP)"`
- **Attachment**: The original foreign invoice is attached directly via `PUT /Invoices/{InvoiceID}/Attachments`.

---

## 3. Accountant Triage Gateway & Review Controls

### 3.1 Mandatory State Machine Lifecycle
To prevent erroneous, unvetted, or duplicate records from reaching Xero, receipts must follow an auditable **Finite State Machine (FSM)**:

```
                      ┌───────────────┐
                      │   INGESTED    │
                      └───────┬───────┘
                              │ (OCR / AI Extraction)
                              ▼
                      ┌───────────────┐
                      │   EXTRACTED   │
                      └───────┬───────┘
                              │
             ┌────────────────┼────────────────┬────────────────┐
             ▼                ▼                ▼                ▼
     [Math Error]      [90-Day Match]     [Item > £500 /    [Confidence < 85% /
     VALIDATION_FAILED  DUPLICATE_SUSPECTED Asset Keywords]  Foreign FX / Sensitive]
             │                │           CAPITAL_ALLOWANCE   NEEDS_REVIEW
             │                │                │                │
             └────────────────┼────────────────┼────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   ACCOUNTANT_TRIAGED  │  (Human overrides/confirms)
                  └───────────┬───────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
        [Confirmed]                       [Rejected]
         APPROVED                          REJECTED (Archived)
             │
             ▼
       POSTING_DRAFT  (Locked, Two-Phase Idempotency)
             │
             ▼
     POSTED_XERO_DRAFT (Created in Xero + Attachments Uploaded)
```

#### Detailed State Definitions
1. **`INGESTED`**: Raw receipt/image uploaded via WhatsApp or web; stored in encrypted vault; awaiting AI extraction.
2. **`EXTRACTED`**: AI has parsed fields (vendor, date, net, VAT, gross, line items); JSON schema validated.
3. **`VALIDATION_FAILED`**: Mathematical mismatch (`|Net + VAT - Gross| > £0.01`), missing tax point date, or unreadable document. Halted.
4. **`DUPLICATE_SUSPECTED`**: Deterministic SHA-256 fingerprint matches an existing ledger record within the rolling 90-day window. Halted to prevent duplicate tax claims.
5. **`CAPITAL_ALLOWANCE`**: Expense exceeds de-minimis threshold (£500) or represents plant/equipment. Requires explicit classification by an accountant.
6. **`NEEDS_REVIEW`**: Extraction confidence < 85%, foreign currency detected, missing supplier VAT number, or sensitive category (entertaining, fines).
7. **`ACCOUNTANT_TRIAGED`**: Accountant has inspected the record, adjusted nominal codes/VAT rates, and selected tax treatment.
8. **`APPROVED`**: Ready for transmission to Xero (either by accountant approval or by passing straight-through processing gates: domestic GBP, non-capital, unambiguous vendor, confidence > 95%).
9. **`POSTING_DRAFT`**: Worker thread acquires lock; two-phase idempotency key generated; payload being transmitted to Xero API.
10. **`POSTED_XERO_DRAFT`**: Draft bill successfully created in Xero; external `InvoiceID` stored in database; digital image attached; status finalized.
11. **`REJECTED`**: Explicitly marked invalid by accountant (spam, personal receipt, confirmed duplicate). Excluded from Xero.
12. **`FAILED_RETRYABLE`**: Transient failure (Xero rate limit 429, 502/503 network drop, expired token). Managed via exponential backoff.
13. **`FAILED_FATAL`**: Permanent API error (invalid tenant account code, corrupted document). Halted for administrative intervention.

---

### 3.2 Triage Dashboard: Required Override Controls
Before releasing a draft bill to Xero, the triage dashboard must provide inline editing for the following fields:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ EDIT TRANSACTION #1042                                                     Status: NEEDS_REVIEW │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Vendor / Contact:     [ Amazon Business UK                       ] [x] Match Existing Contact   │
│ Tax Point Date:       [ 2026-10-12 ]           Due Date:           [ 2026-11-11 ]               │
│ Invoice / Ref No:     [ INV-GB-2026-981245                       ]                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ FINANCIAL TOTALS (Auto-balancing recalculation engine active)                                   │
│ Net Amount:           [ £1,000.00 ]                                                             │
│ VAT Amount:           [   £200.00 ]   (Set to 0 if supplier invoice lacks valid UK VAT No.)     │
│ Gross Amount:         [ £1,200.00 ]   [✓ Math Balanced: Net + VAT == Gross]                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CODING & TAX CLASSIFICATION                                                                     │
│ Account Classification: (o) Fixed Asset (Capital)   ( ) Revenue Expense (P&L)                   │
│ Nominal Account:      [ 720 - Computer Equipment (Fixed Asset)                               ▼ ]│
│ Tax Rate (VAT Type):  [ INPUT - 20% (VAT on Expenses)                                        ▼ ]│
│ Multi-Currency:       [ Converted to GBP @ 1.2500 (Original: USD $1,500.00)                 ▼ ]│
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ AUDIT & COMPLIANCE (Mandatory for overrides)                                                    │
│ Override Justification: [ Capitalising enterprise development workstation per FRS 102 s17     ]│
│ Accountant Reviewer:    [ lead.accountant@firm.co.uk                                           ]│
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ Reject Transaction ]                            [ Save & Approve -> Release to Xero Draft ]   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Auditability & Compliance under VAT Notice 700/22 (MTD Digital Links)
Under **HMRC VAT Notice 700/22 (Making Tax Digital for VAT)**, strict legal rules govern digital links and manual interventions:

#### 1. Digital Link Definition & Integrity
- A **digital link** is an electronic transfer of data between functional compatible software programs without manual copying, pasting, or re-keying (**Notice 700/22 Section 7**).
- Automated API transmission between the *Invisible Accountant* platform and Xero constitutes a certified digital link.

#### 2. Manual Adjustments & Triage Permissibility
- **Notice 700/22 Section 4.4 and Section 7.4** explicitly permit professional adjustments, classification corrections, and tax rate overrides prior to finalizing the VAT return.
- However, manual overrides **must not break the digital audit chain**. The software must maintain complete traceability between the raw input and the final submitted ledger entry.

#### 3. Mandatory Audit Trail Architecture (`audit_trail` Table)
Any modification made by an accountant in the triage dashboard must be recorded in an immutable, append-only database table:

```sql
CREATE TABLE triage_audit_trail (
    id BIGSERIAL PRIMARY KEY,
    ledger_id BIGINT REFERENCES hmrc_ledger(id) ON DELETE CASCADE,
    accountant_id VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL, -- 'FIELD_OVERRIDE', 'STATUS_CHANGE', 'SPLIT_TRANSACTION'
    field_name VARCHAR(64) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    justification_reason TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_audit_ledger ON triage_audit_trail(ledger_id);
```

#### 4. Source Document Digital Linkage in Xero
To guarantee compliance with **Notice 700/22 Section 3 (Retention of Digital Invoices)**, every draft bill pushed to Xero must have the original receipt/invoice image uploaded directly as an attachment (`PUT /Invoices/{InvoiceID}/Attachments/{FileName}`). This ensures that HMRC auditors inspecting Xero can click directly from Box 4 on the VAT Return down into the transaction and view the original supplier tax invoice.

---

## 4. Phase 3 Architecture & Implementation Roadmap

```
                                  PHASE 3 ARCHITECTURE
                                  
 ┌───────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
 │ Ingestion & AI Parser │ ──────> │  Triage State Machine  │ ──────> │   Accountant Gateway   │
 │ • OCR Line Extraction │         │  • Capital Review Flag │         │   • Inline Overrides   │
 │ • Currency Detection  │         │  • Duplicate Detection │         │   • FRS 102 Validation │
 │ • VAT Registration No │         │  • Foreign FX Engine   │         │   • Audit Logging      │
 └───────────────────────┘         └────────────────────────┘         └───────────┬────────────┘
                                                                                  │ (Approved)
                                                                                  ▼
 ┌───────────────────────┐         ┌────────────────────────┐         ┌────────────────────────┐
 │ Xero Fixed Asset Reg  │ <────── │   Xero Draft Creator   │ <────── │  Two-Phase Idempotency │
 │ • Draft Asset Created │         │   • Account 720 / 420  │         │  • Locking Mechanism   │
 │ • Serial / Tag Stored │         │   • Attach Source PDF  │         │  • external_bill_id    │
 └───────────────────────┘         └────────────────────────┘         └────────────────────────┘
```

### Key Milestones for Implementation
1. **Database Schema Enhancements**: Add `triage_audit_trail` table and expand `hmrc_ledger` status enum to support `CAPITAL_ALLOWANCE`, `NEEDS_REVIEW`, `ACCOUNTANT_TRIAGED`, and `REJECTED`.
2. **Multi-Currency Normalizer**: Integrate daily/monthly exchange rate engine; auto-convert non-base currencies to GBP for single-currency tenants; populate compliant Reference fields.
3. **Gateway UI Expansion**: Transform `/dashboard` into a full triage gateway with interactive dropdowns for Xero Chart of Accounts, VAT rates, and capitalisation toggles.
4. **Audit Trail Enforcer**: Reject any triage modification that lacks an accountant identifier and justification reason.
5. **Fixed Asset Integration**: Leverage Xero's Assets API to automatically draft fixed asset entries when accounts `710`, `720`, `760`, or `764` are approved.

---
*Authored by: UK Chartered Accountant Lead (ICAEW/ACCA)*  
*Invisible Accountant Implementation Team*  
*Document Version: 3.0 (Definitive)*
