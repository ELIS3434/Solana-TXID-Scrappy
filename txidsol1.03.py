from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm  # Import tqdm for the progress bar

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    """Set up the Chrome WebDriver with options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode if needed
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Specify the correct path to the Chrome binary
    chrome_options.binary_location = "/usr/bin/google-chrome"  # Adjust this path as needed

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def fetch_transaction_hashes(driver, url):
    """Fetch transaction hashes from the given URL."""
    try:
        logging.info(f"Accessing URL: {url}")
        driver.get(url)

        # Wait until the transaction elements are loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/transaction/']"))
        )

        # Find all transaction hash elements
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/transaction/']")
        transaction_hashes = [element.get_attribute('href').split('/')[-1] for element in elements]

        logging.info(f"Found {len(transaction_hashes)} transaction hashes on this page.")
        return transaction_hashes

    except Exception as e:
        logging.error(f"Error fetching transaction hashes: {e}")
        return []

def save_to_file(hashes, filename):
    """Save the list of hashes to a file."""
    try:
        with open(filename, 'w') as file:
            file.write('\n'.join(hashes))
        logging.info(f"Saved {len(hashes)} transaction hashes to '{filename}'")
    except Exception as e:
        logging.error(f"Error saving to file: {e}")

def main(url, output_file, max_txids):
    """ Main function to execute the script."""
    driver = None
    all_transaction_hashes = []
    page_number = 1
    
    try:
        driver = setup_driver()
        
        # Initialize tqdm progress bar
        with tqdm(total=max_txids, desc="Fetching TXIDs", unit="TXID") as pbar:
            while len(all_transaction_hashes) < max_txids:
                current_url = f"{url}?page={page_number}"
                transaction_hashes = fetch_transaction_hashes(driver, current_url)

                if not transaction_hashes:
                    logging.warning("No more transaction hashes found or reached the end of available pages.")
                    break
                
                all_transaction_hashes.extend(transaction_hashes)
                pbar.update(len(transaction_hashes))  # Update progress bar
                page_number += 1

        # Save the collected hashes, ensuring we only save up to the specified max_txids
        save_to_file(all_transaction_hashes[:max_txids], output_file)

    finally:
        if driver:
            driver.quit()  # Ensure the driver is closed after use

if __name__ == "__main__":
    url = "https://solanabeach.io/transactions"  # Base URL for transactions
    
    # User input for the number of TXIDs to fetch
    max_txids = int(input("Enter the number of TXIDs to fetch (up to 1000): "))
    if max_txids > 1000:
        print("The maximum number of TXIDs you can fetch is 1000. Setting to 1000.")
        max_txids = 1000

    # User input for the output file name
    output_file = input("Enter the output file name (e.g., txidsol01.txt): ")  # Output file name
    
    main(url, output_file, max_txids)