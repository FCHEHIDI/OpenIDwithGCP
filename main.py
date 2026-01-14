from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import status
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

# Charger les variables d'environnement
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
SECRET_KEY = os.getenv("SECRET_KEY", "changez-cette-cle-secrete")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET doivent être définis dans .env")

# Créer l'application FastAPI
app = FastAPI(
    title="OpenID Connect avec Google",
    description="Authentification OpenID Connect utilisant Google OAuth2",
    version="1.0.0"
)

# Configuration des templates
templates = Jinja2Templates(directory="templates")

# Ajouter le middleware de session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configurer OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Security pour JWT
security = HTTPBearer()


# Fonctions JWT
def create_jwt_token(user_data: dict) -> str:
    """Créer un JWT contenant les données utilisateur"""
    to_encode = user_data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> dict:
    """Vérifier et décoder un JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")


def get_current_user(request: Request) -> dict:
    """Dépendance pour extraire l'utilisateur du JWT depuis les cookies"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié - JWT manquant")
    return verify_jwt_token(token)


@app.get("/")
async def home(request: Request):
    """Page d'accueil avec interface HTML"""
    # Vérifier si un JWT est présent dans les cookies
    token = request.cookies.get("access_token")
    user = None
    
    if token:
        try:
            user = verify_jwt_token(token)
        except HTTPException:
            pass  # Token invalide, utilisateur non connecté
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user
    })


@app.get("/auth/login")
async def login(request: Request):
    """Initier le flux d'authentification OpenID Connect avec Google"""
    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """
    Callback après authentification Google.
    Récupère le token et crée un JWT.
    """
    try:
        # Échanger le code d'autorisation contre un token
        token = await oauth.google.authorize_access_token(request)
        
        # Récupérer les informations utilisateur via OpenID Connect
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Impossible de récupérer les informations utilisateur")
        
        # Créer les données utilisateur pour le JWT
        user_data = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'sub': user_info.get('sub'),
            'email_verified': user_info.get('email_verified')
        }
        
        # Créer un JWT
        jwt_token = create_jwt_token(user_data)
        
        # Rediriger vers la page d'accueil avec le JWT dans un cookie
        response = RedirectResponse(url='/')
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,  # Protection XSS
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax" # Protection CSRF
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'authentification: {str(e)}")


@app.get("/auth/logout")
async def logout():
    """Déconnecter l'utilisateur en supprimant le JWT"""
    response = JSONResponse({
        "message": "Déconnexion réussie",
        "authenticated": False
    })
    response.delete_cookie("access_token")
    return response


@app.get("/api/user")
async def get_user(user: dict = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur connecté (protégé par JWT)"""
    return user


@app.get("/api/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """Exemple de route protégée nécessitant un JWT valide"""
    return {
        "message": "Accès autorisé à cette ressource protégée",
        "user_email": user.get('email'),
        "token_expires_at": datetime.fromtimestamp(user.get('exp')).isoformat()
    }


@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
