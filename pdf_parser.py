import os
import requests
import pandas as pd
from tqdm import tqdm
from time import sleep


QUERY = "induced pluripotent stem cells review"
MAX_PAPERS = 200
EMAIL = "dovgusha1@gmail.com"  # REQUIRED for Unpaywall

SAVE_DIR = "ipsc_papers_full"
os.makedirs(SAVE_DIR, exist_ok=True)



def search_pubmed(query, max_results=20):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    r = requests.get(url, params=params)
    return r.json()["esearchresult"]["idlist"]


def fetch_pubmed_details(pmids):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }
    r = requests.get(url, params=params)
    return r.json()["result"]


def get_doi(article):
    for item in article.get("articleids", []):
        if item["idtype"] == "doi":
            return item["value"]
    return None


def get_pdf_url(doi, pmid):
    # 1️⃣ Try Unpaywall
    try:
        if doi:
            url = f"https://api.unpaywall.org/v2/{doi}"
            r = requests.get(url, params={"email": EMAIL}, timeout=10)

            if r.status_code == 200:
                data = r.json()
                if data.get("best_oa_location"):
                    pdf = data["best_oa_location"].get("url_for_pdf")
                    if pdf:
                        return pdf, "Unpaywall"
                return None, "No OA via Unpaywall"
            else:
                return None, f"Unpaywall error {r.status_code}"
    except Exception as e:
        return None, f"Unpaywall exception: {e}"

    # 2️⃣ Try PMC
    try:
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/pdf"
        r = requests.get(pmc_url, timeout=10)

        if r.status_code == 200:
            return pmc_url, "PMC"
        else:
            return None, f"PMC not available ({r.status_code})"
    except Exception as e:
        return None, f"PMC exception: {e}"


def download_pdf(url, filename):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, stream=True, timeout=20)

        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        path = os.path.join(SAVE_DIR, filename)
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)

        return True, "Downloaded"

    except Exception as e:
        return False, str(e)


# ================= MAIN =================

print("🔎 Searching PubMed...")
pmids = search_pubmed(QUERY, MAX_PAPERS)

print("📄 Fetching article details...")
details = fetch_pubmed_details(pmids)

records = []

print("\n⬇️ Processing papers with feedback...\n")

for pmid in tqdm(pmids):
    article = details.get(pmid, {})

    title = article.get("title", "No title")
    doi = get_doi(article)

    print(f"\n📄 {title[:80]}...")
    print(f"   PMID: {pmid} | DOI: {doi}")

    pdf_url, source_info = get_pdf_url(doi, pmid)

    if pdf_url:
        print(f"   🔗 Found PDF via: {source_info}")
        success, status = download_pdf(pdf_url, f"{pmid}.pdf")
        print(f"   📥 {status}")
    else:
        success = False
        status = source_info
        print(f"   ❌ No PDF: {status}")

    records.append({
        "PMID": pmid,
        "Title": title,
        "DOI": doi,
        "PDF_URL": pdf_url,
        "Source": source_info,
        "Status": status,
        "Downloaded": success
    })

    sleep(1)  # polite delay

# ================= SAVE METADATA =================

df = pd.DataFrame(records)
csv_path = os.path.join(SAVE_DIR, "papers_metadata.csv")
df.to_csv(csv_path, index=False)

# ================= SUMMARY =================

total = len(records)
downloaded = sum(1 for r in records if r["Downloaded"])

print("\n📊 SUMMARY")
print(f"Total papers: {total}")
print(f"Downloaded: {downloaded}")
print(f"Failed: {total - downloaded}")

print("\n✅ DONE!")
print(f"📁 PDFs saved in: {SAVE_DIR}")
print(f"📄 Metadata saved: {csv_path}")