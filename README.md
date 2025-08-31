\# CSV Cleaner (Python OOP)



Python project for object-oriented programming, CSV normalization, and deduplication. Created to detect and remove duplicate vendors for one of my previous jobs where duplicate vendors created errors and stop information flow on the integration among Salesforce.com, NetSuite and Flexera.



\## Run locally

```bash

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python cleaner.py --input sample\_data.csv --output cleaned.csv --keys VendorName ProductID --normalize VendorName --report report.txt



