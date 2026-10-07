"""
Synthetic Kirana Data Generator CLI
Tools / Data Engineering for Dukaan Growth Worker (PRD §8.5, TRD §16)

Generates realistic Sales, Expenses, and Udhaar registers with configurable
anomalies, customer debt profiles, and payment modes.
"""

import argparse
import calendar
import csv
import random
from pathlib import Path


def generate_dataset(
    output_dir: Path,
    month: str = "2026-09",
    missing_days: int = 0,
    inject_formulas: bool = False,
    high_udhaar: bool = False,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    year, mon = int(month[:4]), int(month[5:7])
    days_in_month = calendar.monthrange(year, mon)[1]

    # Active days
    available_days = list(range(1, days_in_month + 1))
    if missing_days > 0:
        # Drop random days
        drop_count = min(missing_days, len(available_days) - 1)
        dropped = set(random.sample(available_days, drop_count))
        active_days = [d for d in available_days if d not in dropped]
    else:
        active_days = available_days

    # Customer aliases
    regular_customers = [f"CUST_{i:03d}" for i in range(1, 26)]
    top_debtors = ["CUST_BIG1", "CUST_BIG2", "CUST_BIG3"] if high_udhaar else ["CUST_002", "CUST_008"]

    # 1. Generate Sales Register
    sales_file = output_dir / "sales.csv"
    with open(sales_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "bill_no", "customer_ref", "amount", "payment_mode"])

        bill_counter = 1001
        for day in active_days:
            date_str = f"{year:04d}-{mon:02d}-{day:02d}"
            # 3 to 6 bills per day
            bills_today = random.randint(3, 6)
            for _ in range(bills_today):
                bill_no = f"B{bill_counter}"
                bill_counter += 1

                cust = random.choice(regular_customers)
                if high_udhaar and random.random() < 0.4:
                    cust = random.choice(top_debtors)
                    mode = "UDHAAR"
                    amount = random.randint(1500, 4500)
                else:
                    mode = random.choices(["CASH", "UPI", "UDHAAR"], weights=[50, 35, 15])[0]
                    amount = random.randint(200, 1500)

                # Formula injection test
                if inject_formulas and bill_counter == 1005:
                    cust = "=SUM(A1:A10)"
                elif inject_formulas and bill_counter == 1006:
                    cust = "@cmd|' /C calc'!A0"

                writer.writerow([date_str, bill_no, cust, float(amount), mode])

    # 2. Generate Expenses Register
    expenses_file = output_dir / "expenses.csv"
    with open(expenses_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "category", "amount", "payment_mode", "notes"])

        # 3-5 wholesale stock purchases
        stock_days = random.sample(active_days, min(4, len(active_days)))
        for sd in stock_days:
            date_str = f"{year:04d}-{mon:02d}-{sd:02d}"
            amt = random.randint(4000, 9000)
            writer.writerow([date_str, "STOCK", float(amt), "BANK", "Wholesale staples replenishment"])

        # Utilities
        util_day = active_days[min(5, len(active_days) - 1)]
        writer.writerow([f"{year:04d}-{mon:02d}-{util_day:02d}", "ELECTRICITY", 1250.0, "UPI", "Shop meter bill"])
        writer.writerow([f"{year:04d}-{mon:02d}-{util_day:02d}", "TRANSPORT", 750.0, "CASH", "Tempo cartage"])

    # 3. Generate Udhaar Register
    udhaar_file = output_dir / "udhaar.csv"
    with open(udhaar_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_ref", "opening_balance", "credit_taken", "repaid_amount", "last_payment_date"])

        all_udhaar_customers = set(regular_customers[:10] + top_debtors)
        for cust in all_udhaar_customers:
            if cust in top_debtors and high_udhaar:
                opening = random.randint(7000, 12000)
                taken = random.randint(5000, 8000)
                repaid = random.randint(1000, 2500)
                last_pay = "2026-08-15"
            else:
                opening = random.randint(200, 1500)
                taken = random.randint(0, 1000)
                repaid = random.randint(200, 1200)
                last_pay = f"{year:04d}-{mon:02d}-20"

            writer.writerow([cust, float(opening), float(taken), float(repaid), last_pay])

    print(f"Generated synthetic dataset in: {output_dir}")
    print(f"  - sales.csv ({len(active_days)} active days)")
    print(f"  - expenses.csv")
    print(f"  - udhaar.csv ({len(all_udhaar_customers)} accounts)")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Kirana ledger datasets.")
    parser.add_argument("--output", "-o", type=Path, default=Path("data/synthetic_sample"))
    parser.add_argument("--month", "-m", type=str, default="2026-09")
    parser.add_argument("--missing-days", type=int, default=0, help="Number of days to omit (0..20)")
    parser.add_argument("--inject-formulas", action="store_true", help="Inject formula injection vectors")
    parser.add_argument("--high-udhaar", action="store_true", help="Generate high credit risk imbalance")

    args = parser.parse_args()
    generate_dataset(
        output_dir=args.output,
        month=args.month,
        missing_days=args.missing_days,
        inject_formulas=args.inject_formulas,
        high_udhaar=args.high_udhaar,
    )


if __name__ == "__main__":
    main()
