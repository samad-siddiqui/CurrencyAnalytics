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
    url = f"{BASE_URL}latest/v1/currencies/{base_currency}.json"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if base_currency in json_data:
            return list(json_data[base_currency].keys()) if base_currency in json_data  else []
    return []
def get_historical_date(currency_list,base_currency, days):
    """
    This function yields historical date for given currency and days.
    """
    
    for c in currency_list:
        # print(c)
        data = []
        list_data = []
        for i in range(days):
            date_str = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{BASE_URL}{date_str}/v1/currencies/{base_currency}.json"
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                if base_currency in json_data and c in json_data[base_currency]:
                    data.append(float(json_data[base_currency][c]))
                    list_data.append((float(json_data[base_currency][c])))
            else:
                print(f"Failed to fetch data for {c} on {date_str}")
        yield c, data, list_data
    print("data",data)
    print("list_data",list_data)
def standard_deviation(data):
    """
    this function calculates standard deviation for given data
    
    """
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
    plt.figure(figsize=(8, 8))
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
                        "Exchange_Rate (%)", "ROC", 
                        "Short MA", "Long MA"])
        writer.writerows(csv_data)
    print(f"CSV file saved: {filename}")


# Formation of PDF
# pdf.cell(width, height, text, ln(new line), align)
# pdf.set_font("font_name", style='B/I', size=size of text)
# pdf.image("Title", x co-ordinates, y co-ordinates, w = width of image)
def get_pdf(filename, top_3, bottom_3, csv_data, graph_filenames):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # First Page - Summary
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(250, 10, "Currency Performance Report", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.cell(250, 10, "Top 3 Best Performing Currencies:", ln=True)
    for rank, (cur, change) in enumerate(top_3, start=1):
        pdf.cell(250, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)

    pdf.cell(250, 10, "", ln=True)
    pdf.cell(250, 10, "Bottom 3 Worst Performing Currencies:", ln=True)
    for rank, (cur, change) in enumerate(bottom_3, start=1):
        pdf.cell(250, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)

    pdf.cell(350, 10, "", ln=True)
    pdf.cell(350,10,"Full Data Table:", ln=True)

    # Table Headers
    pdf.set_font("Arial", style='B', size=10)
    headers = ["Currency", "Std Dev", "Variation (%)", 
               "ROC", "Short MA", "Long MA", 
               "Max Rate", "Min Rate"]
    
    for header in headers:
        pdf.cell(25, 10, header, border=1)
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=10)
    for row in csv_data:
        for col in row:
            pdf.cell(25, 10, str(col), border=1)
        pdf.ln()

    # **Page Per Currency**
    for i, row in enumerate(csv_data):
        cur = row[0]
        max_value = row[6]  # Extract Max Value from csv_data
        min_value = row[7]  # Extract Min Value from csv_data
        
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(250, 10, f"Exchange Rate Analysis: {cur}", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.cell(250, 10, f"Max Exchange Rate: {max_value}", ln=True)
        pdf.cell(250, 10, f"Min Exchange Rate: {min_value}", ln=True)

        # Insert Graph
        if i < len(graph_filenames):
            pdf.image(graph_filenames[i], x=10, y=None, w=180)

    pdf.output(filename)
    print(f"PDF report saved: {filename}")

def run_pipeline(args):
        """
        Main function to run the pipeline.
        
        """
        validate_args(args.base_currency, args.N, args.M)
        available_currencies = fetch_available_currencies(args.base_currency)
        if not available_currencies:
            print("No available currencies to analyze.")
            exit(1)

        currencies = random.sample(available_currencies, args.M)
        list1 = []
        csv_data = []
        graph_filenames = []
        # historical_data = {} 
        for cur, rate, list_data in get_historical_date(currencies, args.base_currency, args.N):
            if not rate:
                print(f"{cur.upper()} - No Data Available")
                continue
            max_value = max(rate)
            min_value = min(rate)
            std_d = standard_deviation(rate)
            change = exchange_rate_data(rate)
            list1.append((cur, change))
            ROC = rate_of_change(rate)
            short_MA = moving_average(rate, 3)
            Long_MA = moving_average(rate, 10)

            print(
            f"\n{cur.upper()} - std_d Dev: {std_d}, "
            f"Exchange Rate: {change:.2f}%, "
            f"Max Value: {max_value}, Min Value: {min_value}"
            )

            print(f"ROC: {ROC}")
            print(f"Short MA: {short_MA}")
            print(f"Long MA: {Long_MA}")
            print(f"Maximum Value: {max_value}")
            print(f"Minimum Value: {min_value}")

            csv_data.append([cur.upper(), round(std_d, 4),
                            round(change, 2), round(ROC[-1], 4) if ROC else 0.0,
                            round(short_MA[-1], 4) if short_MA else 0.0,
                            round(Long_MA[-1], 4) if Long_MA else 0.0,
                            round(max_value, 4), 
                            round(min_value, 4)
                            
            ])
            filename = f"{cur}_trend.png"
            create_graph(
            x_labels=list(range(1, len(rate) + 1)), 
            y_values=rate, 
            title=f"Exchange Rate Trend for {cur.upper()}", 
            ylabel="Exchange Rate", 
            filename=f"{cur}_trend.png"
            )
            graph_filenames.append(filename)

            create_graph(
            x_labels=list(range(1, len(rate) + 1)), 
            y_values=rate, 
            title=f"Exchange Rate Trend for {cur.upper()}", 
            ylabel="Rate of Change (%)", 
            filename=f"{cur}_trend.png"
            )
            graph_filenames.append(filename)
        ranked = sorted(list1, key=lambda x: x[1],reverse=True)
        top_3 = ranked[:3]
        bottom_3 = ranked[-3:]
        
        for name, change in top_3:
            print(f"{name.upper()} - {change:.4f}%")
        for name, change in bottom_3:
            print(f"{name.upper()} - {change:.4f}%")
            
        create_csv("currency_data.csv",csv_data)
        # Generate standard deviation graph
        print("Generating standard deviation",graph_filenames)

        get_pdf("currency_analysis.pdf",top_3,bottom_3, csv_data, graph_filenames)
        # plot_each_currency_separately(historical_data, args.N)

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Currency Performance Analysis")
    parser.add_argument("N", type=int, default=3, help="Number of Days")
    parser.add_argument("M", type=int, default=3, help="Number of Currecies to Analize")
    parser.add_argument("base_currency", type=str, help="Base currency")
    args = parser.parse_args()
    run_pipeline(args)
    
    
    