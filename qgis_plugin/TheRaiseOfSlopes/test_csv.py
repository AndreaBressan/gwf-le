#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test semplice per verificare che la lettura CSV funzioni
"""

import csv

def test_csv_reading():
    """Test della lettura del file CSV"""
    csv_path = "profilo_esempio.csv"

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            print(f"Header: {header}")

            count = 0
            for row in reader:
                if len(row) >= 2:
                    dist = float(row[0])
                    elev = float(row[1])
                    print(f"Punto {count+1}: distanza={dist}, quota={elev}")
                    count += 1
                if count >= 5:  # Mostra solo i primi 5 punti
                    break

            print(f"✓ File CSV letto correttamente. Totale punti: {count}")

    except Exception as e:
        print(f"✗ Errore nella lettura CSV: {e}")

if __name__ == "__main__":
    test_csv_reading()