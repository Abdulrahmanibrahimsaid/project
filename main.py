from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

# Constant values based on real scientific studies - EXACT VALUES
CONSTANTS = {
    # Biomass composition (corn stover model)
    "celluloseFraction": 0.45,        # 45% cellulose
    "hemicelluloseFraction": 0.30,     # 30% hemicellulose
    "ligninFraction": 0.15,            # 15% lignin
    "otherFraction": 0.10,              # 10% other materials
    
    # Default moisture content
    "moisture": 0.15,                   # 15% moisture
    
    # Conversion factors (EXACT scientific values)
    "celluloseToGlucose": 1.111,        # (162/180) polymerization factor
    "hemicelluloseToXylose": 1.136,      # (132/150) hemicellulose conversion
    
    # Biochemical conversion efficiencies (EXACT)
    "glucoseToEthanol": 0.511,           # 51.1% theoretical yield
    "xyloseToEthanol": 0.481,            # 48.1% xylose conversion
    
    # Physical properties
    "ethanolDensity": 0.789,              # kg/L at 20°C
    
    # Energy values
    "ethanolEnergy": 29.7,                 # MJ/kg
}

def simulate_scenario(params):
    """Main simulation function - EXACT CALCULATIONS"""
    
    # Read inputs
    feed_rate = params["feed_rate"]              # ton/day
    pretreat_eff = params["pretreat_eff"]        # 0-1
    hydroly_eff = params["hydroly_eff"]          # 0-1
    ferment_eff = params["ferment_eff"]          # 0-1
    eth_price = params["eth_price"]              # $/L
    feed_cost = params["feed_cost"]              # $/ton
    enzyme_cost = params["enzyme_cost"]          # $/kg sugar
    annual_op_cost = params["annual_operating_cost"]  # $/year

    # 1. Dry biomass calculation (ton/day)
    dry_biomass = feed_rate * (1 - CONSTANTS["moisture"])
    
    # 2. Component calculations (convert to kg/day)
    cellulose = dry_biomass * 1000 * CONSTANTS["celluloseFraction"]
    hemicellulose = dry_biomass * 1000 * CONSTANTS["hemicelluloseFraction"]
    lignin = dry_biomass * 1000 * CONSTANTS["ligninFraction"]
    
    # 3. Sugar production (kg/day)
    glucose = cellulose * CONSTANTS["celluloseToGlucose"] * pretreat_eff * hydroly_eff
    xylose = hemicellulose * CONSTANTS["hemicelluloseToXylose"] * pretreat_eff * hydroly_eff
    other_sugars = hemicellulose * 0.10 * pretreat_eff * hydroly_eff
    total_sugars = glucose + xylose + other_sugars
    
    # 4. Ethanol production (kg/day)
    ethanol_from_glucose = glucose * CONSTANTS["glucoseToEthanol"] * ferment_eff
    ethanol_from_xylose = xylose * CONSTANTS["xyloseToEthanol"] * ferment_eff * 0.85
    ethanol_from_others = other_sugars * 0.51 * ferment_eff * 0.90
    
    ethanol_kg = ethanol_from_glucose + ethanol_from_xylose + ethanol_from_others
    ethanol_liters = ethanol_kg / CONSTANTS["ethanolDensity"]
    
    # 5. Economic calculations
    # Revenue
    daily_revenue = ethanol_liters * eth_price
    
    # Costs
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugars * enzyme_cost
    daily_operating = annual_op_cost / 365
    daily_labor = annual_op_cost * 0.30 / 365
    daily_utilities = annual_op_cost * 0.20 / 365
    
    total_daily_cost = (daily_feed_cost + daily_enzyme_cost + 
                       daily_operating + daily_labor + daily_utilities)
    
    daily_profit = daily_revenue - total_daily_cost
    
    # Performance indicators
    yield_per_ton = ethanol_liters / feed_rate
    sugar_conversion = (ethanol_kg / total_sugars * 100) if total_sugars > 0 else 0
    profit_margin = (daily_profit / daily_revenue * 100) if daily_revenue > 0 else 0
    break_even = total_daily_cost / eth_price if eth_price > 0 else 0
    roi = (daily_profit * 365) / (annual_op_cost * 2) * 100 if annual_op_cost > 0 else 0
    
    return {
        # Inputs
        "feed_rate": feed_rate,
        
        # Components
        "dry_biomass": dry_biomass,
        "cellulose": round(cellulose, 2),
        "hemicellulose": round(hemicellulose, 2),
        "lignin": round(lignin, 2),
        
        # Sugars
        "glucose": round(glucose, 2),
        "xylose": round(xylose, 2),
        "total_sugars": round(total_sugars, 2),
        
        # Ethanol
        "ethanol_kg": round(ethanol_kg, 2),
        "ethanol_liters": round(ethanol_liters, 2),
        "yield_per_ton": round(yield_per_ton, 2),
        
        # Economics
        "daily_revenue": round(daily_revenue, 2),
        "daily_feed_cost": round(daily_feed_cost, 2),
        "daily_enzyme_cost": round(daily_enzyme_cost, 2),
        "daily_operating": round(daily_operating, 2),
        "daily_labor": round(daily_labor, 2),
        "daily_utilities": round(daily_utilities, 2),
        "total_daily_cost": round(total_daily_cost, 2),
        "daily_profit": round(daily_profit, 2),
        
        # Performance
        "profit_margin": round(profit_margin, 2),
        "break_even": round(break_even, 2),
        "roi": round(roi, 2),
        "sugar_conversion": round(sugar_conversion, 2),
        
        # Energy
        "energy_output": round(ethanol_kg * CONSTANTS["ethanolEnergy"], 2)
    }

def sensitivity_analysis(params):
    """Sensitivity analysis for efficiencies"""
    results = []
    efficiencies = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
    
    for eff in efficiencies:
        sim = simulate_scenario({
            "feed_rate": params["feed_rate"],
            "pretreat_eff": eff,
            "hydroly_eff": eff,
            "ferment_eff": eff,
            "eth_price": params["eth_price"],
            "feed_cost": params["feed_cost"],
            "enzyme_cost": params["enzyme_cost"],
            "annual_operating_cost": params["annual_operating_cost"]
        })
        results.append({
            "efficiency": eff * 100,
            "profit": sim["daily_profit"],
            "ethanol": sim["ethanol_liters"]
        })
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page"""
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
            
            # Validate
            if params["feed_rate"] <= 0:
                raise ValueError("Feed rate must be > 0")
            
            results = simulate_scenario(params)
            sensitivity = sensitivity_analysis(params)
            
        except Exception as e:
            error = str(e)
    
    return render_template('index.html', 
                         results=results, 
                         sensitivity=sensitivity,
                         error=error,
                         constants=CONSTANTS)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.5.0', port=5000)
