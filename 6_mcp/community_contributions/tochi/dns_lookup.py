from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# Load the environment variables
load_dotenv()
API_KEY = os.getenv("API_NINJA")

if not API_KEY:
    raise ValueError("Unable to fetch the API key")
else:
    print("API Key loaded")

# Database setup
DB_PATH = Path("dns_records.db")


def init_database():
    """Initialize the SQLite database and create table if not exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dns_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL UNIQUE,
            expiry_date INTEGER NOT NULL,
            expiry_date_formatted TEXT,
            registrar TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    conn.commit()
    conn.close()


# Initialize database on module load
init_database()


def format_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y at %I:%M:%S %p')


class DNS(BaseModel):
    domain: str
    dns_data: dict = {}

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, domain: str, **kwargs):
        super().__init__(domain=domain, **kwargs)
        self._fetch_dns_records()

    def _fetch_dns_records(self):
        """Fetch DNS records from API (called once during initialization)"""
        api_url = f"https://api.api-ninjas.com/v1/whois?domain={self.domain}"
        try:
            response = requests.get(api_url, headers={"X-Api-Key": API_KEY})
            if response.status_code == requests.codes.ok:
                self.dns_data = response.json()
                print(f"DNS records fetched successfully for {self.domain}")
            else:
                print(f"Error: {response.status_code}, {response.text}")
                self.dns_data = {}
        except Exception as e:
            print(f"Failed to fetch DNS records: {e}")
            self.dns_data = {}

    def get_registrar(self):
        try:
            return {"status": True, "registrar": self.dns_data["registrar"]}
        except KeyError:
            return {
                "status": False,
                "error": "Registrar information not available in DNS records"
            }
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve registrar: {e}"
            }

    def get_creation_date(self):
        try:
            creation_date = format_date(self.dns_data["creation_date"])
            return {"status": True, "creation_date": creation_date}
        except KeyError:
            return {
                "status": False,
                "error": "Creation date not available in DNS records"
            }
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve creation date: {e}"
            }

    def get_expiry_date(self):
        try:
            expiration_date = format_date(self.dns_data["expiration_date"])
            return {"status": True, "expiration_date": expiration_date}
        except KeyError:
            return {
                "status": False,
                "error": "Expiration date not available in DNS records"
            }
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve expiration date: {e}"
            }

    def get_name_servers(self):
        try:
            ns = self.dns_data["name_servers"]
            return {"status": True, "name_servers": ns}
        except KeyError:
            return {
                "status": False,
                "error": "Name servers not available in DNS records"
            }
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve name servers: {e}"
            }

    def save_dns_search(self):
        """Save DNS search results to SQLite database"""
        try:
            if not self.dns_data:
                return {
                    "status": False,
                    "error": "No DNS data available to save"
                }
            
            # Extract required fields
            expiry_date = self.dns_data.get("expiration_date")
            registrar = self.dns_data.get("registrar", "Unknown")
            
            if not expiry_date:
                return {
                    "status": False,
                    "error": "Expiration date not available in DNS data"
                }
            
            # Format the expiry date for display
            expiry_date_formatted = format_date(expiry_date)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Insert or update the record
            cursor.execute("""
                INSERT INTO dns_records (domain, expiry_date, expiry_date_formatted, registrar)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    expiry_date = excluded.expiry_date,
                    expiry_date_formatted = excluded.expiry_date_formatted,
                    registrar = excluded.registrar,
                    updated_at = strftime('%s', 'now')
            """, (self.domain, expiry_date, expiry_date_formatted, registrar))
            
            conn.commit()
            conn.close()
            
            return {
                "status": True,
                "message": f"DNS record for {self.domain} saved successfully",
                "domain": self.domain,
                "expiry_date": expiry_date_formatted
            }
            
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to save DNS record: {e}"
            }

    @staticmethod
    def watch_dns():
        """Retrieve DNS records expiring within 3 months from today"""
        try:
            # Calculate timestamp for 3 months from now
            three_months_later = datetime.now() + timedelta(days=90)
            three_months_timestamp = int(three_months_later.timestamp())
            
            # Current timestamp
            now_timestamp = int(datetime.now().timestamp())
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Query records expiring within 3 months
            cursor.execute("""
                SELECT domain, expiry_date, expiry_date_formatted, registrar, 
                       datetime(created_at, 'unixepoch') as created_at,
                       datetime(updated_at, 'unixepoch') as updated_at
                FROM dns_records
                WHERE expiry_date <= ? AND expiry_date >= ?
                ORDER BY expiry_date ASC
            """, (three_months_timestamp, now_timestamp))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return {
                    "status": True,
                    "message": "No domains expiring within 3 months",
                    "records": []
                }
            
            # Format results
            formatted_records = []
            for record in records:
                days_until_expiry = (record[1] - now_timestamp) // (24 * 3600)
                formatted_records.append({
                    "domain": record[0],
                    "expiry_date": record[2],
                    "expiry_timestamp": record[1],
                    "days_until_expiry": days_until_expiry,
                    "registrar": record[3],
                    "tracked_since": record[4],
                    "last_updated": record[5]
                })
            
            return {
                "status": True,
                "message": f"Found {len(formatted_records)} domain(s) expiring within 3 months",
                "records": formatted_records
            }
            
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve DNS records: {e}"
            }

    @staticmethod
    def get_all_tracked_domains():
        """Get all tracked domains from database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT domain, expiry_date_formatted, registrar,
                       datetime(created_at, 'unixepoch') as created_at,
                       datetime(updated_at, 'unixepoch') as updated_at
                FROM dns_records
                ORDER BY expiry_date ASC
            """)
            
            records = cursor.fetchall()
            conn.close()
            
            formatted_records = [{
                "domain": r[0],
                "expiry_date": r[1],
                "registrar": r[2],
                "tracked_since": r[3],
                "last_updated": r[4]
            } for r in records]
            
            return {
                "status": True,
                "total_domains": len(formatted_records),
                "records": formatted_records
            }
            
        except Exception as e:
            return {
                "status": False,
                "error": f"Failed to retrieve tracked domains: {e}"
            }

    def get_all_info(self):
        """Get all DNS information at once"""
        return {
            "domain": self.domain,
            "registrar": self.get_registrar(),
            "creation_date": self.get_creation_date(),
            "expiration_date": self.get_expiry_date(),
            "name_servers": self.get_name_servers()
        }
