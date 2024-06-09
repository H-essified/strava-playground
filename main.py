from stravalib.client import Client
import requests


client = Client()

# Generate authorisation URL if not already authorised
# authorize_url = client.authorization_url(
#     client_id=128202, redirect_uri="http://localhost:8282/authorized"
# )
# print(authorize_url)

code = '5e7c19e74ab6f0300679edf7d0561bcb7f527d64'

# Setup tokens for client
token_response = client.exchange_code_for_token(
    client_id=128202, client_secret="911cdb44473e56a6b087195e89281dee02ad74d2", code=code
)
client.access_token = token_response["access_token"]
client.refresh_token = token_response["refresh_token"]
client.token_expires_at = token_response["expires_at"]

# Pull out athlete information
athlete = client.get_athlete()
print(athlete)
print('mark')