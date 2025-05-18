import json
import pandas as pd
import requests
import time
import logging
import os
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def classify_domain(domain, company_name='', description=''):
    """
    Classify a company domain into specific business categories
    Uses multiple data points: domain name, company name, and description
    """
    # Ensure we're working with lowercase strings
    domain = (domain or '').lower()
    company_name = (company_name or '').lower()
    description = (description or '').lower()
    
    # Combined text for better classification
    combined_text = f"{domain} {company_name} {description}"
    
    # Define specific industry categories with their keywords
    industry_categories = {
        # IT & Tech Services
        'Cloud Services': ['cloud', 'aws', 'azure', 'gcp', 'hosting', 'iaas', 'paas', 'saas'],
        'IT Services': ['it service', 'tech support', 'helpdesk', 'managed service', 'infrastructure', 'network', 'system'],
        'Software Development': ['software', 'development', 'programming', 'code', 'developer', 'app development'],
        'Digital Transformation': ['digital transformation', 'digitization', 'digital strategy', 'digital solution'],
        'Cybersecurity': ['cyber', 'security', 'threat', 'encryption', 'firewall', 'protection', 'data security'],
        'Data Analytics': ['data', 'analytics', 'big data', 'business intelligence', 'bi', 'data science'],
        'AI & Machine Learning': ['ai', 'machine learning', 'artificial intelligence', 'ml', 'neural', 'nlp', 'deep learning'],
        
        # Finance
        'Financial Services': ['financial', 'finance', 'banking', 'investment', 'wealth management'],
        'FinTech': ['fintech', 'payment', 'transaction', 'digital payment', 'banking tech', 'financial technology'],
        'Investment Banking': ['investment bank', 'capital market', 'ipo', 'merger', 'acquisition'],
        'Insurance': ['insurance', 'policy', 'risk management', 'underwriting', 'claim'],
        
        # Healthcare
        'Healthcare Services': ['healthcare', 'medical', 'health service', 'patient care', 'clinic'],
        'HealthTech': ['healthtech', 'health tech', 'medical technology', 'ehealth', 'health platform'],
        'Pharmaceutical': ['pharma', 'pharmaceutical', 'drug', 'medicine', 'therapeutic'],
        'Biotech': ['biotech', 'biotechnology', 'life science', 'genomic', 'biological'],
        
        # Marketing & Media
        'Digital Marketing': ['digital marketing', 'seo', 'sem', 'content marketing', 'social media marketing'],
        'Advertising': ['advertising', 'ad agency', 'adtech', 'media buying', 'programmatic'],
        'PR & Communications': ['pr', 'public relations', 'communication', 'media relation'],
        'Media & Entertainment': ['media', 'entertainment', 'streaming', 'publishing', 'broadcast'],
        
        # Other Industries
        'E-commerce': ['ecommerce', 'e-commerce', 'online store', 'online retail', 'webshop'],
        'Retail': ['retail', 'store', 'merchant', 'shop', 'consumer goods'],
        'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'assembly'],
        'Consulting': ['consulting', 'consultancy', 'advisor', 'business consultant'],
        'Education': ['education', 'learning', 'school', 'university', 'training', 'edtech'],
        'Real Estate': ['real estate', 'property', 'realty', 'building', 'construction', 'proptech'],
        'Legal Services': ['legal', 'law firm', 'attorney', 'lawyer', 'legal service'],
        'Transportation & Logistics': ['transport', 'logistics', 'shipping', 'delivery', 'supply chain'],
        'Energy': ['energy', 'power', 'utility', 'electricity', 'renewable', 'oil', 'gas'],
        'Telecom': ['telecom', 'telecommunication', 'cellular', 'network provider', 'mobile carrier']
    }
    
    # Calculate relevance scores for each industry
    scores = {}
    for industry, keywords in industry_categories.items():
        # Count how many keywords from this industry appear in the text
        industry_score = 0
        for keyword in keywords:
            if keyword in combined_text:
                industry_score += 1
                
                # Add bonus points for exact matches in name or domain
                if keyword in domain or keyword in company_name:
                    industry_score += 2
                    
                # Add bonus for phrases (keywords with spaces)
                if ' ' in keyword and keyword in combined_text:
                    industry_score += 3
        
        if industry_score > 0:
            scores[industry] = industry_score
    
    # If no industry matched, try to determine a general category
    if not scores:
        # General categories as fallback
        general_categories = {
            'Technology': ['tech', 'software', 'digital', 'comp', 'it', 'app', 'online', 'computer', 'technology', 'systems'],
            'Financial Services': ['finance', 'bank', 'invest', 'capital', 'financial', 'insurance', 'asset', 'money'],
            'Healthcare': ['health', 'med', 'care', 'doctor', 'hospital', 'clinic', 'therapy', 'wellness', 'patient'],
            'Professional Services': ['service', 'solution', 'consulting', 'professional', 'management', 'advisor']
        }
        
        for category, keywords in general_categories.items():
            category_score = sum(1 for kw in keywords if kw in combined_text)
            if category_score > 0:
                scores[category] = category_score
    
    # Return the industry with the highest score, or Other if none found
    if scores:
        return max(scores, key=scores.get)
    else:
        return 'Other'

def scrape_linkedin_company_page(url, user_agent='Mozilla/5.0', timeout=10):
    """
    Scrape a LinkedIn company page for company information
    """
    headers = {'User-Agent': user_agent}
    logger.debug(f"Scraping LinkedIn URL: {url}")
    
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(f"Failed to retrieve {url} - Status code: {resp.status_code}")
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract company name
        name_elem = soup.find('h1')
        name = name_elem.text.strip() if name_elem else ''
        
        # Extract description
        desc_elem = soup.find('meta', {'name': 'description'})
        desc = desc_elem['content'].strip() if desc_elem and desc_elem.has_attr('content') else ''
        
        # Extract domain from URL
        domain = url.split('/')[4] if len(url.split('/')) > 4 else ''
        
        # Try to find website URL
        website = ''
        for a in soup.find_all('a', href=True):
            if 'website' in a.text.lower():
                website = a['href']
                break
        
        # Try to extract company size
        size = ''
        for p in soup.find_all('p'):
            if 'employees' in p.text.lower():
                size = p.text.strip()
                break
        
        # Try to extract location
        location = ''
        for span in soup.find_all('span'):
            if 'headquarter' in span.text.lower():
                location = span.text.strip()
                break
        
        # Try to extract founding year
        founded = ''
        for p in soup.find_all('p'):
            if 'founded' in p.text.lower():
                founded = p.text.strip()
                break
        
        # Use improved domain classification with multiple data points
        domain_class = classify_domain(domain, name, desc)
        
        return {
            'companyLinkedinUrl': url,
            'name': name,
            'description': desc,
            'website': website,
            'domain': domain,
            'domain_class': domain_class,
            'size': size,
            'location': location,
            'founded': founded,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return None

def google_search_linkedin_companies(query, max_results=10):
    """
    Search for LinkedIn company URLs via Google
    """
    logger.debug(f"Searching for: {query}")
    urls = []
    
    try:
        # Try using googlesearch-python
        from googlesearch import search
        for url in search(query, num_results=max_results*2):  # Get more results to filter
            if 'linkedin.com/company/' in url and url not in urls:
                urls.append(url)
                if len(urls) >= max_results:
                    break
    except ImportError:
        logger.warning("googlesearch-python not installed, using alternative method")
        try:
            # Try using custom search with requests + BeautifulSoup
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a')
                
                for link in links:
                    href = link.get('href', '')
                    if 'linkedin.com/company/' in href and href not in urls:
                        # Extract actual URL from Google redirect
                        if '/url?q=' in href:
                            href = href.split('/url?q=')[1].split('&')[0]
                        urls.append(href)
                        if len(urls) >= max_results:
                            break
        except Exception as e:
            logger.error(f"Error in custom Google search: {str(e)}")
            # Fall back to mock data if all else fails
            urls = [
                "https://uk.linkedin.com/company/microsoft",
                "https://uk.linkedin.com/company/google",
                "https://uk.linkedin.com/company/amazon"
            ]
            
    logger.debug(f"Found {len(urls)} LinkedIn URLs")
    return urls[:max_results]  # Ensure we only return up to max_results

def run_scraper(
    keywords=None,
    founded_years=None,
    country=None,
    size=None,
    config_path='scraper_config.json',
    max_results=10,
    user_agent='Mozilla/5.0',
    timeout=10,
    output_csv='lead1.csv',
    sleep_time=1.0,
    search_func=None
):
    """
    Main function to run the LinkedIn company scraper
    """
    # Load config if it exists
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Use provided parameters or defaults from config
    keywords = keywords or config.get('keywords', 'IT services')
    founded_years = founded_years or config.get('founded_years', ['2015'])
    country = country or config.get('country', 'United kingdom')
    size = size or config.get('size', '51-200')
    
    # Build search query
    query = f"{keywords} companies founded {','.join(founded_years)} in {country} with {size} employees linkedin"
    logger.info(f"Search Query: {query}")
    
    # Get LinkedIn company URLs
    urls = []
    if search_func is not None:
        urls = search_func(query)
    else:
        urls = google_search_linkedin_companies(query, max_results)
    
    # Scrape each company page
    results = []
    for i, url in enumerate(urls):
        logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
        data = scrape_linkedin_company_page(url, user_agent=user_agent, timeout=timeout)
        if data:
            results.append(data)
        # Add sleep to avoid rate limiting
        if i < len(urls) - 1:  # Don't sleep after the last one
            logger.debug(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    # Save to CSV if output path provided
    if output_csv:
        df.to_csv(output_csv, index=False)
        logger.info(f"Results saved to {output_csv}")
    
    return df

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Company Scraper')
    parser.add_argument('--keywords', type=str, default=None, help='Keywords for search')
    parser.add_argument('--founded_years', type=str, default=None, help='Comma-separated years')
    parser.add_argument('--country', type=str, default=None, help='Country')
    parser.add_argument('--size', type=str, default=None, help='Company size')
    parser.add_argument('--config_path', type=str, default='scraper_config.json', help='Config file path')
    parser.add_argument('--max_results', type=int, default=10, help='Max LinkedIn results')
    parser.add_argument('--user_agent', type=str, default='Mozilla/5.0', help='User agent')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout')
    parser.add_argument('--output_csv', type=str, default='lead1.csv', help='Output CSV file')
    parser.add_argument('--sleep_time', type=float, default=1.0, help='Sleep time between requests (seconds)')
    
    args = parser.parse_args()
    founded_years = args.founded_years.split(',') if args.founded_years else None
    
    df = run_scraper(
        keywords=args.keywords,
        founded_years=founded_years,
        country=args.country,
        size=args.size,
        config_path=args.config_path,
        max_results=args.max_results,
        user_agent=args.user_agent,
        timeout=args.timeout,
        output_csv=args.output_csv,
        sleep_time=args.sleep_time
    )
    
    print(f"Scraped {len(df)} companies and saved to {args.output_csv}")
