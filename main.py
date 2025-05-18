import json
import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import pandas as pd
from leads import run_scraper
from utils.nlp_processor import process_descriptions
import io
import traceback
from models import db, Company

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "linkedin-scraper-secret")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Print debug information about environment
logger.debug(f"DATABASE_URL: {os.environ.get('DATABASE_URL') is not None}")
logger.debug(f"PGDATABASE: {os.environ.get('PGDATABASE')}")
logger.debug(f"PGHOST: {os.environ.get('PGHOST')}")

# Set a fallback SQLite database if DATABASE_URL is not set
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///linkedin_companies.db"
    logger.warning("No DATABASE_URL found, using SQLite database")

# Initialize database
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Read default config
    config = {}
    if os.path.exists('scraper_config.json'):
        with open('scraper_config.json', 'r') as f:
            config = json.load(f)
    
    # Check if CSV exists to pass to template
    csv_exists = os.path.exists('lead1.csv')
    
    return render_template('index.html', config=config, csv_exists=csv_exists)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        keywords = request.form.get('keywords', 'IT services')
        founded_years = request.form.get('founded_years', '2015')
        founded_years = [year.strip() for year in founded_years.split(',')]
        country = request.form.get('country', 'United kingdom')
        size = request.form.get('size', '51-200')
        max_results = int(request.form.get('max_results', 10))
        sleep_time = float(request.form.get('sleep_time', 1.0))
        
        logger.debug(f"Scraping with parameters: keywords={keywords}, years={founded_years}, country={country}, size={size}")
        
        # Run the scraper
        results_df = run_scraper(
            keywords=keywords,
            founded_years=founded_years,
            country=country,
            size=size,
            max_results=max_results,
            sleep_time=sleep_time
        )
        
        # Process descriptions with NLP
        if not results_df.empty:
            results_df = process_descriptions(results_df)
            results_df.to_csv('lead1.csv', index=False)
            
            # Save to database
            companies_saved = 0
            for _, row in results_df.iterrows():
                try:
                    # Convert row to dict and create Company object
                    company_data = row.to_dict()
                    
                    # Check if company already exists (by LinkedIn URL)
                    existing_company = Company.query.filter_by(linkedin_url=company_data.get('companyLinkedinUrl')).first()
                    
                    if existing_company:
                        # Update existing company
                        for key, value in company_data.items():
                            if key == 'companyLinkedinUrl':
                                continue  # Skip the URL as it's already set
                            if hasattr(existing_company, key):
                                setattr(existing_company, key, value)
                            elif key == 'linkedin_url':
                                setattr(existing_company, 'linkedin_url', value)
                        db.session.commit()
                    else:
                        # Create new company record
                        new_company = Company.from_dict(company_data)
                        db.session.add(new_company)
                        db.session.commit()
                    
                    companies_saved += 1
                except Exception as e:
                    logger.error(f"Error saving company to database: {str(e)}")
                    db.session.rollback()
            
            flash(f"Scraping completed successfully! Saved {companies_saved} companies to database.", "success")
            return render_template('results.html', results=results_df.to_dict('records'))
        else:
            flash("No results found. Try adjusting your search parameters.", "warning")
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/download')
def download():
    try:
        # Create a CSV string from the DataFrame
        if os.path.exists('lead1.csv'):
            return send_file('lead1.csv', as_attachment=True)
        else:
            flash("No data available to download. Please run a scrape first.", "warning")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/companies')
def view_companies():
    try:
        # Get companies from database
        companies = Company.query.all()
        company_list = [company.to_dict() for company in companies]
        
        # Pass to template for display
        return render_template('companies.html', companies=company_list)
    except Exception as e:
        logger.error(f"Error viewing companies: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error retrieving companies: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    try:
        body = request.get_json()
        keywords = body.get('keywords', 'IT services')
        founded_years = body.get('founded_years', ['2015'])
        country = body.get('country', 'United kingdom')
        size = body.get('size', '51-200')
        
        # Run the scraper
        df = run_scraper(keywords, founded_years, country, size)
        
        # Process with NLP
        df = process_descriptions(df)
        
        # Save to CSV
        df.to_csv('lead1.csv', index=False)
        
        # Save to database
        for _, row in df.iterrows():
            try:
                company_data = row.to_dict()
                existing_company = Company.query.filter_by(linkedin_url=company_data.get('companyLinkedinUrl')).first()
                
                if existing_company:
                    # Update existing company
                    for key, value in company_data.items():
                        if key == 'companyLinkedinUrl':
                            continue
                        if hasattr(existing_company, key):
                            setattr(existing_company, key, value)
                        elif key == 'linkedin_url':
                            setattr(existing_company, 'linkedin_url', value)
                    db.session.commit()
                else:
                    # Create new company record
                    new_company = Company.from_dict(company_data)
                    db.session.add(new_company)
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error saving company to database: {str(e)}")
                db.session.rollback()
        
        # Return as CSV string
        csv_str = df.to_csv(index=False)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/csv"},
            "body": csv_str
        }
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
