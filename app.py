import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)

# Load CSV file data into memory

commodity_data = pd.read_csv("commodity_prices.csv")

# Ensure 'Date' is parsed as datetime
commodity_data['Date'] = pd.to_datetime(commodity_data['Date'])

# List of commodities from the dataset
commodities = [
    'NATURAL GAS', 'GOLD', 'WTI CRUDE', 'BRENT CRUDE', 'SOYBEANS', 'CORN',
    'COPPER', 'SILVER', 'LOW SULPHUR GAS OIL', 'LIVE CATTLE', 'SOYBEAN OIL',
    'ALUMINIUM', 'SOYBEAN MEAL', 'ZINC', 'ULS DIESEL', 'NICKEL', 'WHEAT',
    'SUGAR', 'GASOLINE', 'COFFEE', 'LEAN HOGS', 'HRW WHEAT', 'COTTON'
]

# Dictionary to store trained models for each commodity
commodity_models = {}

# Train models for each commodity based on historical data
def train_models():
    global commodity_models
    for commodity in commodities:
        # Prepare the dataset for the commodity
        df = commodity_data[['Date', commodity]].dropna()
        df['Date'] = pd.to_datetime(df['Date']).map(pd.Timestamp.toordinal)
        
        # Split data into features and target
        X = df[['Date']]
        y = df[commodity]

        # Split into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model (using linear regression for simplicity)
        model = LinearRegression()
        model.fit(X_train, y_train)
        commodity_models[commodity] = model

# Function to predict price if exact date is not available
def predict_price(commodity, date):
    model = commodity_models.get(commodity)
    if model:
        date_ordinal = pd.to_datetime(date).toordinal()
        prediction = model.predict(np.array([[date_ordinal]]))
        return prediction[0]
    return None

@app.route('/')
def index():
    print(commodities)  # Debug log to check if commodities list is populated
    return render_template('index.html', commodities=commodities)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    selected_commodity = data['commodity']
    selected_date = data['date']

    try:
        # Convert user input date to datetime
        selected_date = pd.to_datetime(selected_date)

        # Filter the dataset based on selected date
        filtered_data = commodity_data[commodity_data['Date'] == selected_date]

        if not filtered_data.empty:
            # Get the price of the selected commodity
            price = filtered_data[selected_commodity].values[0]
            if pd.isna(price):
                return jsonify({"error": f"Price for {selected_commodity} not available on {selected_date.strftime('%Y-%m-%d')}."})
            return jsonify({"price": price})
        else:
            # If no data is available for the selected date, use the trained model to predict
            predicted_price = predict_price(selected_commodity, selected_date)
            if predicted_price:
                return jsonify({"price": predicted_price})
            else:
                return jsonify({"error": f"Prediction model for {selected_commodity} is not available."})
        
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # Train the models on startup
    train_models()
    app.run(debug=True)
