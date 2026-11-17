# Duka Sales Exploration and Agent Network Clean-Up

**Name:** ADEN AHMED MOHAMED  
**Cohort:** 1M DEVIS

## Engagements

Duka Electronics needs a January–June 2026 sales review that explains branch, product, channel and calendar performance. The agent-network engagement audits and cleans unreliable transactions before reporting county/type and weekly throughput. Both datasets are synthetic and regenerated from the supplied generators without changing their random calls or seeds (2026 and 44).

## How to regenerate and run

1. Clone/download this repository and work from its root directory.
2. Install Python 3.10+ and dependencies: `python -m pip install -r requirements.txt`.
3. Run `python generate_data.py` to create `duka_sales.csv`, `agents.csv` and `agent_transactions.csv` locally.
4. Open `duka_sales_exploration.ipynb` in Jupyter, choose **Restart Kernel and Run All Cells**, then save; it regenerates the Premium Online CSV and validates the committed workbook against pandas.
5. Open `agent_cleanup.ipynb`, restart and run all cells, then save; it imports `clean_agent_data()`, shows the audit/log/validation/summaries and regenerates the clean transaction CSV.

Jupyter is the notebook application, installed separately if needed; pandas and NumPy are the only external libraries imported by the analysis. Both committed notebooks contain execution outputs. The raw generated CSVs are intentionally ignored by Git and must not be committed. Run generators locally before analysis (the notebooks also regenerate absent raw files automatically).

For Colab, first clone the complete repository and change into it so the local Python module and workbook are available, then run the relevant notebook cells:

```python
!git clone https://github.com/adenahmedm87/plp-da-a3-duka-sales-and-agent-cleanup.git
%cd plp-da-a3-duka-sales-and-agent-cleanup
!pip install -r requirements.txt
!python generate_data.py
```

## Duka Executive Summary

- The 1,000 orders generated KES 71,792,500 in revenue during the supplied January–June 2026 period.
- Nairobi led with KES 26,106,100, or 36.36% of revenue, and 376 orders, so it should remain the main sales focus.
- Laptops generated KES 41,535,000, while Tablets led unit sales at 691, supporting different priorities for revenue and volume.
- April was the best month at KES 13,518,300, exceeding June's KES 10,903,400 by 23.98%, using the worst month as the baseline.
- The Premium Online segment in Nairobi and Mombasa contained 83 orders worth KES 10,218,000, or 14.23% of total revenue, making it a specific segment for follow-up.

## Spreadsheet

`excel/duka_branch_summary.xlsx` includes the prepared Sales table, quantity × unit_price formulas, a SUMIFS branch revenue ranking, XLOOKUP regions and a **native PivotTable** of revenue by branch/channel. Branch totals and all 15 channel intersections match pandas, at **KES 71,792,500** in total. In Excel 365/2021+, use **Data → Refresh All** after editing the Sales table; formulas recalculate automatically. The workbook is a prepared deliverable; regenerating the same seed data does not change it. To rebuild its contents manually, import generated Duka orders into Sales, retain revenue/region formulas, SUMIFS summary and the documented Branches mapping, then refresh the PivotTable. The notebook checks the cached values of the saved workbook, so recalculate and save Excel before rerunning that check after edits.

## Agent cleaning: before and after

| Measure | Count |
|---|---:|
| Raw transaction rows | 612 |
| Unique clean transactions | 600 |
| Extra txn_id rows removed | 12 |
| Exact duplicate rows within the 12 extras | 11 |
| Duplicate IDs with an agent-only disagreement | 1 |
| Imputed amounts | 20 |
| Observed IQR outliers retained | 40 |
| Unknown agents after deduplication | 7 |

The pipeline prefers the registered ID only when a repeated txn_id differs solely in agent_id; other conflicting financial/type/date fields raise an error for source review. It trims/type-normalises labels, parses amounts and dates, flags before imputing missing/invalid amounts at **KES 1,776.50**, calculates IQR fences on observed valid deduplicated amounts, and uses a validated left join. Unknown county is labelled Unknown; outliers are not deleted. These choices preserve all 600 distinct transactions, but estimates and unverified values are not fit for settlement. See the notebook's six-dimension Data Quality Report and sensitivity tables.

## Repository contents

- `generate_data.py`: both supplied generators, fixed seeds and unchanged generation logic.
- `duka_sales_exploration.ipynb`: inspection, features, answers to Tasks 3–7 and workbook reconciliation.
- `cleaning_pipeline.py`: reusable cleaning function returning a DataFrame and structured log.
- `agent_cleanup.ipynb`: raw audit, cleaning, merge validation, county/agent/weekly summaries and report.
- `outputs/premium_online_coast_capital.csv`: 83 qualifying orders without an index column.
- `outputs/agent_transactions_clean.csv`: 600 unique transactions, ISO dates, county and flags.
- `excel/duka_branch_summary.xlsx`: SUMIFS, XLOOKUP and native PivotTable.
- `requirements.txt`: pandas and numpy, one per line.

## Definitions and privacy

Premium means **unit price ≥ KES 28,000**; weekends are Saturday/Sunday; monthly percentage comparison uses the worst month as denominator; weeks run Monday–Sunday and are labelled by Monday start date. The 180-day Duka sampling window ends before June month-end. Revenue does not measure Duka profit; agent transaction value measures throughput, not provider income. Region labels follow the Practicals mapping.

All committed records are synthetic. Real customer phone numbers and linkable transaction records would be personal data; keep them off public GitHub, minimise data, use appropriate purpose/notice and retention, encrypt it, restrict access and separate token mappings. See the [Kenya Data Protection Act 2019](https://odpc.go.ke/wp-content/uploads/2024/02/TheDataProtectionAct__No24of2019.pdf) and the report's privacy paragraph.
