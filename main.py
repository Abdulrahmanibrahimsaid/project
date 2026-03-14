from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

# Constant values based on real scientific studies
CONSTANTS = {
    # Biomass composition (corn stover model)
    "celluloseFraction": 0.45,        # 45% cellulose
    "hemicelluloseFraction": 0.30,     # 30% hemicellulose
    "ligninFraction": 0.15,            # 15% lignin
    "otherFraction": 0.10,              # 10% other materials
    
    # Default moisture content
    "moisture": 0.15,                   # 15% moisture
    
    # Conversion factors (based on scientific literature)
    "celluloseToGlucose": 1.111,        # (162/180) polymerization factor
    "hemicelluloseToXylose": 1.136,      # (132/150) hemicellulose conversion
    
    # Biochemical conversion efficiencies
    "glucoseToEthanol": 0.511,           # 51.1% conversion efficiency (theoretical 0.511)
    "xyloseToEthanol": 0.481,            # 48.1% xylose conversion efficiency
    
    # Physical properties
    "ethanolDensity": 0.789,              # Ethanol density kg/L at 20°C
    "sugarToEthanol": 0.51,               # Sugar to ethanol conversion factor
    
    # Energy values
    "ethanolEnergy": 29.7,                 # MJ/kg specific energy of ethanol
}

def calculate_carbohydrates(dry_biomass):
    """Calculate biomass components"""
    cellulose = dry_biomass * CONSTANTS["celluloseFraction"]
    hemicellulose = dry_biomass * CONSTANTS["hemicelluloseFraction"]
    lignin = dry_biomass * CONSTANTS["ligninFraction"]
    others = dry_biomass * CONSTANTS["otherFraction"]
    
    return {
        "cellulose": cellulose,
        "hemicellulose": hemicellulose,
        "lignin": lignin,
        "others": others
    }

def calculate_sugars(cellulose, hemicellulose, pretreat_eff, hydroly_eff):
    """Calculate produced sugars"""
    # Convert cellulose to glucose
    glucose = cellulose * CONSTANTS["celluloseToGlucose"] * pretreat_eff * hydroly_eff
    
    # Convert hemicellulose to xylose and other sugars
    xylose = hemicellulose * CONSTANTS["hemicelluloseToXylose"] * pretreat_eff * hydroly_eff
    
    # Other sugars (10% of hemicellulose)
    other_sugars = hemicellulose * 0.10 * pretreat_eff * hydroly_eff
    
    return {
        "glucose": glucose,
        "xylose": xylose,
        "otherSugars": other_sugars,
        "total": glucose + xylose + other_sugars
    }

def calculate_ethanol(sugars, ferment_eff):
    """Calculate ethanol production"""
    # Glucose conversion
    ethanol_from_glucose = sugars["glucose"] * CONSTANTS["glucoseToEthanol"] * ferment_eff
    
    # Xylose conversion (lower efficiency)
    ethanol_from_xylose = sugars["xylose"] * CONSTANTS["xyloseToEthanol"] * ferment_eff * 0.85
    
    # Other sugars conversion
    ethanol_from_others = sugars["otherSugars"] * CONSTANTS["sugarToEthanol"] * ferment_eff * 0.90
    
    ethanol_kg = ethanol_from_glucose + ethanol_from_xylose + ethanol_from_others
    ethanol_l = ethanol_kg / CONSTANTS["ethanolDensity"]
    
    return {
        "kg": ethanol_kg,
        "liters": ethanol_l,
        "fromGlucose": ethanol_from_glucose,
        "fromXylose": ethanol_from_xylose,
        "fromOthers": ethanol_from_others
    }

def calculate_economics(ethanol, feed_rate, sugars, params):
    """Calculate economic indicators"""
    # Revenue
    daily_revenue = ethanol["liters"] * params["eth_price"]
    
    # Costs
    daily_feed_cost = feed_rate * params["feed_cost"]
    daily_enzyme_cost = sugars["total"] * params["enzyme_cost"]
    daily_operating = params["annual_operating_cost"] / 365
    daily_labor_cost = params["annual_operating_cost"] * 0.3 / 365  # 30% labor
    daily_utility_cost = params["annual_operating_cost"] * 0.2 / 365  # 20% utilities
    
    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating + \
                      daily_labor_cost + daily_utility_cost
    
    daily_profit = daily_revenue - total_daily_cost
    
    # Economic indicators
    profit_margin = (daily_profit / daily_revenue * 100) if daily_revenue > 0 else 0
    break_even_point = total_daily_cost / params["eth_price"] if params["eth_price"] > 0 else 0
    roi = (daily_profit * 365) / (params["annual_operating_cost"] * 2) * 100 if params["annual_operating_cost"] > 0 else 0
    
    return {
        "revenue": daily_revenue,
        "feedCost": daily_feed_cost,
        "enzymeCost": daily_enzyme_cost,
        "operatingCost": daily_operating,
        "laborCost": daily_labor_cost,
        "utilityCost": daily_utility_cost,
        "totalCost": total_daily_cost,
        "profit": daily_profit,
        "profitMargin": profit_margin,
        "breakEvenPoint": break_even_point,
        "roi": roi
    }

def simulate_scenario(params):
    """Main simulation function"""
    # Extract parameters
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_operating_cost = params["annual_operating_cost"]
    
    # 1. Calculate dry biomass
    dry_biomass = feed_rate * (1 - CONSTANTS["moisture"])
    
    # 2. Calculate biomass components
    components = calculate_carbohydrates(dry_biomass)
    
    # 3. Calculate produced sugars
    sugars = calculate_sugars(components["cellulose"], components["hemicellulose"], 
                              pretreat_eff, hydroly_eff)
    
    # 4. Calculate ethanol production
    ethanol = calculate_ethanol(sugars, ferment_eff)
    
    # 5. Economic calculations
    economics = calculate_economics(ethanol, feed_rate, sugars, {
        "eth_price": eth_price,
        "feed_cost": feed_cost,
        "enzyme_cost": enzyme_cost,
        "annual_operating_cost": annual_operating_cost
    })
    
    # 6. Additional calculations
    yield_per_ton = ethanol["liters"] / feed_rate if feed_rate > 0 else 0
    sugar_conversion_eff = (ethanol["kg"] / sugars["total"] * 100) if sugars["total"] > 0 else 0
    overall_eff = (ethanol["kg"] / (dry_biomass * 1000 * 0.75) * 100) if dry_biomass > 0 else 0
    
    return {
        # Inputs
        "feedRate": feed_rate,
        "dryBiomass": dry_biomass,
        
        # Components
        "cellulose": components["cellulose"] * 1000,
        "hemicellulose": components["hemicellulose"] * 1000,
        "lignin": components["lignin"] * 1000,
        
        # Sugars
        "glucose": sugars["glucose"],
        "xylose": sugars["xylose"],
        "totalSugars": sugars["total"],
        
        # Ethanol
        "ethanolKg": ethanol["kg"],
        "ethanolL": ethanol["liters"],
        "ethanolFromGlucose": ethanol["fromGlucose"],
        "ethanolFromXylose": ethanol["fromXylose"],
        
        # Economics
        "dailyRevenue": economics["revenue"],
        "dailyFeedCost": economics["feedCost"],
        "dailyEnzymeCost": economics["enzymeCost"],
        "dailyOperating": economics["operatingCost"],
        "dailyLaborCost": economics["laborCost"],
        "dailyUtilityCost": economics["utilityCost"],
        "totalDailyCost": economics["totalCost"],
        "dailyProfit": economics["profit"],
        "profitMargin": economics["profitMargin"],
        "breakEvenPoint": economics["breakEvenPoint"],
        "roi": economics["roi"],
        
        # Performance indicators
        "yieldPerTon": yield_per_ton,
        "sugarConversionEff": sugar_conversion_eff,
        "overallEff": overall_eff,
        
        # Ethanol energy
        "energyOutput": ethanol["kg"] * CONSTANTS["ethanolEnergy"]
    }

def sensitivity_analysis(params):
    """Advanced sensitivity analysis"""
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_cost = params["annual_operating_cost"]
    
    steps = 20
    range_vals = np.linspace(0.5, 1.0, steps + 1)
    
    pretreat_profits = []
    hydroly_profits = []
    ferment_profits = []
    ethanol_production = []
    
    for val in range_vals:
        # Pretreatment efficiency effect
        sim1 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": val, "hydroly_eff": hydroly_eff,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        pretreat_profits.append(sim1["dailyProfit"])
        
        # Hydrolysis efficiency effect
        sim2 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": val,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        hydroly_profits.append(sim2["dailyProfit"])
        
        # Fermentation efficiency effect
        sim3 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": hydroly_eff,
            "ferment_eff": val, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        ferment_profits.append(sim3["dailyProfit"])
        
        # Ethanol production at different efficiencies
        ethanol_production.append(sim3["ethanolL"])
    
    return {
        "range": (range_vals * 100).tolist(),
        "pretreatProfits": pretreat_profits,
        "hydrolyProfits": hydroly_profits,
        "fermentProfits": ferment_profits,
        "ethanolProduction": ethanol_production
    }

def feed_rate_analysis(params):
    """Feed rate impact analysis"""
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_cost = params["annual_operating_cost"]
    
    min_feed = feed_rate * 0.5
    max_feed = feed_rate * 1.5
    steps = 15
    feed_values = np.linspace(min_feed, max_feed, steps + 1)
    
    ethanol_values = []
    profit_values = []
    revenue_values = []
    cost_values = []
    
    for f in feed_values:
        sim = simulate_scenario({
            "feed_rate": f, "pretreat_eff": pretreat_eff, "hydroly_eff": hydroly_eff,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        ethanol_values.append(sim["ethanolL"])
        profit_values.append(sim["dailyProfit"])
        revenue_values.append(sim["dailyRevenue"])
        cost_values.append(sim["totalDailyCost"])
    
    return {
        "feedValues": feed_values.tolist(),
        "ethanolValues": ethanol_values,
        "profitValues": profit_values,
        "revenueValues": revenue_values,
        "costValues": cost_values
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - displays form and results"""
    results = None
    sensitivity = None
    feed_analysis = None
    error = None
    
    if request.method == 'POST':
        try:
            # Read inputs from form
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
            
            # Validate inputs
            if params["feed_rate"] <= 0:
                raise ValueError("Feed rate must be greater than 0")
            if not all(0.5 <= v <= 1.0 for v in [params["pretreat_eff"], params["hydroly_eff"], params["ferment_eff"]]):
                raise ValueError("Efficiencies must be between 0.5 and 1.0")
            
            # Run simulations
            results = simulate_scenario(params)
            sensitivity = sensitivity_analysis(params)
            feed_analysis = feed_rate_analysis(params)
            
        except Exception as e:
            error = str(e)
    
    return render_template('index.html', 
                         results=results, 
                         sensitivity=sensitivity,
                         feed_analysis=feed_analysis,
                         error=error,
                         constants=CONSTANTS)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
