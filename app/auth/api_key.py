from fastapi import Header, HTTPException, status

VALID_API_KEY="narasimha_9963111874"

def verify_api_key(x_api_key: str = Header(...)):

    if (x_api_key != VALID_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api key"
        )
    
    return x_api_key