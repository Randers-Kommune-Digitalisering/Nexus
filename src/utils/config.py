import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'Pod name not set')

# NEXUS
NEXUS_URL = os.environ["NEXUS_URL"].strip()
NEXUS_CLIENT_ID = os.environ["NEXUS_CLIENT_ID"].strip()
NEXUS_CLIENT_SECRET = os.environ["NEXUS_CLIENT_SECRET"].strip()
NEXUS_TOKEN_ROUTE = os.environ["NEXUS_TOKEN_ROUTE"].strip()

# KP
KP_URL = os.environ["KP_URL"].strip()
KP_USERNAME = os.environ["KP_USERNAME"].strip()
KP_PASSWORD = os.environ["KP_PASSWORD"].strip()

# SBSYS
SBSYS_URL = os.environ["SBSYS_URL"].strip()
SBSIP_URL = os.environ["SBSIP_URL"].strip()
SBSIP_MASTER_URL = os.environ["SBSIP_MASTER_URL"].strip()

# Personalesager
SBSIP_PSAG_CLIENT_ID = os.environ["SBSIP_PSAG_CLIENT_ID"].strip()
SBSIP_PSAG_CLIENT_SECRET = os.environ["SBSIP_PSAG_CLIENT_SECRET"].strip()
SBSYS_PSAG_USERNAME = os.environ["SBSYS_PSAG_USERNAME"].strip()
SBSYS_PSAG_PASSWORD = os.environ["SBSYS_PSAG_PASSWORD"].strip()

# Korsel
SBSIP_CLIENT_ID = os.environ["SBSIP_CLIENT_ID"].strip()
SBSIP_CLIENT_SECRET = os.environ["SBSIP_CLIENT_SECRET"].strip()
SBSYS_USERNAME = os.environ["SBSYS_USERNAME"].strip()
SBSYS_PASSWORD = os.environ["SBSYS_PASSWORD"].strip()

# Browserless
BROWSERLESS_URL = os.environ["BROWSERLESS_URL"].strip()
BROWSERLESS_CLIENT_ID = os.environ["BROWSERLESS_CLIENT_ID"].strip()
BROWSERLESS_CLIENT_SECRET = os.environ["BROWSERLESS_CLIENT_SECRET"].strip()

# SD
SD_URL = os.getenv("SD_URL", "https://sd-mock.com").strip()
SD_USERNAME = os.getenv("SD_USERNAME", "sd-test-user").strip()
SD_PASSWORD = os.getenv("SD_PASSWORD", "sd-test-pass").strip()
SD_INST_ID = os.getenv("SD_INST_ID", "sd-test-inst-id").strip()
SD_BASIC_AUTH = os.getenv("SD_BASIC_AUTH", "sd-test-basic-auth").strip()

# Azure
AZURE_TENANTID = os.environ['AZURE_TENANTID'].rstrip()