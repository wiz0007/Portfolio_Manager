# Investment Knowledge Base — India

**Version:** 1.0  
**Research cut-off:** 15 November 2026  
**Primary source:** *Finance Masterclass Notes.pdf* supplied in this conversation (21 pages).  
**Purpose:** A structured knowledge and data-design reference for the multi-asset portfolio management platform.

> **Important:** This is product research, not personalized financial advice. Rates, product terms, tax rules, ratings, market prices and property charges change. Every live value used by the product must carry a source, timestamp, effective date, unit and freshness status. The PDF's figures and opinions are retained as source material, not treated as verified current facts.

## 1. Evidence and data standards

Labels used below:
- **[PDF]** Explicitly stated in the supplied Finance Masterclass Notes.
- **[Research]** External research; source links are included.
- **[Design]** Proposed product or database requirement.
- **[Verify]** Must be checked against the current official provider terms, exchange data or law before implementation.

For every changing value, retain:
`value`, `unit`, `currency`, `source_provider`, `source_url`, `observed_at_utc`, `effective_from`, `effective_to`, `methodology`, `freshness_status`, `verification_status`, `notes`.

Do not store rates without their slab, product variant, customer eligibility, unit, time basis and effective date.

---

# PART A — FINANCIAL PLANNING CONTEXT

## 2. Inflation, compounding and investment horizon

### 2.1 Source notes [PDF]
The PDF explains inflation as a reduction in purchasing power and mentions lifestyle inflation. It quotes a 60-year average inflation figure of 7.5%, claims an 8–10% practical impact, and gives category estimates: education 10%, healthcare 13–14%, housing 10%, gold 10%. These are the speaker's figures and must not be used as current inflation assumptions without independent verification.

It recommends earning more, investing for long periods (10+ years), and reviewing portfolios periodically. Its compounding illustration and Rule of 72 are educational simplifications.

### 2.2 Product requirements [Design]
Support nominal return, inflation-adjusted return, user-defined inflation assumptions, goal horizon, liquidity needs, compounding frequency and cash-flow-aware returns.

Exact real return:
`real_return = (1 + nominal_return) / (1 + inflation_rate) - 1`

Rule of 72 approximation:
`years_to_double ≈ 72 / annual_return_percentage`

The Rule of 72 is a rough mental shortcut, not a forecast or guarantee.

## 3. Liquidity buckets

### 3.1 Source notes [PDF]
The PDF proposes:
- Bucket 1: 2–4 months of expenses in a bank account with auto-sweep FD; it gives ₹1–4 lakh as an example.
- Bucket 2: 6 months to 3 years of expenses in ultra-short/short-duration debt funds or FDs; it gives ₹10–36 lakh as an example.
- Bucket 3: long-term wealth in equity and real estate.

These are illustrative amounts, not universal targets. The platform should calculate needs from the user's expenses, goals, liabilities and risk capacity.

### 3.2 Suggested entities [Design]
`financial_goal`: user, target amount/date, priority, goal type, liquidity need, risk capacity, inflation assumption.  
`liquidity_bucket`: user, bucket type, target months of expenses, target amount, current value, linked instruments.

---

# PART B — CASH, BANK ACCOUNTS AND DEPOSITS

## 4. Savings and current accounts

A savings account is a liquid bank deposit. Interest is generally calculated using daily balances, but the applicable method, slabs and credit frequency must be taken from the bank's current terms. A current account is primarily transactional and may pay no interest or a bank-specific rate.

### 4.1 Comparison criteria [Design]

| Field | Required meaning |
|---|---|
| Bank/legal entity | Exact regulated bank, not just brand |
| Product/account variant | Savings, salary, premium, senior, current, NRE/NRO, etc. |
| Interest-rate slabs | Minimum/maximum balance and annual rate per slab |
| Interest calculation | Daily balance or other stated basis |
| Interest credit | Monthly/quarterly/other |
| Minimum balance | MAB/AMB/AQB requirement and measurement period |
| Non-maintenance charges | Fee, waiver and GST treatment |
| Transaction limits | ATM, cash deposit/withdrawal, UPI, NEFT/RTGS/IMPS |
| Auto-sweep | Available, opt-in/default, activation process |
| Sweep-out threshold | Balance above which surplus moves to FD |
| Sweep unit | Minimum sweep and increment/multiple |
| Sweep-in threshold | Balance below which FD is broken |
| Break order | LIFO/FIFO/bank-specific |
| Partial break | Whether only shortfall or whole FD is broken |
| Linked FD terms | Tenure, rate, renewal, maturity instructions |
| Premature closure | Penalty and interest recalculation |
| Eligibility | Residency, age, segment, account type and balance |
| Insurance | DICGC eligibility and aggregate cover |
| Source/effective date | Official document and rate effective date |

### 4.2 Auto-sweep / sweep-in deposits

An auto-sweep facility links a savings/current account to a term deposit. When the account balance exceeds a threshold, eligible surplus is transferred into one or more FDs. When the account needs money, the bank may break linked FD units to fund the debit.

**Do not model auto-sweep as a single interest rate.** Savings interest, linked FD interest, threshold logic, sweep unit, break order and premature-closure treatment are distinct product terms.

Capture:
1. Activation and deactivation method.
2. Eligible account variants and customer segments.
3. Sweep-out threshold and minimum sweep unit.
4. Sweep-in threshold and minimum reverse-sweep unit.
5. Trigger timing (end-of-day, periodic, real-time).
6. FD tenure, rate, compounding and renewal rules.
7. Partial-break support and break order.
8. Interest treatment if broken early.
9. Exclusions (tax-saver/non-callable/lien-marked deposits, account types).
10. Fees, tax/TDS, lien and minimum balance conditions.
11. Whether the customer can change thresholds.
12. Transaction-level sweep audit history.

### 4.3 Bank examples with verified rule details

These are product-specific examples, not bank-wide promises. Terms can change and must be rechecked before onboarding or recommendation.

**State Bank of India — Savings Plus / MODS**
- SBI's product booklet describes Savings Plus as a savings account linked to Multi Option Deposit Scheme (MODS).
- Surplus above a threshold is transferred automatically to term deposits.
- MODS withdrawals are described in multiples of ₹1,000.
- SBI's Depositors' Rights policy describes an auto-sweep minimum threshold balance of ₹35,000, minimum resultant balance ₹25,000, and minimum sweep amount ₹10,000 in multiples of ₹1,000.
- Sources: [SBI Depositors' Rights policy](https://sbi.co.in/documents/53471/263971/Policy%2Bon%2BDepositors%2BRights18082025.pdf/d171eb0e-5674-0a8b-98b5-f86e4491373a?t=1755494798543), [SBI product booklet](https://sbi.co.in/documents/53471/53742/210224-English%2B-%2Bmodified%2Binteractive%2Bbooklet%2Bof%2Bproducts%2B%26%2BServices.pdf/382b2ce6-8668-fb6f-c5f7-b462bce0e3d1?t=1708521488905).

**HDFC Bank — Sweep-in**
- HDFC's sweep-in undertaking describes LIFO (last-in, first-out) breakage.
- It specifies exclusions for certain FD sizes and non-withdrawable/tax-saver deposits.
- The document states no interest is paid when sweep-in is triggered within seven days of booking for domestic/NRO FDs, and within one year for NRE FDs. This is a document-specific term; confirm the current account and FD variant.
- Source: [HDFC sweep-in activation undertaking](https://www.hdfcbank.com/content/bbp/repositories/723fb80a-2dde-42a3-9793-7ae1be57c87f/?path=%2FFooter%2FResource%2FForms+Centre%2FContent%2FDetail+Page%2FForms+Center+-personal%2FUndertaking-of-Sweep-in-Activation.pdf).

**Kotak Mahindra Bank — ActivMoney**
- Kotak publishes variant-specific sweep-in/sweep-out thresholds.
- Its FAQ gives examples for savings accounts: Edge/Classic/Nova/Salary variants generally show ₹25,000 sweep-in and ₹50,000 sweep-out for new sign-ups; Ace/Pro savings show ₹50,000/₹50,000; Kotak 811 is listed separately. Privy/private-banking tiers have much higher thresholds.
- Kotak's help page also describes a minimum sweep-in formula tied to AMB (or ₹10,000, whichever is higher) and current-account thresholds tied to AQB. The published pages contain variant- and registration-date-specific rules; do not merge them into one generic Kotak rule.
- Kotak states regular FD rates apply to ActivMoney deposits, including for senior citizens, and ActivMoney cannot coexist with its separate one-way sweep-in facility on the same account.
- Sources: [ActivMoney FAQ](https://www.kotak.bank.in/en/get-help/activmoney.html), [threshold FAQ](https://www.kotak.bank.in/en/help-center/bank-account/activ-money/q14.html), [ActivMoney product page](https://www.kotak.bank.in/en/personal-banking/accounts/savings-account/activ-money-savings-account.html).

**Other banks to include in the catalogue**
- ICICI Bank — Money Multiplier / linked FD variants.
- Axis Bank — Encash 24 / sweep-in variants.
- IDFC FIRST Bank, AU Small Finance Bank, Equitas Small Finance Bank, Ujjivan Small Finance Bank and Jana Small Finance Bank — compare savings rates and FD products; verify sweep availability separately.
- For these banks, do not populate threshold fields until the exact current official product terms are obtained.

### 4.4 Savings-rate comparison methodology

Do not compare a single headline rate. Capture every rate slab and calculate the effective interest for a sample balance over a stated period. Include:
- balance slab and applicable rate;
- customer category;
- daily balance method;
- credit frequency;
- minimum balance and charges;
- auto-sweep eligibility;
- linked FD rate and breakage penalty;
- DICGC cover and bank risk context.

**Rate feed:** RBI's National Summary Data page provides banking-system savings and term-deposit rate statistics, not a substitute for each bank's product rate card. Use individual bank official rate cards for account-level data. [RBI National Summary Data](https://www.rbi.org.in/Scripts/BS_NSDPDisplay.aspx?param=4).

### 4.5 Deposit insurance

DICGC generally insures eligible deposits up to ₹5 lakh per depositor per insured bank, including principal and interest, in the same right and capacity. It is an aggregate bank-level limit, not ₹5 lakh per account or branch. Confirm eligibility, insured-bank status and exclusions against DICGC's current official material before showing coverage.

### 4.6 Fixed deposits

Capture principal, bank/product, start/maturity date, tenure, rate, fixed/floating basis, compounding frequency, cumulative/payout type, senior-citizen eligibility, callable status, premature penalty, loan/OD facility, accrued/credited interest, TDS and maturity instructions.

Compare effective annual yield and cash-flow timing, not headline rates alone.

### 4.7 Cash/deposit schema

`bank` (legal entity, regulator identifiers, insured status)  
`bank_account_product` (name, variant, segment, account type, minimum balance, charges, eligibility)  
`bank_interest_slab` (min/max balance, rate, effective dates, calculation and credit basis)  
`auto_sweep_rule` (thresholds, units, trigger, linked FD terms, break order, exclusions, effective dates)  
`deposit_position` (user, portfolio, bank/product, principal, dates, rate, tenure, payout, accrued interest)  
`deposit_transaction` (opening, sweep, reverse sweep, interest credit, maturity, premature closure).

---

# PART C — EQUITY

## 5. Equity instruments

Equity includes direct listed shares, equity mutual funds, ETFs and international equity funds. REITs/InvITs are listed securities but should have their own instrument types rather than being treated as ordinary company shares.

### 5.1 Individual stocks

A share is an ownership interest in a company. Return may come from price appreciation and dividends; neither is guaranteed.

The PDF names Reliance Industries, Asian Paints and ONGC as examples. Other large, widely followed Indian listed companies useful for building a reference universe include HDFC Bank, ICICI Bank, SBI, Infosys, TCS, Bharti Airtel, Larsen & Toubro, ITC, Hindustan Unilever, Mahindra & Mahindra, Maruti Suzuki and Sun Pharma. These are examples, not recommendations. Use NSE/BSE security masters for the actual universe.

### 5.2 Fundamental evaluation criteria [PDF + Design]

The PDF lists revenue/sales, gross profit margin, operating profit margin, net profit, free cash flow, debt/equity, loan interest, moat, P&L and balance sheet, P/E, average P/E, P/B, fair valuation, management ethics, fair-trade practices, depreciation, amortisation, EBIT and EBITDA.

Add:
- operating cash flow and cash conversion;
- EPS/diluted EPS and growth;
- ROE, ROCE and interest coverage;
- net debt/EBITDA and working-capital cycle;
- promoter holding/pledge and shareholding pattern;
- auditor qualifications, related-party transactions and contingent liabilities;
- corporate actions, dividends and buybacks;
- sector-specific operating metrics;
- consolidated vs standalone financial basis and reporting period.

### 5.3 Valuation metrics

- P/E: price divided by earnings per share; interpret with growth, cyclicality, accounting quality and peers.
- P/B: price relative to book value; often useful for financial institutions and asset-heavy businesses.
- EV/EBITDA: enterprise value relative to EBITDA; account for capital intensity and accounting differences.
- Price/sales: sometimes useful for low/negative-earnings businesses, but not a profitability substitute.
- Dividend yield: label trailing or forward basis.
- DCF/intrinsic value: assumption-sensitive; use scenarios and disclose inputs.
- Margin of safety: discount to estimated intrinsic value, with valuation method shown.

### 5.4 Stock schema

`equity_security`: ISIN, exchange, symbol, name, sector, industry, currency, tick size, lot size, listing status.  
`equity_quote`: price, bid/ask, volume, market cap, timestamp, source, delay flag.  
`equity_financial_metric`: instrument, period, metric, value, unit, consolidated/standalone basis, reported date, source.  
`corporate_action`: split, bonus, dividend, rights, merger, ex-date, record date and adjustment factor.  
`equity_holding` and `trade_lot`: user, portfolio, instrument, quantity, acquisition date, cost, fees and taxes.

## 6. Equity mutual funds

### 6.1 Types

**Passive/index funds:** Nifty 50, Nifty Next 50, Nifty 100, Nifty 500, Sensex, Nifty Midcap 150, Nifty Smallcap 250, Nifty Bank, Nifty IT, equal-weight and factor indices.

**Active equity fund categories:** Large Cap, Large & Mid Cap, Mid Cap, Small Cap, Flexi Cap, Multi Cap, Focused, Value, Contra, Dividend Yield, Sectoral/Thematic and ELSS. Category definitions must follow current SEBI rules.

Examples of AMCs to catalogue include SBI, HDFC, ICICI Prudential, UTI, Nippon India, Kotak, Axis, Motilal Oswal, DSP, Mirae Asset, Quant, Aditya Birla Sun Life, Edelweiss, Invesco, Navi and Tata. This is an AMC list, not a list of best schemes. Build the scheme catalogue from current AMFI/AMC feeds.

### 6.2 Scheme evaluation criteria

| Criterion | Meaning |
|---|---|
| Scheme category | SEBI category, mandate and benchmark |
| Direct/regular | Distribution-cost structure |
| Growth/IDCW | Accumulation vs distribution option |
| NAV | Per-unit value and date |
| TER/expense ratio | Annual scheme expenses; keep history |
| Tracking difference | Fund return minus benchmark return |
| Tracking error | Volatility of return difference; passive funds |
| AUM | Scheme assets; scale, not a safety score |
| Returns | 1/3/5/10-year and since inception; annualized/absolute label |
| Risk | Standard deviation, beta, Sharpe, Sortino, drawdown, riskometer |
| Portfolio | Holdings, sector weights, concentration, turnover |
| Fund manager | Tenure, changes, process |
| Exit load | Amount and holding-period conditions |
| Minimum investment | Lump-sum and SIP minimum |
| Liquidity | Redemption/settlement restrictions |
| Benchmark | Prefer TRI where appropriate |
| Overlap | Portfolio overlap with user's other schemes |
| Tax category | Effective-dated legal classification |

Do not compare returns unless period, NAV dates, plan type, option and benchmark return basis match.

### 6.3 Data sources and scheme records

AMFI provides latest NAV, downloadable NAV reports and historical NAV lookup. Its NFO page provides scheme launch and offer information. These are important discovery sources; AMC scheme documents and disclosures remain necessary for full terms.
- [AMFI NAV download/history](https://www.amfiindia.com/net-asset-value/nav-download)
- [AMFI NFO list](https://www.amfiindia.com/new-fund-offer)
- [AMFI scheme data/downloads](https://www.amfiindia.com/distributor-quick-access/downloads)

`mutual_fund_scheme`: scheme code, ISIN, AMC, name, category, benchmark, launch date, plan, option, status, riskometer.  
`fund_nav_history`: scheme, NAV, date, source, fetched_at.  
`fund_ter_history`: scheme, TER, plan, effective date.  
`fund_performance`: period, return type, benchmark return, calculation method.  
`fund_portfolio_disclosure`: disclosure date, security, weight, sector, asset type.  
`fund_risk_snapshot`: period, volatility, beta, Sharpe, Sortino, max drawdown, tracking error/difference.  
`mutual_fund_holding`: user, portfolio, scheme, units, lots, average cost/NAV, transactions.

---

# PART D — DEBT AND FIXED INCOME

## 7. Debt instruments

Debt means lending to a government, company or other issuer. Return can be fixed, floating, discounted or benchmark-linked. Risks include default, interest-rate changes, liquidity, reinvestment, inflation and concentration.

### 7.1 Government securities

- Treasury Bills (91/182/364-day tenors are common): issued at a discount and redeemed at face value.
- Dated Government Securities: sovereign bonds with stated coupon/maturity.
- State Development Loans (SDLs).
- Floating-rate and other notified government savings securities.
- Sovereign Gold Bonds: government securities denominated in grams of gold; new issuance depends on government policy, while outstanding issues may trade in the secondary market.

Evaluation: issuer, ISIN, face value, denomination, coupon, payment frequency, maturity, issue/current price, clean/dirty price, accrued interest, YTM, duration, convexity, liquidity, bid/ask spread, tax and settlement.

Coupon is not yield. YTM incorporates purchase price, coupons and redemption value under stated cash-flow assumptions.

### 7.2 Current government yield examples [Research]

RBI's 11 November 2026 T-Bill auction result reports cut-off YTMs:
- 91-day: 5.8681%
- 182-day: 6.5183%
- 364-day: 6.6394%

These are auction-specific yields, not guaranteed rates available at all times or a forecast. Use the latest RBI auction result for a live reference. [RBI, 11 Nov 2026](https://www.rbi.org.in/scripts/FS_PressRelease.aspx?fn=2757&prid=63955).

### 7.3 Corporate debt

Instrument types:
- Non-convertible debentures (NCDs).
- Secured/unsecured debentures.
- Convertible debentures.
- Commercial paper.
- Certificates of Deposit.
- Fixed/floating corporate bonds.
- Subordinated/perpetual debt (advanced/high-risk category).

Capture issuer/group, ISIN, series, secured status/collateral, seniority, covenants, coupon/reset benchmark, maturity, call/put, price, accrued interest, YTM, minimum investment, lot size, listing venue, volume, bid/ask, rating actions, defaults, restructuring, concentration and taxes.

### 7.4 Credit ratings

Ratings are opinions about relative credit risk, not guarantees. Preserve agency, rating symbol, scale, instrument/facility, outlook, watch status, action date, previous rating, rationale and report URL.

CRISIL's long-term scale describes AAA as highest safety/lowest credit risk, AA as high safety/very low credit risk, A as adequate safety/low credit risk, BBB as moderate safety/moderate credit risk, with lower categories carrying progressively greater risk; D denotes default/expected default. Short-term ratings use a different scale (A1, A2, A3, A4, D). Do not compare symbols across rating agencies without a valid mapping. [CRISIL rating scale](https://www.crisilratings.com/en/home/our-business/ratings/credit-ratings-scale.html).

### 7.5 Corporate bond yield examples [Research]

RBI's published market data reports September 2026 monthly-average corporate bond yields:
- AAA 1-year: 7.53%
- AAA 3-year: 7.85%
- AAA 5-year: 7.81%
- AA 3-year: 8.63%
- BBB-minus 3-year: 12.23%

RBI/FIMMDA figures are market averages, not promised investor returns. Higher yield can reflect materially higher credit/liquidity risk. [RBI Bulletin, September 2026 data](https://www.rbi.org.in/scripts/bs_viewbulletin.aspx/searchnew/Scripts/Scripts/BS_ViewBulletin.aspx?Id=24513).

## 8. Debt mutual funds

### 8.1 Categories

Common debt categories include Overnight, Liquid, Ultra Short Duration, Low Duration, Money Market, Short Duration, Medium Duration, Medium to Long Duration, Long Duration, Dynamic Bond, Corporate Bond, Credit Risk, Banking & PSU, Gilt, Gilt with 10-year constant duration and Floater funds.

The PDF groups overnight, liquid, ultra-short, short and long-duration funds and mentions gilt, money-market and dynamic-bond funds. Its tenure and return examples are illustrative, not current expected returns.

**Regulatory note:** SEBI issued a new categorization/rationalization circular dated 26 February 2026. The product taxonomy must follow the current circular and subsequent amendments, not rely on an old static category list. [SEBI circular](https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1772079826878.pdf).

### 8.2 Debt-fund evaluation

- YTM (portfolio yield indicator, not guaranteed investor return).
- Modified/Macaulay duration and average maturity.
- Credit-quality mix and issuer/group concentration.
- Sovereign/AAA/AA/A and lower-rated exposure.
- Interest-rate risk and credit-spread risk.
- AUM, TER, exit load and redemption terms.
- 1M/3M/6M/1Y/3Y/5Y returns with annualized/absolute label.
- Benchmark, riskometer and risk metrics.
- Fund manager tenure/process.
- Liquidity of underlying securities.
- Defaults, delays, downgrades and side-pocketing events.
- Portfolio turnover and cash levels.

AUM is not automatically “higher is better.” It is descriptive; portfolio quality, liquidity, concentration and mandate matter.

### 8.3 Recently launched debt funds — examples found at research cut-off

The NFO list is dynamic. These examples were visible in current 2026 source records and should be verified against the AMC SID/KIM and AMFI before being used in the app:

- **UTI Financial Services Debt Fund:** NFO 27 Oct–2 Nov 2026; allotment 3 Nov 2026. Invests predominantly in debt/money-market securities of financial-services entities; UTI's scheme page describes at least 80% allocation to eligible financial-services debt and AA+ and above credit quality. [UTI scheme page](https://www.utimf.com/mutual-funds/nfo/uti-financial-services-debt-fund), [NSE notice](https://noticeblue.com/circulars/ec3ae60f-7abb-44fb-843f-12a75140700f).
- **Aditya Birla Sun Life Fixed Maturity Plan — Series VC (114 Days):** AMFI lists NFO 5–17 Nov 2026, closed-ended fixed-income scheme. [AMFI NFO list](https://www.amfiindia.com/new-fund-offer).
- **DSP Fixed Maturity Plan Series 280 (90 Days):** reported as an NFO opening 13 Nov and closing 17 Nov 2026. Verify exact scheme documents and AMFI record before onboarding. [NFO listing](https://www.angelone.in/mutual-funds/new-fund-offers).
- **Nippon India CRISIL-IBX Far Gilt ETF:** debt ETF NFO record dated October 2026. Verify the AMC's scheme page and official offer document. [NFO notice](https://noticeblue.com/circulars/48cbdccb-b793-4db3-8f19-4917623f32dc).

For the product, derive “recently launched” from actual scheme launch dates. Distinguish a new scheme from a new plan/option, renamed scheme or exchange listing. Do not rank a new fund using a short track record.

### 8.4 Debt schema

`bond_security`: issuer, ISIN, instrument type, secured status, seniority, coupon, maturity, options, rating links.  
`bond_quote`: clean price, accrued interest, dirty price, YTM, timestamp, volume, bid/ask, source.  
`credit_rating_event`: agency, instrument, symbol, outlook, action, date, rationale, report URL.  
`debt_fund_snapshot`: scheme, date, YTM, duration, average maturity, credit mix, AUM, TER, source.  
`debt_fund_holding`: scheme, disclosure date, security, issuer, ISIN, weight, rating, maturity.

---

# PART E — REAL ESTATE

## 9. Types and source notes

Types: residential apartment, independent house, plot/land, commercial property, rental property, under-construction, ready-to-move, and REITs (listed trusts, separately modelled).

The PDF emphasizes locality knowledge, demand/supply, title/registry/GPA checks, possession, land use and upcoming government projects. It warns that buying can be easier than selling. It gives 3–4% rental yield plus 8–9% appreciation as an illustrative example only.

## 10. Real-estate evaluation criteria

### 10.1 Location and market
- Country/state/district/city/locality/micro-market and coordinates.
- Urban/rural status, zoning and land use.
- Road/rail/metro/airport access.
- Employment, schools, hospitals, retail and infrastructure projects.
- Comparable registered sale transactions (not only asking prices).
- Rent comparables, vacancy, absorption and transaction volume.
- Local demand/supply, environmental/flood risk.
- Public sentiment/perception only with source, date, sample and methodology; anecdotal views are not objective ratings.

### 10.2 Property and valuation
- Carpet, built-up, super built-up and plot area (store each separately with unit).
- Total price and price per sq ft/sq m.
- Government circle/guidance/ready-reckoner rate.
- Comparable market value and valuation method.
- Stamp duty, registration fee, surcharge, cess and exemptions.
- Brokerage, legal fees, loan charges, maintenance deposits and applicable GST.
- Property tax, recurring maintenance and insurance.
- Gross/net rental yield, vacancy and operating expenses.
- Loan-to-value, interest rate, EMI, leverage and selling costs.
- Liquidity/estimated time to sell.

### 10.3 Legal due diligence
Title chain, encumbrance search, registered deed, mutation, land records, survey boundaries, sanctioned plan, layout approval, land-use conversion, RERA registration/disclosures, occupancy/completion certificate, possession, litigation/acquisition notices, easements/access, GPA/POA validity, builder record, construction quality, society dues and utility connections.

A GPA is not automatically equivalent to a registered conveyance of ownership.

### 10.4 Government rates and registry charges

There is no single all-India circle rate or registration percentage. Rates and charges depend on state, district, sub-registrar jurisdiction, locality, property type, land use, transaction value, ownership attributes and current notifications.

Store:
- jurisdiction hierarchy and sub-registrar office;
- locality/ward/village and property classification;
- rate unit and government guidance value;
- stamp-duty slab/percentage;
- registration fee, cap or fixed component;
- surcharge/cess and exemptions;
- effective dates and official calculator/notification URL.

The PDF's 6–7% registry figure is a broad speaker estimate, not a national rule.

**Official jurisdiction sources**
- Uttarakhand Department of Stamps and Registration provides stamp-duty/registration notifications, e-valuation and GIS rate-list services: [official portal](https://registration.uk.gov.in/stampduty-registration-fee/) and [department home/e-services](https://registration.uk.gov.in/).
- Uttar Pradesh IGRSUP provides an official stamp and registration fee calculator requiring district, locality/village, document type, transaction value, market value and buyer attributes: [IGRSUP calculator](https://www.igrsup.gov.in/igrsup/stampFeesCalculator).

### 10.5 Property schema

`property_asset`: owner, portfolio, type, address, geo, ownership share, acquisition date, possession, area by type/unit, land use, project/RERA ID.  
`property_valuation`: date, estimated value, method, source, confidence, government value, comparable references.  
`property_cost`: stamp duty, registration, brokerage, legal, renovation, tax, maintenance, amount/date.  
`property_cashflow`: rent, vacancy, expense, property tax, date and amount.  
`property_legal_document`: type, issuing authority, date, verification status, secure document reference.  
`jurisdiction_charge_rule`: jurisdiction, property attributes, stamp/registration formula, effective dates, official source.

---

# PART F — GOLD AND COMMODITIES

## 11. Gold investment types

- Physical jewellery, coins and bars.
- Gold ETFs.
- Gold mutual funds/FoFs.
- Sovereign Gold Bonds (existing outstanding issues; new issuance is policy-dependent).
- Digital gold (review custody, counterparty, spread and regulatory structure carefully).

### 11.1 Evaluation criteria

Purity/fineness (999/916/750), reference price, city premium, buy/sell spread, making charges, GST/TCS where applicable, storage/insurance, hallmark/HUID, custody, liquidity, ETF NAV/market price, tracking difference, expense ratio, SGB issue/redemption terms and exchange liquidity.

### 11.2 Gold rate at research cut-off

Gold rates differ by provider, city, purity, timestamp and whether the quote is bullion, retail or exchange-traded. On 15 November 2026, Goodreturns reported indicative India rates of ₹13,762/g for 24K, ₹12,615/g for 22K and ₹10,322/g for 18K, excluding GST/TCS/other levies. Another bullion source showed a different Mumbai reference rate, demonstrating why the app must retain quote source and methodology rather than one national “gold price.” [Goodreturns, 15 Nov 2026](https://www.goodreturns.in/gold-rates/?formCode=MG0AV3), [All India Bullion reference](https://allindiabullion.com/gold-rate-today).

For a production feed store:
`metal`, `purity`, `city/market`, `quote_type`, `bid`, `ask`, `last`, `unit`, `currency`, `timestamp`, `source`, `tax_inclusion`, `retail_premium`.

### 11.3 Gold schema

`commodity_instrument`: metal, purity, contract/benchmark, currency, unit.  
`commodity_quote`: market/city, bid/ask/last, unit, quote type, timestamp, source.  
`gold_holding`: form, quantity, purity, cost, fees, storage/custody, acquisition date.

---

# PART G — HYBRID AND OTHER ASSETS

## 12. Hybrid mutual funds

Hybrid schemes combine equity, debt and, under current SEBI categories, potentially other permitted asset classes. Common categories include Conservative Hybrid, Balanced Hybrid, Aggressive Hybrid, Dynamic Asset Allocation/Balanced Advantage, Multi Asset Allocation, Arbitrage and Equity Savings.

Evaluate actual and permitted allocation ranges, rebalancing, equity style, debt credit quality/duration, derivatives/hedging, allocation drift, TER, AUM, manager tenure, benchmark, returns across cycles, riskometer, volatility, drawdown, exit load, liquidity and current tax classification.

Schema: `hybrid_allocation_history` (scheme/date/equity/debt/cash/commodity/InvIT/derivatives exposure); `hybrid_risk_snapshot` (scheme/date/volatility/drawdown/duration/credit mix/source).

## 13. Future asset classes

Not fully covered in the PDF; research separately before implementation:
- REITs and InvITs.
- International equity and foreign-currency assets.
- EPF, PPF, NPS, annuity/retirement products.
- Insurance products (separate insurance cover from investment value).
- Private equity, venture capital and unlisted shares.
- Crypto-assets (separate legal, custody, volatility and compliance review).
- Collectibles and other illiquid assets.

---

# PART H — PORTFOLIO TRACKING AND MARKET DATA

## 14. Holdings, transactions and valuation

Keep these concepts separate:
1. **Instrument master:** what the asset/product is.
2. **Holding:** what the user owns now.
3. **Transaction ledger:** what happened.
4. **Price/valuation observation:** observed or estimated value at a time.
5. **Portfolio snapshot:** calculated portfolio value at a time.

Maintain transactions or acquisition lots so quantities and cost basis can be reconstructed. Do not calculate holdings only from a manually entered average purchase price.

Transaction types should include buy, sell, deposit, withdrawal, dividend, interest, coupon, fee, tax/TDS, split, bonus, merger, rights issue, SIP, FD opening/maturity/breakage, bond redemption, rent, property expense and gold purchase/sale.

Each transaction: trade date, settlement date, type, quantity, unit price, gross amount, fees, taxes, currency, FX rate, linked instrument, status and source.

## 15. Charts and valuation frequency

Charts to support:
- instrument price/NAV history;
- portfolio total value;
- allocation by asset class over time;
- holding value and invested capital;
- realized/unrealized P&L;
- dividends, interest, coupons and rent;
- return contribution by asset;
- benchmark comparison;
- drawdown/volatility;
- cash-flow timeline.

**Price freshness must be asset-specific:**
- Listed stocks/ETFs: live or delayed exchange/broker quotes, subject to licensing.
- Mutual funds: generally latest published NAV, not tick-by-tick live prices.
- Savings/FDs: ledger balance and accrued interest, not market quotes.
- Bonds: may trade infrequently; last traded price may be stale. Clearly label evaluated prices/YTM.
- Direct property: periodic estimate/comparable/professional valuation, with date and confidence.
- Physical gold: reference quote updates frequently, but retail exit value depends on purity, local spread, tax and dealer.
- SGBs/gold ETFs: exchange quote/NAV availability and liquidity vary.

Use labels such as `live`, `delayed`, `end_of_day`, `latest_nav`, `indicative`, `estimated` and `stale`. Never label yesterday's NAV or a property estimate as a real-time executable price.

### 15.1 Valuation formulas

Quoted holding:
`market_value = quantity × latest_valid_price × contract_multiplier`

Multi-currency:
`base_value = local_value × fx_rate_to_portfolio_currency`

Deposit:
principal plus accrued interest under the product's actual terms; distinguish accrued from credited interest.

Bond:
clean price plus accrued interest (dirty value), where source data supports it. Be explicit about accrued coupon treatment.

Property:
latest estimate with valuation date, method, source and confidence.

### 15.2 Return calculations

Support absolute return, CAGR, time-weighted return, XIRR/money-weighted return, real return, realized/unrealized gain and income yield. A portfolio with deposits and withdrawals must use cash-flow-aware returns; simple percentage change is misleading.

## 16. Market-data provider architecture

Do not bind the application permanently to one vendor. Build adapters that normalize vendor responses into canonical internal observations.

Provider evaluation:
- asset coverage and Indian market coverage;
- live/delayed/EOD frequency and historical depth;
- NAV and corporate-action coverage;
- bond price/YTM/rating coverage;
- gold benchmark/city retail coverage;
- API limits, cost and redistribution rights;
- uptime/SLA, corrections and outage handling;
- timestamps/timezones and market calendars;
- authentication, key rotation and server-side secret storage.

Suggested entities: `data_provider`, `provider_instrument_mapping`, `market_quote`, `nav_observation`, `fx_rate`, `valuation_observation`, `market_calendar`, `ingestion_job`, `data_quality_issue`.

Pipeline: provider response → validation/normalization → canonical observation → time-series storage → valuation service. Store raw payload references only where licensing and privacy permit.

---

# PART I — TAX, COSTS AND RISK

## 17. Tax rules

The PDF contains tax-rate statements that may be outdated or incomplete. Do not hard-code them. Tax depends on instrument, acquisition/transaction date, holding period, residency, income slab and current law.

Model effective-dated rules:
- instrument/asset classification;
- taxable event (interest, dividend, coupon, rent, sale/redemption);
- holding-period threshold;
- STCG/LTCG treatment and applicable rates;
- surcharge/cess;
- cost-basis/indexation treatment where applicable;
- TDS/TCS;
- exemptions/reinvestment provisions;
- effective dates and official source.

Every tax estimate should show its assumptions, dates and rule version.

## 18. Cross-asset risk dimensions

Market/price, credit/default, interest-rate/duration, liquidity/exit, inflation, currency, concentration, counterparty/custody, operational/fraud, legal/title/regulatory, leverage/refinancing and valuation/model uncertainty.

A generic risk score without asset-specific methodology is misleading.

---

# PART J — CONCEPTUAL DATA MODEL

## 19. Recommended core entities

- `asset_class`
- `instrument_type`
- `instrument`
- `provider`
- `provider_product_terms`
- `market_observation`
- `portfolio`
- `holding`
- `transaction`
- `valuation_snapshot`
- `benchmark`
- `risk_snapshot`
- `tax_rule`
- `source_record`

Use common instrument identity plus type-specific extension tables; avoid one huge table full of nullable columns.

### 19.1 Data integrity requirements

- UUID internal primary keys.
- Official identifiers (ISIN, AMFI scheme code, bank product code, RERA number) where applicable.
- Fixed-precision decimal for money; never binary floating point.
- Adequate decimal precision for units/quantities.
- UTC storage, user-local display.
- Effective dates separate from fetch timestamps.
- Append-only transaction/observation history; correct via reversal/superseding records, not silent overwrites.
- Currency and unit on every monetary/market value.
- Source and methodology on derived metrics.
- Version calculation methodologies.

---

# PART K — RESEARCH AND IMPLEMENTATION BACKLOG

## 20. Current research gaps to close before production

1. Collect current official savings-rate slabs for each bank/account variant.
2. Verify exact sweep availability, thresholds, units, activation and breakage rules for ICICI, Axis and other shortlisted banks.
3. Collect FD rate cards and premature-closure rules.
4. Verify DICGC bank coverage and official wording.
5. Ingest current AMFI scheme master, NAV, TER, AUM, benchmark, portfolio and exit-load data.
6. Track NFOs from AMFI and verify each SID/KIM.
7. Collect current government-security and corporate-bond prices, YTM, rating actions and liquidity.
8. Build state/locality-specific circle-rate and stamp-duty rules from official portals.
9. Select gold quote source(s), purity, city and timestamp policy.
10. Verify tax rules with effective dates and official legislation.
11. Evaluate market-data API licensing, coverage, rate limits and cost.

## 21. Suggested build order

**Phase 1 — Catalogue and manual holdings:** asset classes, instrument types, instrument master, user holdings and transactions.  
**Phase 2 — Market data:** equities/ETFs, mutual-fund NAV, gold and FX.  
**Phase 3 — Cash/fixed income:** bank products, sweep terms, FD accrual, bonds, debt funds, ratings and duration.  
**Phase 4 — Real estate:** property records, acquisition costs, rent, expenses, jurisdictional rates and estimate confidence.  
**Phase 5 — Analytics and AI:** deterministic valuation, allocation, performance, risk and tax first; AI may explain and explore scenarios, but must not invent prices, ratings, returns or tax rules.

---

# APPENDIX A — SOURCE PDF TOPIC INDEX

| PDF pages | Topics |
|---|---|
| 1–3 | Inflation, purchasing power, savings vs FD vs Nifty 50 vs real estate, long-term investing |
| 4 | Compounding and Rule of 72 |
| 5–6 | Increasing income, spending discipline, major expenses and loans |
| 7–9 | Equity principles, stocks vs index/active funds, expense ratio, mutual-fund benefits |
| 10–12 | Market valuation, P/E vs risk-free rate, earnings, fundamental analysis |
| 13–14 | Debt mutual funds, bond types, debt-fund categories, risks and selection |
| 15–16 | Real estate, renting vs owning, title checks, locality, rental yield/appreciation |
| 17–18 | Cash management buckets and insurance |
| 19 | Investing principles and behavioural lessons |
| 20–21 | Tax discussion and case-study notes |

### PDF figures/claims requiring verification
Inflation assumptions; historical Nifty return; tax rates; P/E valuation bands; debt-fund return/tenure examples; real-estate yield/appreciation; registry-cost estimate; bank balance/bucket amounts; long-horizon asset-class ranking.

# APPENDIX B — GLOSSARY

AMC — Asset Management Company  
AUM — Assets Under Management  
CAGR — Compound Annual Growth Rate  
DICGC — Deposit Insurance and Credit Guarantee Corporation  
FD — Fixed Deposit  
G-Sec — Government Security  
IDCW — Income Distribution cum Capital Withdrawal  
ISIN — International Securities Identification Number  
NAV — Net Asset Value  
NCD — Non-Convertible Debenture  
NFO — New Fund Offer  
REIT — Real Estate Investment Trust  
SDL — State Development Loan  
SGB — Sovereign Gold Bond  
SIP — Systematic Investment Plan  
TER — Total Expense Ratio  
T-Bill — Treasury Bill  
TRI — Total Return Index  
YTM — Yield to Maturity  
XIRR — Extended Internal Rate of Return

---

**Document status:** Initial researched knowledge base. Source-PDF content, external research and proposed schema design are deliberately distinguished. Provider-specific bank rates, complete current scheme catalogues, and locality-level property charges remain data-ingestion/research tasks rather than invented static values.
