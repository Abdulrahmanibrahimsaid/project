from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

CONSTANTS = {
    "celluloseFraction": 0.45,
    "hemicelluloseFraction": 0.30,
    "ligninFraction": 0.15,
    "moisture": 0.15,
    "celluloseToGlucose": 1.111,
    "hemicelluloseToXylose": 1.136,
    "glucoseToEthanol": 0.511,
    "xyloseToEthanol": 0.481,
    "ethanolDensity": 0.789,
    "ethanolEnergy": 29.7
}

def simulate_scenario(params):
    feed_rate = params["feed_rate"]
    pretreat = params["pretreat_eff"]
    hydroly = params["hydroly_eff"]
    ferment = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_op = params["annual_operating_cost"]

    dry_biomass = feed_rate * (1 - CONSTANTS["moisture"])
    cellulose = dry_biomass * 1000 * CONSTANTS["celluloseFraction"]
    hemicellulose = dry_biomass * 1000 * CONSTANTS["hemicelluloseFraction"]
    lignin = dry_biomass * 1000 * CONSTANTS["ligninFraction"]

    glucose = cellulose * CONSTANTS["celluloseToGlucose"] * pretreat * hydroly
    xylose = hemicellulose * CONSTANTS["hemicelluloseToXylose"] * pretreat * hydroly
    other_sugars = hemicellulose * 0.10 * pretreat * hydroly
    total_sugars = glucose + xylose + other_sugars

    ethanol_from_glucose = glucose * CONSTANTS["glucoseToEthanol"] * ferment
    ethanol_from_xylose = xylose * CONSTANTS["xyloseToEthanol"] * ferment * 0.85
    ethanol_from_others = other_sugars * 0.51 * ferment * 0.90
    ethanol_kg = ethanol_from_glucose + ethanol_from_xylose + ethanol_from_others
    ethanol_liters = ethanol_kg / CONSTANTS["ethanolDensity"]

    daily_revenue = ethanol_liters * eth_price
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugars * enzyme_cost
    daily_operating = annual_op / 365
    daily_labor = annual_op * 0.30 / 365
    daily_utilities = annual_op * 0.20 / 365
    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating + daily_labor + daily_utilities
    daily_profit = daily_revenue - total_daily_cost

    yield_per_ton = ethanol_liters / feed_rate
    sugar_conversion = (ethanol_kg / total_sugars * 100)
    profit_margin = (daily_profit / daily_revenue * 100) if daily_revenue > 0 else 0
    roi = (daily_profit * 365) / (annual_op * 2) * 100 if annual_op > 0 else 0

    return {
        "dry_biomass": round(dry_biomass, 2),
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
    pretreat_profits, hydroly_profits, ferment_profits, combined_profits = [], [], [], []

    for eff in efficiencies:
        sim_p = simulate_scenario({**params, "pretreat_eff": eff})
        pretreat_profits.append(sim_p["daily_profit"])

        sim_h = simulate_scenario({**params, "hydroly_eff": eff})
        hydroly_profits.append(sim_h["daily_profit"])

        sim_f = simulate_scenario({**params, "ferment_eff": eff})
        ferment_profits.append(sim_f["daily_profit"])

        sim_all = simulate_scenario({**params, "pretreat_eff": eff, "hydroly_eff": eff, "ferment_eff": eff})
        combined_profits.append(sim_all["daily_profit"])

    feed_rates = np.linspace(params["feed_rate"] * 0.5, params["feed_rate"] * 1.5, 15)
    feed_profits = [simulate_scenario({**params, "feed_rate": fr})["daily_profit"] for fr in feed_rates]

    return {
        "efficiencies": [e * 100 for e in efficiencies],
        "pretreat_profits": pretreat_profits,
        "hydroly_profits": hydroly_profits,
        "ferment_profits": ferment_profits,
        "combined_profits": combined_profits,
        "feed_rates": feed_rates.tolist(),
        "feed_profits": feed_profits
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    sensitivity = None
    error = None
    if request.method == 'POST':
        try:
            params = {k: float(request.form[k]) for k in ['feed_rate', 'pretreat_eff', 'hydroly_eff', 'ferment_eff', 'eth_price', 'feed_cost', 'enzyme_cost', 'annual_operating_cost']}
            results = simulate_scenario(params)
            sensitivity = sensitivity_analysis(params)
        except Exception as e:
            error = str(e)
    return render_template('index.html', results=results, sensitivity=sensitivity, error=error)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
