#!/usr/bin/env python3
"""
CSV Cleaner - simple OOP tool to normalize and deduplicate rows in a CSV.
Usage example:
 python cleaner.py --input sample_data.csv --output cleaned.csv --keys VendorName ProductID --normalize VendorName --report report.txt
"""

import argparse
import pandas as pd
import re
from datetime import datetime
from typing import List

class Normalizer:
    """Normalize text fields for comparison."""
    @staticmethod
    def normalize_text(value):
        if pd.isna(value):
            return ''
        s = str(value).lower().strip()
        # Remove punctuation, keep basic alphanumerics and spaces
        s = re.sub(r'[^a-z0-9\s]', '', s)
        # Collapse multiple spaces
        s = re.sub(r'\s+', ' ', s)
        return s

class CSVCleaner:
    def __init__(self, input_path: str, output_path: str, keys: List[str],
                 normalize_fields: List[str], report_path: str = None, keep_first=True):
        self.input_path = input_path
        self.output_path = output_path
        self.keys = keys or []
        self.normalize_fields = normalize_fields or []
        self.report_path = report_path
        self.keep_first = keep_first
        self.df = None
        self.before_count = 0
        self.after_count = 0
        self.duplicates_removed = 0

    def load(self):
        self.df = pd.read_csv(self.input_path, dtype=str, keep_default_na=False)
        self.before_count = len(self.df)

    def normalize(self):
        for field in self.normalize_fields:
            if field not in self.df.columns:
                print(f"Warning: normalize field '{field}' not in CSV columns.")
                continue
            norm_col = f"{field}__norm"
            self.df[norm_col] = self.df[field].apply(Normalizer.normalize_text)

    def _build_key_columns(self):
        keys = []
        for k in self.keys:
            if k in self.normalize_fields:
                keys.append(f"{k}__norm")
            else:
                keys.append(k)
        return keys

    def deduplicate(self):
        if not self.keys:
            print("No keys provided for deduplication. Skipping dedupe.")
            self.after_count = len(self.df)
            return

        keys = self._build_key_columns()
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=keys, keep='first' if self.keep_first else False)
        after = len(self.df)
        self.after_count = after
        self.duplicates_removed = before - after

    def save_cleaned(self):
        cols_to_drop = [c for c in self.df.columns if c.endswith('__norm')]
        out_df = self.df.drop(columns=cols_to_drop, errors='ignore')
        out_df.to_csv(self.output_path, index=False)

    def save_report(self):
        if not self.report_path:
            return
        lines = []
        lines.append(f"CSV Cleaner Report - {datetime.utcnow().isoformat()} UTC")
        lines.append(f"Input file: {self.input_path}")
        lines.append(f"Output file: {self.output_path}")
        lines.append(f"Rows before: {self.before_count}")
        lines.append(f"Rows after: {self.after_count}")
        lines.append(f"Duplicates removed: {self.duplicates_removed}")
        lines.append("")
        lines.append("Deduplication keys: " + ", ".join(self.keys if self.keys else ["(none)"]))
        lines.append("Normalized fields: " + ", ".join(self.normalize_fields if self.normalize_fields else ["(none)"]))
        try:
            if self.keys:
                key_cols = self._build_key_columns()
                orig = pd.read_csv(self.input_path, dtype=str, keep_default_na=False)
                for f in self.normalize_fields:
                    if f in orig.columns:
                        import re as _re
                        def _norm(v):
                            if pd.isna(v): return ''
                            s = str(v).lower().strip()
                            s = _re.sub(r'[^a-z0-9\s]', '', s)
                            s = _re.sub(r'\s+', ' ', s)
                            return s
                        orig[f + '__norm'] = orig[f].apply(_norm)
                grp = orig.groupby(key_cols).size().reset_index(name='count')
                dup_groups = grp[grp['count'] > 1].sort_values('count', ascending=False).head(10)
                if not dup_groups.empty:
                    lines.append("\nTop duplicate groups (up to 10):")
                    lines.extend(dup_groups.astype(str).to_string(index=False).splitlines())
                else:
                    lines.append("\nNo duplicate groups found in sample scan.")
        except Exception as e:
            lines.append(f"\nError generating groups preview: {e}")

        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def run(self):
        self.load()
        self.normalize()
        self.deduplicate()
        self.save_cleaned()
        if self.report_path:
            self.save_report()
        print("Done.")
        print(f"Rows before: {self.before_count}, after: {self.after_count}, duplicates removed: {self.duplicates_removed}")


def parse_args():
    p = argparse.ArgumentParser(description="CSV Cleaner - normalize & deduplicate using Python (OOP)")
    p.add_argument('--input', '-i', required=True, help='Input CSV path')
    p.add_argument('--output', '-o', required=True, help='Output cleaned CSV path')
    p.add_argument('--keys', '-k', nargs='+', required=True,
                   help='Column names to use as deduplication keys (space separated)')
    p.add_argument('--normalize', '-n', nargs='*', default=[],
                   help='Column names to normalize (case/punct/whitespace) prior to dedupe')
    p.add_argument('--report', '-r', help='Report text file path (optional)')
    p.add_argument('--keep-first', dest='keep_first', action='store_true', help='Keep first occurrence when deduping (default)')
    p.add_argument('--no-keep-first', dest='keep_first', action='store_false', help='Do not keep any duplicates (drop all duplicate groups)')
    p.set_defaults(keep_first=True)
    return p.parse_args()


def main():
    args = parse_args()
    cleaner = CSVCleaner(
        input_path=args.input,
        output_path=args.output,
        keys=args.keys,
        normalize_fields=args.normalize,
        report_path=args.report,
        keep_first=args.keep_first
    )
    cleaner.run()

if __name__ == '__main__':
    main()
