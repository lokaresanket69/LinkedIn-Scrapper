import pandas as pd
import nltk
import logging
import re
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Download necessary NLTK resources if they don't exist
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading required NLTK resources...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Domain-specific stopwords
DOMAIN_STOPWORDS = {
    'company', 'business', 'service', 'services', 'solution', 'solutions',
    'provide', 'provides', 'provider', 'industry', 'industries', 'product',
    'products', 'client', 'clients', 'customer', 'customers', 'team',
    'year', 'years', 'experience', 'professional', 'professionals',
    'work', 'working', 'offer', 'offers', 'offering', 'offerings',
    'help', 'helping', 'helps', 'support', 'supporting'
}

def preprocess_text(text):
    """
    Preprocess text for NLP analysis
    """
    if not isinstance(text, str) or not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs, email addresses, and special characters
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'\S*@\S*\s?', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Get English stopwords and combine with domain-specific ones
    stop_words = set(stopwords.words('english')).union(DOMAIN_STOPWORDS)
    
    # Remove stopwords and short words
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return tokens

def extract_keywords(text, top_n=10):
    """
    Extract the most common keywords from text
    """
    tokens = preprocess_text(text)
    
    # Count word frequencies
    word_freq = Counter(tokens)
    
    # Get the top N keywords
    top_keywords = word_freq.most_common(top_n)
    
    # Format as a comma-separated string
    if top_keywords:
        return ", ".join([word for word, _ in top_keywords])
    else:
        return ""

def extract_entities(text):
    """
    Extract entities like technologies, locations, etc.
    This is a simple implementation - a more advanced version 
    would use named entity recognition (NER)
    """
    # Tech keywords to look for
    tech_keywords = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'data science',
        'cloud', 'aws', 'azure', 'gcp', 'google cloud', 'blockchain', 'iot',
        'internet of things', 'big data', 'analytics', 'devops', 'saas',
        'software as a service', 'python', 'java', 'javascript', 'react',
        'angular', 'node', 'mobile', 'web development', 'cybersecurity',
        'security', 'automation', 'fintech', 'healthtech', 'edtech', 'proptech'
    ]
    
    entities = []
    lower_text = text.lower() if isinstance(text, str) else ""
    
    # Look for tech keywords
    for keyword in tech_keywords:
        if keyword in lower_text:
            entities.append(keyword)
    
    return ", ".join(entities) if entities else ""

def analyze_sentiment(text):
    """
    Perform a very basic sentiment analysis
    Returns: positive, negative, or neutral
    """
    if not isinstance(text, str) or not text:
        return "neutral"
    
    # List of positive and negative words
    positive_words = [
        'innovative', 'leading', 'success', 'successful', 'growth', 'growing',
        'best', 'excellent', 'outstanding', 'award', 'winning', 'top', 'premier',
        'trusted', 'advanced', 'expert', 'specialized', 'quality', 'efficient',
        'effective', 'proven', 'reliable', 'seamless', 'cutting-edge', 'state-of-the-art'
    ]
    
    negative_words = [
        'challenge', 'difficult', 'problem', 'issue', 'struggle', 'fail',
        'limitation', 'constraint', 'weakness', 'disadvantage', 'drawback',
        'decline', 'decrease', 'reduce', 'loss', 'costly', 'expensive'
    ]
    
    # Count occurrences
    lower_text = text.lower()
    positive_count = sum(1 for word in positive_words if word in lower_text)
    negative_count = sum(1 for word in negative_words if word in lower_text)
    
    # Determine sentiment
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def process_descriptions(df):
    """
    Process company descriptions using NLP techniques
    """
    logger.info("Processing company descriptions with NLP...")
    
    if 'description' not in df.columns:
        logger.warning("No 'description' column found in DataFrame")
        return df
    
    # Apply NLP processing to each description
    df['keywords'] = df['description'].apply(extract_keywords)
    df['technologies'] = df['description'].apply(extract_entities)
    df['sentiment'] = df['description'].apply(analyze_sentiment)
    
    # Calculate description length as a feature
    df['description_length'] = df['description'].apply(lambda x: len(x) if isinstance(x, str) else 0)
    
    logger.info("NLP processing completed")
    return df

if __name__ == "__main__":
    # Test the NLP processor
    test_text = """
    Our company is a leading provider of artificial intelligence and machine learning 
    solutions for the healthcare industry. Based in London, we've been helping hospitals 
    and clinics improve patient outcomes since 2015. Our team of experts specializes in 
    predictive analytics and cloud-based systems using AWS and Azure.
    """
    
    print("Test text:", test_text)
    print("Keywords:", extract_keywords(test_text))
    print("Technologies:", extract_entities(test_text))
    print("Sentiment:", analyze_sentiment(test_text))
