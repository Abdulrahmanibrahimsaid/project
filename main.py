from flask import Flask, render_template, request, jsonify
import numpy as np
import json

app = Flask(__name__)

# القيم الثابتة المعتمدة على دراسات حقيقية
CONSTANTS = {
    # تركيبة الكتلة الحيوية (نموذج لقش الذرة)
    "celluloseFraction": 0.45,        # 45% سليلوز
    "hemicelluloseFraction": 0.30,     # 30% هيميسليلوز
    "ligninFraction": 0.15,            # 15% ليجنين
    "otherFraction": 0.10,              # 10% مواد أخرى
    
    # محتوى الرطوبة الافتراضي
    "moisture": 0.15,                   # 15% رطوبة
    
    # معاملات التحويل (حسب الدراسات)
    "celluloseToGlucose": 1.111,        # (162/180) معامل البلمرة
    "hemicelluloseToXylose": 1.136,      # (132/150) معامل تحويل الهيميسليلوز
    
    # كفاءات التحويل البيوكيميائية
    "glucoseToEthanol": 0.511,           # 51.1% كفاءة تحويل (نظري 0.511)
    "xyloseToEthanol": 0.481,            # 48.1% كفاءة تحويل الزايلوز
    
    # خواص فيزيائية
    "ethanolDensity": 0.789,              # كثافة الإيثانول كجم/لتر عند 20°C
    "sugarToEthanol": 0.51,               # معامل تحويل السكر لإيثانول
    
    # القيم الحرارية
    "ethanolEnergy": 29.7,                 # MJ/kg الطاقة النوعية للإيثانول
}

def calculate_carbohydrates(dry_biomass):
    """حساب مكونات الكتلة الحيوية"""
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
    """حساب السكريات المنتجة"""
    # تحويل السليلوز إلى جلوكوز
    glucose = cellulose * CONSTANTS["celluloseToGlucose"] * pretreat_eff * hydroly_eff
    
    # تحويل الهيميسليلوز إلى زايلوز وسكريات أخرى
    xylose = hemicellulose * CONSTANTS["hemicelluloseToXylose"] * pretreat_eff * hydroly_eff
    
    # سكريات أخرى بنسبة 10% من الهيميسليلوز
    other_sugars = hemicellulose * 0.10 * pretreat_eff * hydroly_eff
    
    return {
        "glucose": glucose,
        "xylose": xylose,
        "otherSugars": other_sugars,
        "total": glucose + xylose + other_sugars
    }

def calculate_ethanol(sugars, ferment_eff):
    """حساب الإيثانول المنتج"""
    # تحويل الجلوكوز
    ethanol_from_glucose = sugars["glucose"] * CONSTANTS["glucoseToEthanol"] * ferment_eff
    
    # تحويل الزايلوز (كفاءة أقل)
    ethanol_from_xylose = sugars["xylose"] * CONSTANTS["xyloseToEthanol"] * ferment_eff * 0.85
    
    # تحويل السكريات الأخرى
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
    """حساب المؤشرات الاقتصادية"""
    # الإيرادات
    daily_revenue = ethanol["liters"] * params["eth_price"]
    
    # التكاليف
    daily_feed_cost = feed_rate * params["feed_cost"]
    daily_enzyme_cost = sugars["total"] * params["enzyme_cost"]
    daily_operating = params["annual_operating_cost"] / 365
    daily_labor_cost = params["annual_operating_cost"] * 0.3 / 365  # 30% للعمالة
    daily_utility_cost = params["annual_operating_cost"] * 0.2 / 365  # 20% للطاقة
    
    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating + \
                      daily_labor_cost + daily_utility_cost
    
    daily_profit = daily_revenue - total_daily_cost
    
    # مؤشرات اقتصادية
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
    """دالة المحاكاة الرئيسية"""
    # استخراج المعاملات
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_operating_cost = params["annual_operating_cost"]
    
    # 1. حساب الكتلة الحيوية الجافة
    dry_biomass = feed_rate * (1 - CONSTANTS["moisture"])
    
    # 2. حساب مكونات الكتلة الحيوية
    components = calculate_carbohydrates(dry_biomass)
    
    # 3. حساب السكريات المنتجة
    sugars = calculate_sugars(components["cellulose"], components["hemicellulose"], 
                              pretreat_eff, hydroly_eff)
    
    # 4. حساب الإيثانول المنتج
    ethanol = calculate_ethanol(sugars, ferment_eff)
    
    # 5. الحسابات الاقتصادية
    economics = calculate_economics(ethanol, feed_rate, sugars, {
        "eth_price": eth_price,
        "feed_cost": feed_cost,
        "enzyme_cost": enzyme_cost,
        "annual_operating_cost": annual_operating_cost
    })
    
    # 6. حسابات إضافية
    yield_per_ton = ethanol["liters"] / feed_rate if feed_rate > 0 else 0
    sugar_conversion_eff = (ethanol["kg"] / sugars["total"] * 100) if sugars["total"] > 0 else 0
    overall_eff = (ethanol["kg"] / (dry_biomass * 1000 * 0.75) * 100) if dry_biomass > 0 else 0
    
    return {
        # المدخلات
        "feedRate": feed_rate,
        "dryBiomass": dry_biomass,
        
        # المكونات
        "cellulose": components["cellulose"] * 1000,
        "hemicellulose": components["hemicellulose"] * 1000,
        "lignin": components["lignin"] * 1000,
        
        # السكريات
        "glucose": sugars["glucose"],
        "xylose": sugars["xylose"],
        "totalSugars": sugars["total"],
        
        # الإيثانول
        "ethanolKg": ethanol["kg"],
        "ethanolL": ethanol["liters"],
        "ethanolFromGlucose": ethanol["fromGlucose"],
        "ethanolFromXylose": ethanol["fromXylose"],
        
        # الاقتصاد
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
        
        # مؤشرات الأداء
        "yieldPerTon": yield_per_ton,
        "sugarConversionEff": sugar_conversion_eff,
        "overallEff": overall_eff,
        
        # طاقة الإيثانول
        "energyOutput": ethanol["kg"] * CONSTANTS["ethanolEnergy"]
    }

def sensitivity_analysis(params):
    """تحليل الحساسية المتقدم"""
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_cost = params["annual_operating_cost"]
    sens_min = params.get("sens_min", 0.5)
    sens_max = params.get("sens_max", 1.0)
    
    steps = 20
    range_vals = np.linspace(sens_min, sens_max, steps + 1)
    
    pretreat_profits = []
    hydroly_profits = []
    ferment_profits = []
    price_profits = []
    cost_profits = []
    
    for val in range_vals:
        # تأثير كفاءة المعالجة
        sim1 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": val, "hydroly_eff": hydroly_eff,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        pretreat_profits.append(sim1["dailyProfit"])
        
        # تأثير كفاءة التحلل
        sim2 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": val,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        hydroly_profits.append(sim2["dailyProfit"])
        
        # تأثير كفاءة التخمير
        sim3 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": hydroly_eff,
            "ferment_eff": val, "eth_price": eth_price, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        ferment_profits.append(sim3["dailyProfit"])
        
        # تأثير سعر الإيثانول
        sim4 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": hydroly_eff,
            "ferment_eff": ferment_eff, "eth_price": val * 2, "feed_cost": feed_cost,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        price_profits.append(sim4["dailyProfit"])
        
        # تأثير تكلفة المواد
        sim5 = simulate_scenario({
            "feed_rate": feed_rate, "pretreat_eff": pretreat_eff, "hydroly_eff": hydroly_eff,
            "ferment_eff": ferment_eff, "eth_price": eth_price, "feed_cost": val * 100,
            "enzyme_cost": enzyme_cost, "annual_operating_cost": annual_cost
        })
        cost_profits.append(sim5["dailyProfit"])
    
    return {
        "range": (range_vals * 100).tolist(),
        "pretreatProfits": pretreat_profits,
        "hydrolyProfits": hydroly_profits,
        "fermentProfits": ferment_profits,
        "priceProfits": price_profits,
        "costProfits": cost_profits
    }

def feed_rate_analysis(params):
    """تحليل تأثير كمية المواد الخام"""
    feed_rate = params["feed_rate"]
    pretreat_eff = params["pretreat_eff"]
    hydroly_eff = params["hydroly_eff"]
    ferment_eff = params["ferment_eff"]
    eth_price = params["eth_price"]
    feed_cost = params["feed_cost"]
    enzyme_cost = params["enzyme_cost"]
    annual_cost = params["annual_operating_cost"]
    feed_range = params.get("feed_range", 30)
    
    min_feed = feed_rate * (1 - feed_range/100)
    max_feed = feed_rate * (1 + feed_range/100)
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

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html', constants=CONSTANTS)

@app.route('/simulate', methods=['POST'])
def simulate():
    """API للمحاكاة"""
    try:
        data = request.json
        
        # تشغيل المحاكاة الرئيسية
        results = simulate_scenario(data)
        
        # تحليل الحساسية
        sensitivity = sensitivity_analysis(data)
        
        # تحليل المواد الخام
        feed_analysis = feed_rate_analysis(data)
        
        return jsonify({
            'success': True,
            'results': results,
            'sensitivity': sensitivity,
            'feedAnalysis': feed_analysis,
            'constants': CONSTANTS
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/health')
def health():
    """فحص صحة التطبيق"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
