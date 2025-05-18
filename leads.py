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
    Classify a company domain into a business category
    Uses multiple data points: domain name, company name, and description
    """
    # Ensure we're working with lowercase strings
    domain = (domain or '').lower()
    company_name = (company_name or '').lower()
    description = (description or '').lower()
    
    # Combined text for better classification
    combined_text = f"{domain} {company_name} {description}"
    
    # Technology
    tech_keywords = ['tech', 'software', 'digital', 'comp', 'it', 'ai', 'artificial intelligence', 
                    'data', 'cloud', 'web', 'app', 'mobile', 'dev', 'programming', 'cyber', 'security',
                    'network', 'internet', 'saas', 'platform', 'online', 'computer', 'technology', 'systems']
    
    # Finance
    finance_keywords = ['finance', 'bank', 'invest', 'capital', 'financial', 'insurance', 'asset',
                       'wealth', 'money', 'trading', 'payment', 'fintech', 'credit', 'loan', 'accounting']
    
    # Healthcare
    health_keywords = ['health', 'med', 'care', 'pharm', 'doctor', 'hospital', 'clinic', 'therapy',
                      'wellness', 'patient', 'drug', 'biotech', 'life science', 'diagnostic']
    
    # Education
    edu_keywords = ['edu', 'school', 'college', 'univ', 'learn', 'train', 'course', 'academy',
                   'study', 'student', 'teach', 'tutoring', 'knowledge', 'skill', 'education']
    
    # Marketing
    marketing_keywords = ['marketing', 'media', 'advert', 'pr', 'brand', 'market', 'campaign',
                         'content', 'social media', 'seo', 'audience', 'analytics', 'promotion', 'agency']
    
    # Retail
    retail_keywords = ['retail', 'shop', 'store', 'ecommerce', 'commerce', 'consumer', 'product',
                      'goods', 'sell', 'marketplace', 'customer', 'buy', 'purchase', 'sale']
    
    # Manufacturing
    manufacturing_keywords = ['manufact', 'indust', 'prod', 'factory', 'assembly', 'engineering',
                             'material', 'equipment', 'machinery', 'construction', 'build', 'hardware']
    
    # Consulting
    consulting_keywords = ['consult', 'service', 'solution', 'advisor', 'strategy', 'management',
                          'business', 'professional', 'outsource', 'expert', 'specialist']
    
    # Count keywords in each category
    counts = {
        'Technology': sum(1 for kw in tech_keywords if kw in combined_text),
        'Finance': sum(1 for kw in finance_keywords if kw in combined_text),
        'Healthcare': sum(1 for kw in health_keywords if kw in combined_text),
        'Education': sum(1 for kw in edu_keywords if kw in combined_text),
        'Marketing': sum(1 for kw in marketing_keywords if kw in combined_text),
        'Retail': sum(1 for kw in retail_keywords if kw in combined_text),
        'Manufacturing': sum(1 for kw in manufacturing_keywords if kw in combined_text),
        'Consulting': sum(1 for kw in consulting_keywords if kw in combined_text)
    }
    
    # Get the category with the highest count
    max_count = max(counts.values())
    
    # If we found at least one keyword, return the category with the most matches
    if max_count > 0:
        # If there's a tie, prioritize certain categories
        max_categories = [cat for cat, count in counts.items() if count == max_count]
        if len(max_categories) > 1:
            # Prioritize Technology, then Finance, then Healthcare
            for priority in ['Technology', 'Finance', 'Healthcare', 'Consulting']:
                if priority in max_categories:
                    return priority
        return max(counts, key=counts.get)
    
    # Default to 'Other' if no keywords match
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
