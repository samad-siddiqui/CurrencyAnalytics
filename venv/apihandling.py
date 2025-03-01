import argparse
import random
from datetime import datetime, timedelta
import requests
import csv
import matplotlib.pyplot as plt
from fpdf import FPDF




BASE_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@"

def validate_args(base_currency, days, num_currencies):
    """
    Validate command-line arguments.
    """
    if not (1 <= days < 101):  
        raise ValueError("N (days) must be a positive integer.")
    if num_currencies <= 0:
        raise ValueError("M (number of currencies) must be a positive integer.")
    if not isinstance(base_currency, str) or len(base_currency) != 3:
        raise ValueError("Base currency must be a valid 3-letter currency code.")
def fetch_available_currencies(base_currency):
    """
    Fetch available currencies from the API.
    """
    l = []
    url = f"{BASE_URL}latest/v1/currencies/{base_currency}.json"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if base_currency in json_data:
            for currency, rate in json_data[base_currency].items():
                l.append(currency)
        return list(json_data[base_currency].keys()) if base_currency in json_data  else []
    return []
def get_historical_date(currency_list,base_currency, days):
    """
    This function yields historical date for given currency and days.
    """
    
    for c in currency_list:
        print(c)
        data = []
        for i in range(days):
            date_str = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{BASE_URL}{date_str}/v1/currencies/{base_currency}.json"
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                if base_currency in json_data and c in json_data[base_currency]:
                    data.append(float(json_data[base_currency][c]))
            else:
                print(f"Failed to fetch data for {c} on {date_str}")
        yield c, data


def standard_deviation(data):
    """
    this function calculates standard deviation for given data
    
    """
    if not data :
        raise ValueError("Data cant't be empty.")
    mean = sum(data)/len(data)
    var  = sum((x - mean) ** 2 for x in data) / len(data)
    std_d  = var**0.5
    return std_d
def  exchange_rate_data(data):
    """
    this function calculates exchange rate for given data
    
    """
    initital, final = data[0], data[-1]
    exchange_rate = ((initital - final)/initital)*100
    return exchange_rate

def rate_of_change(data):
    """
    this function calculates rate of change for given data
    
    """
    # start range with 1 bcz we have to compare to prevoius value
    if len(data) <2:
        return []
    return [(data[i] - data[i - 1]) / data[i - 1] * 100 for i in range(1, len(data))]



def moving_average(data, window):
    """
    this function calculates moving average for given data
    
    """
    if len(data) < window:
        return [sum(data) / len(data)]
    return [sum(data[i:i+window]) / window for i in range(len(data) - window + 1)]

def create_graph(x_labels, y_values, title, ylabel, filename):
    """
    this function creates graph for standard deviation and ROC
    
    """
    plt.figure(figsize=(8, 5))
    plt.plot(x_labels, y_values, marker='o', linestyle='-', color='b', linewidth=2, markersize=6)
    plt.xlabel("currency")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(filename)
    plt.close()
def create_csv(filename,csv_data):
    """
    this function creates CSV file for given data
    
    """
    with open(filename,'w', encoding="Utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["currency", "std_d Dev",
                        "Exchange Rate (%)", "ROC (Last)", 
                        "Short MA (Last)", "Long MA (Last)"])
        writer.writerows(csv_data)
    print(f"CSV file saved: {filename}")


# Formation of PDF
# pdf.cell(width, height, text, ln(new line), align)
# pdf.set_font("font_name", style='B/I', size=size of text)
# pdf.image("Title", x co-ordinates, y co-ordinates, w = width of image)

def get_pdf(filename,top_3,bottom_3, csv_data):
    """
    this function creates PDF file for given data
    
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "currency Performance Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Top 3 Best Performing currencies:", ln=True)
    for rank, (cur, change) in enumerate(top_3, start=1):
        pdf.cell(200, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)
    pdf.cell(200, 10, "", ln=True)
    pdf.cell(200, 10, "Bottom 3 Worst Performing currencies:", ln=True)
    for rank, (cur, change) in enumerate(bottom_3, start=1):
        pdf.cell(200, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)
    pdf.cell(200, 10, "", ln=True)
    pdf.cell(200, 10, "Full Data Table:", ln=True)
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(40, 10, "currency", border=1)
    pdf.cell(40, 10, "std_d Dev", border=1)
    pdf.cell(40, 10, "Exchange Rate (%)", border=1)
    pdf.cell(40, 10, "ROC (Last)", border=1)
    pdf.cell(40, 10, "Short MA (Last)", border=1)
    pdf.cell(40, 10, "Long MA (Last)", border=1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for row in csv_data:
        for col in row:
            pdf.cell(40, 10, str(col), border=1)
            #print(col)
        pdf.ln()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "currency Performance Graphs", ln=True, align='C')
    pdf.image("std_d_dev_chart.png", x=10, y=30, w=180)
    pdf.ln(150)
    pdf.image("roc_chart.png", x=10, y=150, w=180)
    pdf.ln(50)
    pdf.output("currency_analysis.pdf")
    print(f"PDF report saved: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Currency Performance Analysis")
    parser.add_argument("N", type=int, default=3, help="Number of Days")
    parser.add_argument("M", type=int, default=3, help="Number of Currecies to Analize")
    parser.add_argument("base_currency", type=str, help="Base currency")

    args = parser.parse_args()
    validate_args(args.base_currency, args.N, args.M)
    available_currencies = fetch_available_currencies(args.base_currency)
    if not available_currencies:
        print("No available currencies to analyze.")
        exit(1)

    currencies = random.sample(available_currencies, args.M)
    list1 = []
    csv_data = []

    for cur, rate in get_historical_date(currencies, args.base_currency, args.N):
        if not rate:
            print(f"{cur.upper()} - No Data Available")
            continue

        std_d = standard_deviation(rate)
        change = exchange_rate_data(rate)
        list1.append((cur, change))
        ROC = rate_of_change(rate)
        short_MA = moving_average(rate, 3)
        Long_MA = moving_average(rate, 10)

        print(f"\n{cur.upper()} - std_d Dev: {std_d}, Exchange Rate: {change:.2f}%")
        print(f"ROC: {ROC}")
        print(f"Short MA: {short_MA}")
        print(f"Long MA: {Long_MA}")

        csv_data.append([cur.upper(), round(std_d, 4),
                        round(change, 2), round(ROC[-1], 4) if ROC else 0.0,
                        round(short_MA[-1], 4) if short_MA else 0.0,
                        round(Long_MA[-1], 4) if Long_MA else 0.0
        ])

    ranked = sorted(list1, key=lambda x: x[1],reverse=True)
    top_3 = ranked[:3]
    bottom_3 = ranked[-3:]
    
    for name, change in top_3:
        print(f"{name.upper()} - {change:.4f}%")
    for name, change in bottom_3:
        print(f"{name.upper()} - {change:.4f}%")
        
    create_csv("currency_data.csv",csv_data)
    # Generate standard deviation graph
    create_graph(
    x_labels=[row[0] for row in csv_data], 
    y_values=[row[1] for row in csv_data], 
    title="Standard Deviation of Currencies", 
    ylabel="Standard Deviation", 
    filename="std_d_dev_chart.png"
    )

    create_graph(
    x_labels=[row[0] for row in csv_data], 
    y_values=[row[3] for row in csv_data], 
    title="Rate of Change (ROC) of Currencies", 
    ylabel="Rate of Change (%)", 
    filename="roc_chart.png"
    )

    get_pdf("currency_analysis.pdf ",top_3,bottom_3, csv_data)