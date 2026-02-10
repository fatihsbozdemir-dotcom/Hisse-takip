name: Hisse Fiyat Botu

on:
  schedule:
    # Türkiye saati 10:00, 13:00 ve 18:00 (UTC: 07:00, 10:00, 15:00)
    - cron: '0 7,10,15 * * 1-5'
  workflow_dispatch: # İstediğiniz an elle çalıştırmak için

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Kodları çek
        uses: actions/checkout@v3

      - name: Python ayarla
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Kütüphaneleri kur
        run: pip install yfinance pandas

      - name: Botu çalıştır
        run: python borsa.py

      - name: Değişiklikleri kaydet
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add fiyat_gecmisi.csv
          git commit -m "Fiyat güncellendi: $(date)" || exit 0
          git push
