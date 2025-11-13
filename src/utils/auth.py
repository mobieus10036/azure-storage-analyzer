"""
Utility module for Azure authentication and credential management.
"""

import logging
from typing import Optional
from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential
from azure.core.credentials import TokenCredential
from azure.core.exceptions import ClientAuthenticationError

logger = logging.getLogger(__name__)


def get_azure_credential() -> TokenCredential:
    """
    Get Azure credential using Azure CLI first, then DefaultAzureCredential.
    
    This tries multiple authentication methods in order:
    1. Azure CLI (az login) - PREFERRED for local development
    2. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
    3. Visual Studio Code
    4. Azure PowerShell
    
    Returns:
        TokenCredential: Azure credential object
        
    Raises:
        ClientAuthenticationError: If no valid authentication method is found
    """
    try:
        # Try Azure CLI first (most common for local dev)
        try:
            cli_credential = AzureCliCredential()
            # Test the credential by requesting a token
            cli_credential.get_token("https://management.azure.com/.default")
            logger.info("Successfully obtained Azure CLI credentials")
            return cli_credential
        except Exception as cli_error:
            logger.debug(f"Azure CLI authentication not available: {cli_error}")
            
        # Fallback to DefaultAzureCredential with specific exclusions to avoid errors
        credential = DefaultAzureCredential(
            exclude_managed_identity_credential=True,  # Exclude to avoid ManagedIdentity errors
            exclude_workload_identity_credential=True,  # Exclude to avoid workload identity errors
        )
        logger.info("Successfully obtained Azure credentials via DefaultAzureCredential")
        return credential
    except Exception as e:
        logger.error(f"Failed to obtain Azure credentials: {e}")
        raise ClientAuthenticationError(
            "Unable to authenticate with Azure. "
            "Please ensure you're logged in via Azure CLI (az login) "
            "or have configured environment variables."
        ) from e


def get_cli_credential() -> TokenCredential:
    """
    Get Azure CLI credential specifically.
    
    Returns:
        TokenCredential: Azure CLI credential object
        
    Raises:
        ClientAuthenticationError: If Azure CLI is not available or not logged in
    """
    try:
        credential = AzureCliCredential()
        logger.info("Successfully obtained Azure CLI credentials")
        return credential
    except Exception as e:
        logger.error(f"Failed to obtain Azure CLI credentials: {e}")
        raise ClientAuthenticationError(
            "Azure CLI authentication failed. "
            "Please run 'az login' to authenticate."
        ) from e


def validate_credential(credential: TokenCredential, scope: str = "https://management.azure.com/.default") -> bool:
    """
    Validate that a credential can obtain a token.
    
    Args:
        credential: The credential to validate
        scope: The scope to request a token for
        
    Returns:
        bool: True if credential is valid, False otherwise
    """
    try:
        token = credential.get_token(scope)
        if token and token.token:
            logger.debug("Credential validation successful")
            return True
        return False
    except Exception as e:
        logger.warning(f"Credential validation failed: {e}")
        return False
