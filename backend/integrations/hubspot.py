# hubspot.py

import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
import hashlib
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis


CLIENT_ID = '9cfb624d-e3af-4dfa-8ac3-311f3b65718a'
CLIENT_SECRET = 'd8a7c939-c249-4921-86c9-8d6b70530610'
encoded_client_id_secret = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()

REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=tickets%20e-commerce%20crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.custom.read%20crm.objects.custom.write%20crm.objects.companies.write%20media_bridge.read%20crm.objects.companies.read%20crm.objects.deals.read%20crm.objects.deals.write%20crm.objects.quotes.write%20crm.objects.quotes.read%20crm.objects.line_items.read%20crm.objects.line_items.write%20crm.objects.goals.read'

async def authorize_hubspot(user_id, org_id):

    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')

    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode('utf-8'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')

    auth_url = f'{authorization_url}&state={encoded_state}&code_challenge={code_challenge}&code_challenge_method=S256'
    await asyncio.gather(
        add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600),
        add_key_value_redis(f'hubspot_verifier:{org_id}:{user_id}', code_verifier, expire=600),
    )

    return auth_url

async def oauth2callback_hubspot(request: Request):

    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state, code_verifier = await asyncio.gather(
        get_value_redis(f'hubspot_state:{org_id}:{user_id}'),
        get_value_redis(f'hubspot_verifier:{org_id}:{user_id}'),
    )

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code,
                }, 
                headers={
                    'Authorization': f'Basic {encoded_client_id_secret}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
            delete_key_redis(f'hubspot_verifier:{org_id}:{user_id}'),
        )

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')


    return credentials

async def create_integration_item_metadata_query_object(response_json: dict) -> IntegrationItem:
    print(response_json)
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None),
        name=response_json.get('firstname', None) + " " + response_json.get('lastname', None),
        email=response_json.get('email', None),
        hs_object_id=response_json.get('hs_object_id', None),
        create_date=response_json.get('createdate', None)
    )

    return integration_item_metadata

async def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    print(response_json)
    integration_item_metadata = IntegrationItem(
        name=response_json.get('firstname', None) + " " + response_json.get('lastname', None),
        email=response_json.get('email', None),
    )

    return integration_item_metadata


async def fetch_items(
    access_token: str, url: str, aggregated_response: list, offset=None
) -> dict:
    """Fetching the list of contacts"""
    
    params = {'offset': offset} if offset is not None else {}
    headers = {'Authorization': f'Bearer {access_token}'}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    if response.status_code == 200:
        
        results = response.json()

        for result in results["results"]:
            properties = result.get("properties", {})
            aggregated_response.append(properties)

    else:
        print(f"Error: {response.status_code}, {response.text}")


#######################################################################################################################
    
# TO-DO

async def get_items_hubspot_query(credentials, query_user_email):

    list_of_integration_item_metadata_query = []
    list_of_responses = []

    credentials = json.loads(credentials)
    url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    list_of_integration_item_metadata_query = []
    list_of_responses = []

    await fetch_items(credentials.get('access_token'), url, list_of_responses)

    found = False
    for response in list_of_responses:

        if response['email'] == query_user_email:
            found = True
            list_of_integration_item_metadata_query.append(

            # append only if response equals query_user_email
            await create_integration_item_metadata_query_object(response)
        )

    if found:
        print(f'list_of_integration_item_metadata: {list_of_integration_item_metadata_query}')
        return list_of_integration_item_metadata_query
    else:
        error_message = f'No user with the email {query_user_email} exists in our database'
        raise HTTPException(status_code=404, detail=error_message)

#######################################################################################################################
    
async def get_items_hubspot(credentials):
    
    credentials = json.loads(credentials)
    url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    list_of_integration_item_metadata = []
    list_of_responses = []

    await fetch_items(credentials.get('access_token'), url, list_of_responses)


    for response in list_of_responses:
        list_of_integration_item_metadata.append(
            await create_integration_item_metadata_object(response)
        )

    print(f'list_of_integration_item_metadata: {list_of_integration_item_metadata}')
    return list_of_integration_item_metadata




    