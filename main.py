from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ------------------------------
# ثوابت المرجع (ضمان نتائج دقيقة)
# ------------------------------
cell_frac = 0.38
hemi_frac = 0.32
lign_frac = 0.18
moisture_default = 0.10  # 10% moisture

gluc_to_eth = 0.51       # glucose to ethanol yield
eth_density = 0.786      # kg/L
cellulose_to_glucose = 1.111

# ------------------------------
# دالة المحاكاة
# ------------------------------
def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                      eth_price, feed_cost, enzyme_cost, annual_operating_cost):
    
    dry_biomass = feed_rate * (1 - moisture_default)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg  = dry_biomass * hemi_frac * 1000

    glucose_from_cellulose = cellulose_kg * cellulose_to_glucose
    xylose_from_hemi = hemicell_kg * cellulose_to_glucose

    sugar_from_cell = glucose_from_cellulose * pretreat_eff * hydroly_eff
    sugar_from_hemi = xylose_from_hemi * pretreat_eff * hydroly_eff

    total_sugar_kg = sugar_from_cell + sugar_from_hemi
    fermentable_sugar = total_sugar_kg * ferment_eff

    ethanol_kg = fermentable_sugar * gluc_to_eth
    ethanol_L = ethanol_kg / eth_density

    daily_revenue = ethanol_L * eth_price
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugar_kg * enzyme_cost
    daily_operating = annual_operating_cost / 365

    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating
    daily_profit = daily_revenue - total_daily_cost

    return {
        "dry_biomass": dry_biomass,
        "total_sugar_kg": total_sugar_kg,
        "fermentable_sugar_kg": fermentable_sugar,
        "ethanol_L": ethanol_L,
        "ethanol_kg": ethanol_kg,
        "daily_revenue": daily_revenue,
        "total_daily_cost": total_daily_cost,
        "daily_profit": daily_profit
    }

# ------------------------------
# دالة لتحويل الرسومات لBase64
# ------------------------------
def plot_to_img(x, y, title, xlabel, ylabel, color='blue', marker=None):
    plt.figure(figsize=(8,5))
    if marker:
        plt.plot(x, y, marker=marker, color=color)
    else:
        plt.plot(x, y, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# ------------------------------
# Flask route
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    pretreat_plot = hydroly_plot = ferment_plot = ethanol_plot = profit_plot = None

    # القيم الافتراضية
    feed_rate = 2205
    pretreat_eff = 0.9
    hydroly_eff = 0.9
    ferment_eff = 0.95
    eth_price = 0.57
    feed_cost = 58.5
    enzyme_cost = 0.1
    annual_operating_cost = 12000000

    if request.method == "POST":
        feed_rate = float(request.form["feed_rate"])
        pretreat_eff = float(request.form["pretreat_eff"])
        hydroly_eff = float(request.form["hydroly_eff"])
        ferment_eff = float(request.form["ferment_eff"])
        eth_price = float(request.form["eth_price"])
        feed_cost = float(request.form["feed_cost"])
        enzyme_cost = float(request.form["enzyme_cost"])
        annual_operating_cost = float(request.form["annual_operating_cost"])

    results = simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                                eth_price, feed_cost, enzyme_cost, annual_operating_cost)

    # Sensitivity Analysis - Efficiencies
    eff_range = np.linspace(0.5, 1.0, 31)
    pretreat_profits = [simulate_scenario(feed_rate, p, hydroly_eff, ferment_eff,
                                         eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for p in eff_range]
    hydroly_profits = [simulate_scenario(feed_rate, pretreat_eff, h, ferment_eff,
                                        eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for h in eff_range]
    ferment_profits = [simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, f,
                                        eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for f in eff_range]

    pretreat_plot = plot_to_img(eff_range*100, pretreat_profits, "Pretreatment Efficiency", "Efficiency (%)", "Daily Profit ($)", "red")
    hydroly_plot  = plot_to_img(eff_range*100, hydroly_profits, "Hydrolysis Efficiency", "Efficiency (%)", "Daily Profit ($)", "blue")
    ferment_plot  = plot_to_img(eff_range*100, ferment_profits, "Fermentation Efficiency", "Efficiency (%)", "Daily Profit ($)", "green")

    # Sensitivity vs Feed Rate
    feed_range = np.linspace(feed_rate*0.7, feed_rate*1.3, 10)
    ethanol_prod = []
    profit_list = []

    for f in feed_range:
        sim = simulate_scenario(f, pretreat_eff, hydroly_eff, ferment_eff,
                                eth_price, feed_cost, enzyme_cost, annual_operating_cost)
        ethanol_prod.append(sim["ethanol_L"])
        profit_list.append(sim["daily_profit"])

    ethanol_plot = plot_to_img(feed_range, ethanol_prod, "Ethanol Production vs Feedstock Rate",
                               "Feedstock Rate (ton/day)", "Ethanol Production (L/day)", "blue", marker='o')
    profit_plot = plot_to_img(feed_range, profit_list, "Daily Profit vs Feedstock Rate",
                               "Feedstock Rate (ton/day)", "Daily Profit ($)", "orange", marker='o')

    return render_template("index.html",
                           results=results,
                           pretreat_plot=pretreat_plot,
                           hydroly_plot=hydroly_plot,
                           ferment_plot=ferment_plot,
                           ethanol_plot=ethanol_plot,
                           profit_plot=profit_plot)

if __name__ == "__main__":
    app.run(debug=True)
