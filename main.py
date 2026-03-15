from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

# NREL standard constants
CONSTANTS = {
    "celluloseFraction": 0.45,          # 45% of dry biomass
    "hemicelluloseFraction": 0.30,       # 30% of dry biomass
    "ligninFraction": 0.15,              # 15% of dry biomass
    "otherFraction": 0.10,                # 10% other
    "celluloseToGlucose": 1.111,         # (180/162)
    "hemicelluloseToXylose": 1.136,       # (150/132)
    "glucoseToEthanol": 0.511,            # theoretical yield kg/kg
    "xyloseToEthanol": 0.481,             # theoretical yield kg/kg
    "ethanolDensity": 0.789,              # kg/L at 20°C
}

def simulate_scenario(params):
    # Read inputs (feed_rate is in dry tonnes/day)
    feed_rate = params["feed_rate"]          # dry tonne/day
    pretreat = params["pretreat_eff"]
    hydroly = params["hydroly_eff"]
    ferment = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]          # $/dry tonne
    enzyme_cost = params["enzyme_cost"]      # $/kg sugar
    annual_op = params["annual_operating_cost"]

    # Components (kg/day) – directly from dry feed rate
    cellulose = feed_rate * 1000 * CONSTANTS["celluloseFraction"]
    hemicellulose = feed_rate * 1000 * CONSTANTS["hemicelluloseFraction"]
    lignin = feed_rate * 1000 * CONSTANTS["ligninFraction"]

    # Sugars (kg/day)
    glucose = cellulose * CONSTANTS["celluloseToGlucose"] * pretreat * hydroly
    xylose = hemicellulose * CONSTANTS["hemicelluloseToXylose"] * pretreat * hydroly
    other_sugars = hemicellulose * 0.10 * pretreat * hydroly   # other sugars
    total_sugars = glucose + xylose + other_sugars

    # Ethanol (kg/day)
    ethanol_from_glucose = glucose * CONSTANTS["glucoseToEthanol"] * ferment
    ethanol_from_xylose = xylose * CONSTANTS["xyloseToEthanol"] * ferment * 0.85   # 85% of theoretical for xylose
    ethanol_from_others = other_sugars * 0.51 * ferment * 0.90                     # 90% of theoretical for others
    ethanol_kg = ethanol_from_glucose + ethanol_from_xylose + ethanol_from_others
    ethanol_liters = ethanol_kg / CONSTANTS["ethanolDensity"]

    # Economics
    daily_revenue = ethanol_liters * eth_price
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugars * enzyme_cost
    daily_operating = annual_op / 365
    daily_labor = annual_op * 0.30 / 365
    daily_utilities = annual_op * 0.20 / 365
    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating + daily_labor + daily_utilities
    daily_profit = daily_revenue - total_daily_cost

    # Performance indicators
    yield_per_ton = ethanol_liters / feed_rate
    sugar_conversion = (ethanol_kg / total_sugars * 100) if total_sugars > 0 else 0
    profit_margin = (daily_profit / daily_revenue * 100) if daily_revenue > 0 else 0
    roi = (daily_profit * 365) / (annual_op * 2) * 100 if annual_op > 0 else 0

    return {
        # Removed dry_biomass – now feed_rate is already dry
        "feed_rate": feed_rate,
        "cellulose": round(cellulose, 2),
        "hemicellulose": round(hemicellulose, 2),
        "lignin": round(lignin, 2),
        "glucose": round(glucose, 2),
        "xylose": round(xylose, 2),
        "total_sugars": round(total_sugars, 2),
        "ethanol_kg": round(ethanol_kg, 2),
        "ethanol_liters": round(ethanol_liters, 2),
        "yield_per_ton": round(yield_per_ton, 2),
        "daily_revenue": round(daily_revenue, 2),
        "daily_feed_cost": round(daily_feed_cost, 2),
        "daily_enzyme_cost": round(daily_enzyme_cost, 2),
        "daily_operating": round(daily_operating, 2),
        "daily_labor": round(daily_labor, 2),
        "daily_utilities": round(daily_utilities, 2),
        "total_daily_cost": round(total_daily_cost, 2),
        "daily_profit": round(daily_profit, 2),
        "profit_margin": round(profit_margin, 2),
        "roi": round(roi, 2)
    }

def sensitivity_analysis(params):
    efficiencies = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
    pretreat_profits = []
    hydroly_profits = []
    ferment_profits = []

    for eff in efficiencies:
        # Pretreatment variation
        sim_p = simulate_scenario({**params, "pretreat_eff": eff})
        pretreat_profits.append(sim_p["daily_profit"])

        # Hydrolysis variation
        sim_h = simulate_scenario({**params, "hydroly_eff": eff})
        hydroly_profits.append(sim_h["daily_profit"])

        # Fermentation variation
        sim_f = simulate_scenario({**params, "ferment_eff": eff})
        ferment_profits.append(sim_f["daily_profit"])

    return {
        "efficiencies": [e * 100 for e in efficiencies],
        "pretreat_profits": pretreat_profits,
        "hydroly_profits": hydroly_profits,
        "ferment_profits": ferment_profits
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    sensitivity = None
    error = None
    if request.method == 'POST':
        try:
            params = {
                "feed_rate": float(request.form['feed_rate']),
                "pretreat_eff": float(request.form['pretreat_eff']),
                "hydroly_eff": float(request.form['hydroly_eff']),
                "ferment_eff": float(request.form['ferment_eff']),
                "eth_price": float(request.form['eth_price']),
                "feed_cost": float(request.form['feed_cost']),
                "enzyme_cost": float(request.form['enzyme_cost']),
                "annual_operating_cost": float(request.form['annual_operating_cost'])
            }
            results = simulate_scenario(params)
            sensitivity = sensitivity_analysis(params)
        except Exception as e:
            error = str(e)
    return render_template('index.html', results=results, sensitivity=sensitivity, error=error)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
