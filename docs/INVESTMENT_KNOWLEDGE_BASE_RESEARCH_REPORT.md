# Investment Knowledge Base — Research & Verification Report
**Indian Banking Products & Real Estate Valuation (Uttarakhand & Delhi NCT)**

**Version:** 1.0.0  
**Research Cut-Off Date:** 15 November 2026  
**Project:** Indian Multi-Asset Portfolio Management Platform  
**Deliverables Covered:** Deliverable A (Comprehensive Research Report), Deliverable B (Cross-Reference to Structured Tables), Deliverable C (Limitations & Verification Matrix)

---

## 1. Executive Summary

This research report provides verified technical reference data, calculation parameters, and database schemas for an Indian multi-asset portfolio management platform.

### Scope & Highlights:
1. **12 Indian Banks Investigated:**
   - **Public Sector Banks:** State Bank of India (SBI), Punjab National Bank (PNB), Bank of Baroda (BoB), Bank of India (BoI), Canara Bank, Union Bank of India.
   - **Private Sector Banks:** HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra Bank, IDFC FIRST Bank.
   - **Small Finance Banks:** AU Small Finance Bank.
   - **Core Findings on Savings Accounts:** Most large PSU and private banks have shifted to a baseline flat rate of **2.50% to 2.75% p.a.** on retail savings balances, credited quarterly. High-yield progressive/incremental slab rates are offered primarily by newer private and small finance banks (**IDFC FIRST Bank: up to 7.00% p.a.; AU Small Finance Bank: up to 6.75% p.a.**), credited monthly.
   - **Core Findings on Auto-Sweep Deposits:** Auto-sweep facilities (e.g., SBI MODS, HDFC Super Saver, ICICI Money Multiplier, Axis Encash 24, Kotak ActivMoney) transfer balances above a defined threshold into high-yield fixed deposits while retaining liquidity. Liquidation on reverse sweep operates strictly on a **LIFO (Last-In, First-Out)** order in ₹1,000 or ₹5,000 increments, preserving intact FD units at their contracted rate.
2. **Uttarakhand Real Estate Valuation:**
   - Governing body: Department of Stamps and Registration (`registration.uk.gov.in`).
   - Covered key urban hubs: Dehradun, Haridwar, Rishikesh, Haldwani, Nainital, Rudrapur, Kashipur.
   - Stamp Duty: **5.00% for male buyers**; **3.75% for female buyers** (concession up to ₹25 lakh valuation); Joint ownership ~4.375%.
   - Registration Fee: **2.00% of property valuation**, strictly **capped at a maximum of ₹25,000**.
3. **Delhi (NCT) Real Estate Valuation:**
   - Governing body: Revenue Department & DORIS (`doris.delhigovt.nic.in`).
   - Standardized 8-tier locality categorization (**Categories A through H**).
   - Residential land circle rates range from **₹7,74,000/sq. m (Category A)** down to **₹23,280/sq. m (Category H)**.
   - Cost of construction ranges from **₹21,960/sq. m (Category A)** down to **₹3,480/sq. m (Category H)**, modulated by a mandatory age depreciation factor (1.0 for post-2000 down to 0.5 for pre-1960).
   - Stamp Duty: **6.00% for male buyers**, **4.00% for female buyers**, **5.00% for joint buyers**, plus a uniform **1.00% registration fee** (no cap).

---

## 2. Indian Banking Research (12 Banks Detailed)

### 2.1 Savings Account Interest Rate Comparison

| Bank | Current Retail Rate (% p.a.) | Balance Slabs | Calculation Method | Credit Frequency | Special Slabs / Notes | Effective Date | Source URL |
|---|---|---|---|---|---|---|---|
| **State Bank of India (SBI)** | 2.50% | Flat across all domestic retail tiers | Daily closing product | Quarterly (Feb, May, Aug, Nov) | Uniform flat rate for all retail balances | 2026-06-01 | [sbi.co.in](https://sbi.co.in) |
| **Punjab National Bank (PNB)** | 2.70% | Up to ₹10 Cr: 2.70%<br>> ₹10 Cr: 3.00% | Daily closing balance | Quarterly | High-value corporate scales to 3.50% | 2026-07-01 | [pnbindia.in](https://pnbindia.in) |
| **Bank of Baroda (BoB)** | 2.50% | Up to ₹50 Cr: 2.50%<br>₹50 Cr–₹100 Cr: 2.75% | Daily product balance | Quarterly | Institutional scales up to 4.75% | 2026-07-15 | [bankofbaroda.in](https://bankofbaroda.in) |
| **Bank of India (BoI)** | 2.50% | Up to ₹50 Cr: 2.50%<br>₹50 Cr–₹250 Cr: 2.60% | Daily balance | Quarterly | Scales up to 4.85% for ₹2,500 Cr+ | 2026-06-01 | [bankofindia.co.in](https://bankofindia.co.in) |
| **Canara Bank** | 2.55% | Up to ₹100 Cr: 2.55%<br>₹100 Cr–₹300 Cr: 2.65% | Daily product | Quarterly | Scales up to 4.00% for ₹2,000 Cr+ | 2026-06-12 | [canarabank.com](https://canarabank.com) |
| **Union Bank of India** | 2.75% | Up to ₹50 Lakh: 2.75%<br>₹50 Lakh–₹100 Cr: 2.90% | Daily balance | Quarterly | Scales up to 4.20% for ₹2,000 Cr+ | 2026-07-01 | [unionbankofindia.co.in](https://unionbankofindia.co.in) |
| **HDFC Bank** | 2.50% | Flat across retail domestic tiers | Daily closing balance | Quarterly | Flat rate across all regular resident accounts | 2026-06-20 | [hdfcbank.com](https://hdfcbank.com) |
| **ICICI Bank** | 2.50% | Flat across all retail domestic tiers | Daily closing balance | Quarterly | Flat rate across all resident tiers | 2026-06-15 | [icicibank.com](https://icicibank.com) |
| **Axis Bank** | 2.50% | Up to ₹2,000 Cr: 2.50%<br>₹2,000 Cr+: MIBOR + 1.01% | Daily closing balance | Quarterly | Overnight MIBOR linked on incremental > ₹1L for large corporate | 2026-06-15 | [axisbank.com](https://axisbank.com) |
| **Kotak Mahindra Bank** | 2.50% | Flat across all domestic retail tiers | Daily balance | Quarterly | ActivMoney provides term deposit yield on surplus | 2026-05-15 | [kotak.com](https://kotak.com) |
| **IDFC FIRST Bank** | 2.50% to 7.00% | **0–₹3L:** 2.50%<br>**₹3L–₹25L:** 7.00%<br>**₹25L+:** 6.00% | **Progressive / Incremental** on daily closing balance | **Monthly** | Incremental calculation: ₹10L balance earns 2.5% on first ₹3L, 7.0% on next ₹7L | 2026-10-04 | [idfcfirstbank.com](https://idfcfirstbank.com) |
| **AU Small Finance Bank** | 2.50% to 6.75% | **< ₹1L:** 2.50%<br>**₹1L–<₹3L:** 2.50%<br>**₹3L–<₹5L:** 2.75%<br>**₹5L–<₹10L:** 3.50%<br>**₹10L–<₹25Cr:** 6.50% | **Progressive / Incremental** on daily closing balance | **Monthly** | Top slab 7.00% flat on ₹100Cr–₹750Cr | 2026-10-01 | [aubank.in](https://aubank.in) |

---

### 2.2 Fixed Deposit (FD) Retail Interest Rates (< ₹3 Crore)

Comparable tenures across all 12 institutions for general citizens (General) and senior citizens (Senior):

| Bank | 1 Year (Gen / Sen) | 2 Years (Gen / Sen) | 3 Years (Gen / Sen) | 5 Years (Gen / Sen) | 5-Yr Tax Saver (Gen / Sen) | Premature Penalty | Callable vs Non-Callable |
|---|---|---|---|---|---|---|
| **SBI** | 6.25% / 6.75% | 6.40% / 6.90% | 6.30% / 6.80% | 6.05% / 7.05%* | 6.05% / 7.05%* | 0.50% (< ₹5L), 1.00% (≥ ₹5L) | Non-callable available on > ₹1 Cr |
| **PNB** | 6.25% / 6.75% | 6.30% / 6.80% | 6.30% / 6.80% | 6.35% / 6.85% | 6.10% / 6.60% | 1.00% | Non-callable available on > ₹1 Cr |
| **Bank of Baroda** | 6.25% / 6.75% | 6.25% / 6.75% | 6.25% / 6.75% | 6.50% / 7.15% | 6.30% / 6.90% | 1.00% | Baroda Advantage (Non-callable > ₹1 Cr) |
| **Bank of India** | 6.25% / 6.75% | 6.25% / 6.75% | 6.25% / 6.75% | 6.50% / 7.00% | 6.30% / 6.80% | 1.00% | Star Fixed Deposit non-callable option |
| **Canara Bank** | 6.25% / 6.75% | 6.25% / 6.75% | 6.30% / 6.80% | 6.50% / 7.00% | 6.30% / 6.80% | 1.00% | Non-callable available on bulk deposits |
| **Union Bank of India** | 6.25% / 6.75% | 6.30% / 6.80% | 6.30% / 6.80% | 6.40% / 6.90% | 6.30% / 6.80% | 1.00% | Union Non-Callable on > ₹1 Cr |
| **HDFC Bank** | 6.25% / 6.75% | 6.25% / 6.75% | 6.35% / 6.85% | 6.15% / 6.65% | 6.60% / 7.10% | 1.00% | Non-callable (No premature exit) > ₹2 Cr |
| **ICICI Bank** | 6.25% / 6.75% | 6.55% / 7.05% | 6.60% / 7.20% | 6.60% / 7.10% | 6.60% / 7.20% | 1.00% | "FD Xtra" / Non-callable > ₹1 Cr |
| **Axis Bank** | 6.25% / 6.75% | 6.55% / 7.05% | 6.45% / 6.95% | 6.25% / 6.75% | 6.45% / 7.05% | 1.00% | Fixed Deposit Plus (Non-callable > ₹1 Cr) |
| **Kotak Mahindra Bank** | 6.25% / 6.75% | 6.60% / 7.10% | 6.50% / 7.00% | 6.20% / 6.70% | 6.20% / 6.70% | 1.00% | Non-callable option available > ₹2 Cr |
| **IDFC FIRST Bank** | 6.50% / 7.00% | 6.75% / 7.25% | 6.60% / 7.10% | 6.35% / 6.85% | 6.50% / 7.00% | 1.00% | Non-callable available on deposits > ₹2 Cr |
| **AU Small Finance Bank** | 6.75% / 7.25% | 7.00% / 7.50% | 6.80% / 7.30% | 6.50% / 7.00% | 6.75% / 7.25% | 1.00% | Non-callable available on institutional tiers |

*\*Note: SBI WeCare scheme provides 1.00% additional yield to senior citizens on 5-10 year deposits (total 7.05%). Tax Saver FDs across all banks have a statutory 5-year lock-in with zero premature withdrawal permitted under Section 80C.*

---

### 2.3 Auto-Sweep / Sweep-In / Sweep-Out Mechanisms

| Bank | Facility Name | Sweep-Out Threshold | Retained Savings Balance | Sweep-Out Block | Sweep-In (Reverse) Increment | Break Order | Interest Treatment on Broken Units | Exclusions / Rules |
|---|---|---|---|---|---|---|---|---|
| **SBI** | Savings Plus / MODS | ₹50,000 | ₹35,000 | ₹10,000 (mult. of ₹1,000) | ₹1,000 | LIFO (default) | Earns FD rate for actual tenure held; penalty only on broken unit | Minimum MOD tenure 1 yr; maximum 5 yrs |
| **PNB** | PNB Pratham / Auto Sweep | ₹50,000 | ₹25,000 | ₹10,000 (mult. of ₹5,000) | ₹1,000 | LIFO | Contracted card rate for actual holding period | Cannot link tax-saver FDs |
| **Bank of Baroda** | Baroda Suvidha | ₹50,000 | ₹25,000 | ₹10,000 (mult. of ₹5,000) | ₹1,000 | LIFO | Pro-rata interest minus premature penalty | Linked FD tenure typically 12 months |
| **Bank of India** | Star Flexi Savings | ₹50,000 | ₹25,000 | ₹10,000 (mult. of ₹5,000) | ₹1,000 | LIFO | Applicable rate for run period | Standard domestic FDs only |
| **Canara Bank** | Kamadhenu Auto-Sweep | ₹50,000 | ₹25,000 | ₹10,000 (mult. of ₹5,000) | ₹1,000 | LIFO | Applicable term deposit rate | Non-callable excluded |
| **Union Bank of India** | Union Flexi Deposit | ₹50,000 | ₹25,000 | ₹10,000 (mult. of ₹5,000) | ₹1,000 | LIFO | Pro-rata tenure interest | Standard retail accounts only |
| **HDFC Bank** | Super Saver / Sweep-in | ₹100,000 | ₹25,000 | ₹25,000 (mult. of ₹5,000) | ₹1,000 | LIFO | No interest if broken within 7 days; card rate minus penalty thereafter | Excludes 5-year tax saver & non-callable FDs |
| **ICICI Bank** | Money Multiplier | ₹15,000 | ₹10,000 (Special: ₹30,000) | ₹5,000 | ₹5,000 | LIFO | Applicable rate for exact tenure held; unbroken units untouched | Auto-renews principal + interest on maturity |
| **Axis Bank** | Encash 24 / Auto FD | Configurable (typ. ₹25,000) | Account MAB (₹10,000) | ₹5,000 | ₹5,000 | LIFO | Applicable rate for tenure held on broken tranche | Auto FD tenures from 6 months to 5 years |
| **Kotak Mahindra Bank** | ActivMoney | ₹50,000 (Ace: ₹50,000) | ₹25,000 (Ace: ₹50,000) | ₹25,000 (mult. of ₹5,000) | ₹5,000 | LIFO | Regular FD rate for 180 days default; no penalty on intact units | Cannot coexist with manual one-way sweep-in |
| **IDFC FIRST Bank** | Booster Deposit | ₹50,000 | ₹25,000 | ₹10,000 | ₹1,000 | LIFO | Standard term deposit card rate | Progressive savings already provides high yield |
| **AU Small Finance Bank** | AU Sweep-In Facility | ₹50,000 | ₹25,000 | ₹10,000 | ₹1,000 | LIFO | Applicable card rate for actual period | Auto-renewal upon maturity |

---

## 3. Uttarakhand Real Estate Research

### 3.1 Stamp Duty & Registration Charges

The regulatory framework is administered by the **Department of Stamps and Registration, Government of Uttarakhand** (`registration.uk.gov.in`):

1. **Stamp Duty Rates:**
   - **Male Buyer:** **5.00%** of the higher of registered sale consideration or circle rate valuation.
   - **Female Buyer (Concession):** **3.75%** (a 1.25% concession). This concession is legally capped up to a property valuation of **₹25 Lakh**. For valuations exceeding ₹25 Lakh, standard rates apply on the incremental portion in accordance with state notifications.
   - **Joint Ownership (Male + Female):** **4.375%** blended rate (or 5.00% if primary applicant is male).
   - **Joint Ownership (Female + Female):** **3.75%**.
2. **Registration Fee:**
   - **2.00%** of the property valuation.
   - **Statutory Maximum Cap:** Fixed at **₹25,000**. On any property valued above ₹12,50,000, the fee remains exactly ₹25,000, drastically minimizing registration transaction friction for mid- and high-value properties.
3. **Valuation Principle:**
   $$\text{Taxable Value} = \max(\text{Declared Sale Consideration}, \text{Government Circle Rate Value})$$

### 3.2 District-Wise Circle Rate Architecture & Sample Rates

Circle rates in Uttarakhand are published at the district, tehsil, and sub-registrar level. Rates depend critically on:
- **Road Width / Access Category:** Main highway / arterial corridor vs branch road vs interior road (< 15 ft).
- **Distance Bands:** Properties situated within 50 meters of national/state highways attract higher multiplier bands than interior plots.
- **Land Use Category:** Agricultural (per Bigha / Hectare) vs Residential Plot (per sq. m) vs Commercial / Industrial (per sq. m).

#### Representative Rates Across Key Urban Centers:

| District / City | Sub-District / Locality | Category / Road Class | Residential Land (₹/sq. m) | Commercial Land (₹/sq. m) | Built-up Flat (₹/sq. ft) |
|---|---|---|---|---|---|
| **Dehradun** | Rajpur Road (Clock Tower to Diversion) | Prime Commercial Corridor | ₹55,000 – ₹70,000 | ₹1,10,000 – ₹1,50,000 | ₹4,500 – ₹6,500 |
| **Dehradun** | Sahastradhara Road | High-Growth Residential | ₹28,000 – ₹38,000 | ₹55,000 – ₹75,000 | ₹3,800 – ₹4,800 |
| **Dehradun** | Chakrata Road (Ballupur to Premnagar) | Arterial Highway | ₹32,000 – ₹45,000 | ₹65,000 – ₹90,000 | ₹3,500 – ₹4,500 |
| **Rishikesh** | Haridwar Road (Main Arterial) | Commercial Arterial | ₹35,000 – ₹48,000 | ₹70,000 – ₹95,000 | ₹4,000 – ₹5,500 |
| **Rishikesh** | Tapovan / Muni Ki Reti | Tourism / Hospitality Hub | ₹38,000 – ₹52,000 | ₹75,000 – ₹1,10,000 | ₹4,500 – ₹6,000 |
| **Haridwar** | Jwalapur Main Road | Commercial City Center | ₹25,000 – ₹35,000 | ₹50,000 – ₹70,000 | ₹3,000 – ₹4,000 |
| **Haridwar** | SIDCUL Industrial Area | Industrial / Commercial Zone | ₹15,000 – ₹22,000 | ₹30,000 – ₹45,000 | ₹2,500 – ₹3,500 |
| **Nainital** | Mall Road / Town Core | Eco-Sensitive Prime Commercial | ₹45,000 – ₹60,000 | ₹90,000 – ₹1,30,000 | ₹5,000 – ₹7,000 |
| **Haldwani** | Nainital Road / Kaladhungi Road | Commercial Arterial Corridor | ₹32,000 – ₹42,000 | ₹65,000 – ₹85,000 | ₹3,500 – ₹4,800 |
| **Haldwani** | Kathgodam Sub-Area | Residential Fringe | ₹20,000 – ₹28,000 | ₹40,000 – ₹55,000 | ₹3,000 – ₹3,800 |
| **Rudrapur** | Main Nainital Highway | Commercial Arterial | ₹24,000 – ₹34,000 | ₹48,000 – ₹68,000 | ₹2,800 – ₹3,800 |
| **Rudrapur** | SIDCUL Industrial Zone | Manufacturing / Industrial | ₹12,000 – ₹18,000 | ₹24,000 – ₹36,000 | ₹2,200 – ₹3,000 |
| **Kashipur** | Station Road / Ramnagar Road | Commercial Center | ₹22,000 – ₹30,000 | ₹45,000 – ₹60,000 | ₹2,600 – ₹3,500 |

---

## 4. Delhi (NCT) Real Estate Research

### 4.1 Locality Categorization Framework (Categories A through H)

The Government of NCT of Delhi (Department of Revenue, DORIS) categorizes all registered residential colonies into 8 distinct tiers:

| Category | Socio-Economic Classification | Representative Colonies | Base Land Rate (₹ / sq. m) | Base Construction Cost (₹ / sq. m) |
|---|---|---|---|---|
| **A** | Super Premium / Luxury | Golf Links, Vasant Vihar, Shanti Niketan, Jor Bagh, Chanakyapuri, Sunder Nagar, Panchsheel Park | **₹7,74,000** | ₹21,960 |
| **B** | Premium / High-End | Defence Colony, Greater Kailash (I & II), Hauz Khas, Anand Niketan, Neeti Bagh, Gulmohar Park | **₹2,45,520** | ₹17,400 |
| **C** | Upper Middle Class | Civil Lines, Lajpat Nagar (I–IV), Kalkaji, Malviya Nagar, Saket, Green Park | **₹1,59,840** | ₹13,920 |
| **D** | Middle Class | Dwarka (standard sectors), Janakpuri, Karol Bagh, Rajouri Garden, Mayur Vihar Phase I | **₹1,27,680** | ₹11,160 |
| **E** | Lower Middle Class | Chandni Chowk, Moti Nagar, Rohini (standard sectors), Kashmere Gate, Pahar Ganj | **₹70,080** | ₹9,360 |
| **F** | Urbanized Villages / Dense | Govindpuri, Uttam Nagar, Nangloi, Dilshad Garden, Shahdara | **₹56,640** | ₹8,220 |
| **G** | Resettlement / Sub-urban | Dakshinpuri, Tagore Garden Extn, Kondli, Sultanpuri | **₹46,200** | ₹6,960 |
| **H** | Peripheral / Low-Income | Sultanpur Majra, Nand Nagri, Holambi Kalan, Gokalpur | **₹23,280** | ₹3,480 |

### 4.2 Multipliers & Age Depreciation Matrix

1. **Use Multipliers:**
   - **Residential:** $1.0\times$
   - **Commercial:** $3.0\times$ on base land rate; commercial construction base is ₹25,200 (Cat A) down to ₹3,960 (Cat H).
   - **Industrial:** $2.0\times$ on base land rate.
2. **Age Depreciation Factor ($F_{\text{age}}$):**
   - Constructed in **2000 or later:** **1.0**
   - Constructed between **1990 and 1999:** **0.9**
   - Constructed between **1980 and 1989:** **0.8**
   - Constructed between **1970 and 1979:** **0.7**
   - Constructed between **1960 and 1969:** **0.6**
   - Constructed **prior to 1960:** **0.5**

### 4.3 Delhi Stamp Duty & Registration Charges

| Buyer Category | Stamp Duty Rate | Transfer Duty (MCD Component) | Total Effective Duty | Registration Fee |
|---|---|---|---|---|
| **Male Buyer** | 4.00% | 2.00% | **6.00%** | **1.00%** (no cap) |
| **Female Buyer** | 3.00% | 1.00% | **4.00%** | **1.00%** (no cap) |
| **Joint (Male + Female)** | 3.50% | 1.50% | **5.00%** | **1.00%** (no cap) |
| **NDMC Area (Male / Female)** | 3.50% / 2.50% | 2.00% / 1.00% | **5.50% / 3.50%** | **1.00%** (no cap) |
| **Delhi Cantonment Board** | 3.00% | 0.00% | **3.00%** | **1.00%** (no cap) |

### 4.4 Official Delhi Valuation Calculation Formula

For an independent plot and building:
$$\text{Government Valuation} = (\text{Plot Area in sq. m} \times \text{Base Land Rate} \times \text{Use Multiplier}) + (\text{Built-up Area in sq. m} \times \text{Base Construction Rate} \times F_{\text{age}})$$

For DDA / Cooperative Society Flats (Built-up):
$$\text{Flat Valuation} = \text{Plinth Area in sq. m} \times \text{Applicable Category Circle Rate per sq. m} \times \text{Floor / Lift Multiplier}$$

---

## 5. Technical Data Modeling Recommendations

To support accurate, bitemporal, and reproducible financial calculations across Indian banking and real estate, the following relational data schema is recommended:

### 5.1 Banking Domain Schemas
```sql
-- 1. Regulated Bank Entity
CREATE TABLE bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL, -- e.g., 'SBI', 'HDFC'
    name VARCHAR(255) NOT NULL,
    bank_type VARCHAR(64) NOT NULL, -- 'PUBLIC_SECTOR', 'PRIVATE_SECTOR', 'SMALL_FINANCE'
    dicgc_insured BOOLEAN NOT NULL DEFAULT TRUE,
    website_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Bank Account Product Variant
CREATE TABLE bank_account_product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_id UUID NOT NULL REFERENCES bank(id),
    name VARCHAR(255) NOT NULL,
    variant_code VARCHAR(64) NOT NULL, -- 'SAVINGS_PLUS', 'ACTIVMONEY', 'MONEY_MULTIPLIER'
    account_type VARCHAR(32) NOT NULL, -- 'SAVINGS', 'CURRENT', 'SALARY'
    minimum_balance_inr NUMERIC(15, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Effective-Dated Savings Interest Slabs
CREATE TABLE bank_interest_slab (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES bank_account_product(id),
    min_balance_inr NUMERIC(15, 2) NOT NULL,
    max_balance_inr NUMERIC(15, 2), -- NULL denotes unbounded
    interest_rate_pct NUMERIC(6, 4) NOT NULL,
    slab_type VARCHAR(32) NOT NULL, -- 'INCREMENTAL' (progressive) or 'FLAT'
    calculation_basis VARCHAR(64) NOT NULL DEFAULT 'DAILY_CLOSING_PRODUCT',
    credit_frequency VARCHAR(32) NOT NULL DEFAULT 'QUARTERLY',
    effective_from DATE NOT NULL,
    effective_to DATE, -- NULL indicates current active rate
    source_url VARCHAR(512) NOT NULL,
    recorded_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Auto-Sweep Rule Definition
CREATE TABLE auto_sweep_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES bank_account_product(id),
    sweep_out_threshold_inr NUMERIC(15, 2) NOT NULL,
    post_sweep_retained_inr NUMERIC(15, 2) NOT NULL,
    sweep_out_min_inr NUMERIC(15, 2) NOT NULL,
    sweep_out_increment_inr NUMERIC(15, 2) NOT NULL,
    sweep_in_trigger_inr NUMERIC(15, 2) NOT NULL,
    sweep_in_increment_inr NUMERIC(15, 2) NOT NULL,
    linked_fd_tenure_days INT NOT NULL DEFAULT 365,
    break_order VARCHAR(16) NOT NULL DEFAULT 'LIFO', -- 'LIFO' or 'FIFO'
    break_order_user_selectable BOOLEAN NOT NULL DEFAULT FALSE,
    premature_penalty_pct NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source_url VARCHAR(512) NOT NULL
);
```

### 5.2 Real Estate Valuation Schemas
```sql
-- 5. Real Estate Jurisdiction
CREATE TABLE re_jurisdiction (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_code VARCHAR(16) NOT NULL, -- 'UK' for Uttarakhand, 'DL' for Delhi
    state_name VARCHAR(128) NOT NULL,
    governing_body VARCHAR(255) NOT NULL,
    official_portal_url VARCHAR(255) NOT NULL
);

-- 6. Locality & Circle Rate Master
CREATE TABLE re_circle_rate (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id UUID NOT NULL REFERENCES re_jurisdiction(id),
    district VARCHAR(128) NOT NULL,
    tehsil_or_zone VARCHAR(128) NOT NULL,
    colony_or_locality VARCHAR(255) NOT NULL,
    category_tier VARCHAR(16), -- 'A' through 'H' for Delhi; NULL for UK
    road_access_class VARCHAR(64), -- 'ARTERIAL', 'HIGHWAY', 'INTERIOR'
    land_use VARCHAR(64) NOT NULL, -- 'RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL', 'AGRICULTURAL'
    rate_per_unit_inr NUMERIC(15, 2) NOT NULL,
    unit_of_measurement VARCHAR(32) NOT NULL, -- 'SQ_METER', 'SQ_FEET', 'BIGHA'
    effective_from DATE NOT NULL,
    effective_to DATE,
    notification_ref VARCHAR(255),
    source_url VARCHAR(512) NOT NULL
);

-- 7. Statutory Stamp & Registration Fee Formula Rules
CREATE TABLE re_stamp_duty_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jurisdiction_id UUID NOT NULL REFERENCES re_jurisdiction(id),
    buyer_gender VARCHAR(16) NOT NULL, -- 'MALE', 'FEMALE', 'JOINT'
    stamp_duty_pct NUMERIC(5, 3) NOT NULL,
    registration_fee_pct NUMERIC(5, 3) NOT NULL,
    registration_fee_cap_inr NUMERIC(15, 2), -- 25,000 for UK; NULL for Delhi
    concession_ceiling_inr NUMERIC(15, 2), -- 25,00,000 for UK female concession
    valuation_basis VARCHAR(64) NOT NULL DEFAULT 'HIGHER_OF_CONSIDERATION_OR_CIRCLE_RATE',
    effective_from DATE NOT NULL,
    effective_to DATE,
    notification_ref VARCHAR(255) NOT NULL
);
```

### 5.3 Historical Reproducibility & Bitemporal Auditing
To guarantee that a portfolio valuation computed in 2024 or 2026 can be reconstructed with 100% mathematical accuracy:
1. **Bitemporal Tracking:** Every rate and rule record must carry both:
   - `effective_from` / `effective_to` (business validity interval in the real world).
   - `recorded_at_utc` (audit system timestamp when the record entered our platform).
2. **Deterministic Valuation Snapshotting:**
   Whenever a portfolio valuation is executed:
   - Store an immutable record in `portfolio_valuation_event` containing: `total_value`, `calculation_timestamp`, `applied_engine_version`.
   - Store line items in `portfolio_valuation_item` linking each asset to the exact `rate_id` / `circle_rate_id` used.
   - Never recompute historical valuation by looking up today's rate table. Always query `WHERE effective_from <= :as_of_date AND (effective_to IS NULL OR effective_to > :as_of_date)`.

---

## 6. Research Limitations & Verification Status (Deliverable C)

1. **Unverified Dynamic Features:**
   - Some private banks (e.g., Axis Bank, ICICI Bank) allow relationship managers to customize sweep-out thresholds for bespoke HNIs. The figures documented here represent standard retail card guidelines.
   - AU Small Finance Bank and IDFC FIRST Bank periodically launch promotional bonus FD rates for specific tenures (e.g., 500 days). The data tables capture core standard tenures (1 yr, 2 yr, 3 yr, 5 yr).
2. **Uttarakhand Rural / Village Circle Rates:**
   - In rural hill tehsils, agricultural circle rates are denominated in local regional land measurement units (*Nali* and *Mutthi* in Garhwal/Kumaon: $1 \text{ Nali} \approx 2,160 \text{ sq. ft} \approx 200.7 \text{ sq. m}$; $1 \text{ Bigha} = 12 \text{ Nali}$). The platform must include conversion units when onboarding rural agricultural tracts.
3. **Delhi Slum / Unauthorized Colony Registrations:**
   - Properties in unauthorized colonies awaiting PM-UDAY regularisation use special concession flat rates rather than standard Category G/H circle rates. Automated valuations must require verification of regularisation status.

---

## 7. Official Source Register

1. **Reserve Bank of India (RBI):**
   - National Summary Data: `https://www.rbi.org.in/Scripts/BS_NSDPDisplay.aspx?param=4`
   - G-Sec & T-Bill Auction Results: `https://www.rbi.org.in/scripts/FS_PressRelease.aspx`
2. **Bank Official Portals:**
   - State Bank of India: `https://sbi.co.in`
   - Punjab National Bank: `https://pnbindia.in`
   - Bank of Baroda: `https://bankofbaroda.in`
   - Bank of India: `https://bankofindia.co.in`
   - Canara Bank: `https://canarabank.com`
   - Union Bank of India: `https://unionbankofindia.co.in`
   - HDFC Bank: `https://hdfcbank.com`
   - ICICI Bank: `https://icicibank.com`
   - Axis Bank: `https://axisbank.com`
   - Kotak Mahindra Bank: `https://kotak.com`
   - IDFC FIRST Bank: `https://idfcfirstbank.com`
   - AU Small Finance Bank: `https://aubank.in`
3. **Government of Uttarakhand:**
   - Department of Stamps and Registration: `https://registration.uk.gov.in`
   - Circle Rates & E-Valuation: `https://registration.uk.gov.in/stampduty-registration-fee/`
4. **Government of NCT of Delhi:**
   - Revenue Department & Circle Rates: `https://revenue.delhi.gov.in`
   - Delhi Online Registration Information System (DORIS): `https://doris.delhigovt.nic.in`
