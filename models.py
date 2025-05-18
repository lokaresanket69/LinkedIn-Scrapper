from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class Company(db.Model):
    """Model for storing LinkedIn company data"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    domain = db.Column(db.String(100))
    domain_class = db.Column(db.String(50))
    size = db.Column(db.String(100))
    location = db.Column(db.String(255))
    founded = db.Column(db.String(100))
    keywords = db.Column(db.Text)
    technologies = db.Column(db.Text)
    sentiment = db.Column(db.String(20))
    description_length = db.Column(db.Integer)
    scraped_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    def to_dict(self):
        """Convert Company object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'website': self.website,
            'companyLinkedinUrl': self.linkedin_url,
            'domain': self.domain,
            'domain_class': self.domain_class,
            'size': self.size,
            'location': self.location,
            'founded': self.founded,
            'keywords': self.keywords,
            'technologies': self.technologies,
            'sentiment': self.sentiment,
            'description_length': self.description_length,
            'scraped_at': self.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if self.scraped_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Company object from dictionary"""
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            website=data.get('website', ''),
            linkedin_url=data.get('companyLinkedinUrl', ''),
            domain=data.get('domain', ''),
            domain_class=data.get('domain_class', ''),
            size=data.get('size', ''),
            location=data.get('location', ''),
            founded=data.get('founded', ''),
            keywords=data.get('keywords', ''),
            technologies=data.get('technologies', ''),
            sentiment=data.get('sentiment', ''),
            description_length=data.get('description_length', 0),
            scraped_at=datetime.now()
        )