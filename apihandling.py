import requests,csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fpdf import FPDF




BASE_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@"

def get_historical_date(CU,days):
    curr = {}
    for cur in CU:
        data = []
        for i in range(days):
            date_str = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{BASE_URL}{date_str}/v1/currencies/{cur}.json"
            #print(url)
            response = requests.get(url)
            #print(response)
            if response.status_code == 200:
                json_data = response.json()
                if cur in json_data:
                    rate = float(json_data[cur]["usd"]) 
                    data.append(rate)
                    #print("data",data)
            else:
                print(f"Failed to fetch data for {cur} on {date_str}")
        curr[cur] = data
    return curr


def Standard_deviation(data):

    mean = sum(data)/len(data)
    var  = sum((x - mean) ** 2 for x in data) / len(data)
    std  = var**0.5
    return std
def  exchange_rate_data(data):
    initital, final = data[0], data[-1]
    exchange_rate = ((initital - final)/initital)*100
    return exchange_rate

def rate_of_change(data):
    # start range with 1 bcz we have to compare to prevoius value
    if len(data) <2:
        return []
    return [(data[i] - data[i - 1]) / data[i - 1] * 100 for i in range(1, len(data))]



def moving_average(data, window):
    if len(data) < window:
        return [sum(data) / len(data)]
    return [sum(data[i:i+window]) / window for i in range(len(data) - window + 1)]

def create_graph(x_labels, y_values, title, ylabel, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(x_labels, y_values, marker='o', linestyle='-', color='b', linewidth=2, markersize=6)
    plt.xlabel("Currency")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(filename)
    plt.close()   
CU = ["usd", "eur", "gbp", "inr", "cad"]
gett = get_historical_date(CU, 10)
#print(Standard_deviation(gett))
list1 = []
csv_data = []
for cur, j in gett.items():
    if not j:
        print(f"{cur.upper()} - No Data Available")
        continue

    std = Standard_deviation(j)
    change = exchange_rate_data(j)
    list1.append(change)
    ROC = rate_of_change(j)
    short_MA = moving_average(j, 3)
    Long_MA = moving_average(j, 10)

    print(f"\n{cur.upper()} - Std Dev: {std}, Exchange Rate: {change:.2f}%")

    print(f"ROC: {ROC}")

    print(f"Short MA: {short_MA}")

    print(f"Long MA: {Long_MA}")

    csv_data.append([cur.upper(), round(std, 4), round(change, 2), round(ROC[-1], 4) if ROC else 0.0, 
    round(short_MA[-1], 4) if short_MA else 0.0, round(Long_MA[-1], 4) if Long_MA else 0.0
])

currencies = [row[0] for row in csv_data]  
std_values = [row[1] for row in csv_data] 
roc_values = [row[3] for row in csv_data]
create_graph(currencies, std_values, "Standard Deviation of Currencies", "Standard Deviation", "std_dev_chart.png")
create_graph(currencies, roc_values, "Rate of Change (ROC) of Currencies", "Rate of Change (%)", "roc_chart.png")

currency_changes = list(zip(CU, list1))
ranked = sorted(currency_changes, key=lambda x: x[1], reverse=True)
top_3 = currency_changes[:3]
bottom_3 = currency_changes[-3:]
print("\n=== Currency Ranking ===")
for rank, (name, exchange) in enumerate(ranked, start=1):
    print(f"{rank}. {name.upper()} - Change: {exchange:.2f}%")

with open("csv_data_file.csv",'w') as file:
    writer = csv.writer(file)
    writer.writerow(["Currency", "Std Dev", "Exchange Rate (%)", "ROC (Last)", "Short MA (Last)", "Long MA (Last)"])
    writer.writerows(csv_data)

# Formation of PDF
# pdf.cell(width, height, text, ln(new line), align)
# pdf.set_font("font_name", style='B/I', size=size of text)
# pdf.image("Title", x co-ordinates, y co-ordinates, w = width of image) 

 
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", style='B', size=16)
pdf.cell(200, 10, "Currency Performance Report", ln=True, align='C')


pdf.set_font("Arial", size=12)
pdf.cell(200, 10, "Top 3 Best Performing Currencies:", ln=True)
for rank, (cur, change) in enumerate(top_3, start=1):
    pdf.cell(200, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)

pdf.cell(200, 10, "", ln=True)
pdf.cell(200, 10, "Bottom 3 Worst Performing Currencies:", ln=True)
for rank, (cur, change) in enumerate(bottom_3, start=1):
    pdf.cell(200, 10, f"{rank}. {cur.upper()} - {change:.2f}%", ln=True)

pdf.cell(200, 10, "", ln=True)
pdf.cell(200, 10, "Full Data Table:", ln=True)

pdf.set_font("Arial", style='B', size=10)
pdf.cell(40, 10, "Currency", border=1)
pdf.cell(40, 10, "Std Dev", border=1)
pdf.cell(40, 10, "Exchange Rate (%)", border=1)
pdf.cell(40, 10, "ROC (Last)", border=1)
pdf.cell(40, 10, "Short MA (Last)", border=1)
pdf.cell(40, 10, "Long MA (Last)", border=1)
pdf.ln()

# Add data to table
pdf.set_font("Arial", size=10)
for row in csv_data:
    for col in row:
        pdf.cell(40, 10, str(col), border=1)
        #print(col)
    pdf.ln()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(200, 10, "Currency Performance Graphs", ln=True, align='C')

pdf.image("std_dev_chart.png", x=10, y=30, w=180)  
pdf.ln(110) 

pdf.image("roc_chart.png", x=10, y=150, w=180)  
pdf.ln(10)
pdf.output("currency_analysis.pdf")
print("PDF and CSV generated successfully!")