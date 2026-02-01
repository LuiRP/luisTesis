import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_bcv_rates():
    url = "https://www.bcv.org.ve/"

    try:
        response = requests.get(url, verify=False, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        euro_div = soup.find("div", id="euro")
        euro_val = euro_div.find("strong").text.strip() if euro_div else "Not Found"
        dolar_div = soup.find("div", id="dolar")
        dolar_val = dolar_div.find("strong").text.strip() if dolar_div else "Not Found"

        date_span = soup.find("span", class_="date-display-single")
        date_val = date_span.text.strip() if date_span else "Not Found"

        return {"USD": dolar_val, "EUR": euro_val, "Date": date_val}

    except Exception as e:
        return {"error": str(e)}


rates = get_bcv_rates()
