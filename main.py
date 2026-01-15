from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse, Response, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import status
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import json

# Charger les variables d'environnement
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Utiliser REDIRECT_URI de l'environnement, sinon localhost pour dev
GOOGLE_REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
# Utiliser JWT_SECRET_KEY ou SECRET_KEY pour compatibilité
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET doivent être définis dans .env")

if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY ou SECRET_KEY doit être défini dans les variables d'environnement")

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

# Base de données en mémoire (à remplacer par une vraie DB en production)
# Structure: {sub: {email, name, picture, email_verified, updated_at}}
users_db = {}


# Fonctions JWT
def create_jwt_token(user_sub: str) -> str:
    """Créer un JWT contenant uniquement le sub (identifiant utilisateur)"""
    to_encode = {'sub': user_sub}
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


def save_user_to_db(user_data: dict) -> None:
    """Sauvegarder ou mettre à jour les données utilisateur en base de données"""
    sub = user_data.get('sub')
    if not sub:
        raise ValueError("Le 'sub' est requis pour sauvegarder un utilisateur")
    
    # Upsert: créer ou mettre à jour
    users_db[sub] = {
        'email': user_data.get('email'),
        'name': user_data.get('name'),
        'picture': user_data.get('picture'),
        'email_verified': user_data.get('email_verified'),
        'updated_at': datetime.utcnow().isoformat()
    }


def get_user_from_db(sub: str) -> dict:
    """Récupérer les données utilisateur depuis la base de données"""
    user = users_db.get(sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    # Ajouter le sub aux données retournées
    return {**user, 'sub': sub}


def get_current_user(request: Request) -> dict:
    """Dépendance pour extraire l'utilisateur du JWT et récupérer ses données depuis la DB"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifié - JWT manquant")
    
    # Vérifier le JWT (contient uniquement le sub)
    jwt_payload = verify_jwt_token(token)
    user_sub = jwt_payload.get('sub')
    
    if not user_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide: 'sub' manquant")
    
    # Récupérer les données complètes depuis la DB
    user_data = get_user_from_db(user_sub)
    
    # Ajouter les infos du JWT (exp, iat) aux données utilisateur
    user_data['exp'] = jwt_payload.get('exp')
    user_data['iat'] = jwt_payload.get('iat')
    
    return user_data


@app.get("/")
async def home(request: Request):
    """Page d'accueil avec interface HTML"""
    # Vérifier si un JWT est présent dans les cookies
    token = request.cookies.get("access_token")
    user = None
    
    if token:
        try:
            jwt_payload = verify_jwt_token(token)
            user_sub = jwt_payload.get('sub')
            if user_sub:
                user = get_user_from_db(user_sub)
        except (HTTPException, Exception):
            pass  # Token invalide ou utilisateur non trouvé, utilisateur non connecté
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user
    })


@app.get("/auth/login")
async def login(request: Request):
    """Initier le flux d'authentification OpenID Connect avec Google"""
    redirect_uri = GOOGLE_REDIRECT_URI
    # prompt='select_account' : force l'utilisateur à choisir un compte à chaque connexion
    # Utile pour les démos ou si plusieurs utilisateurs partagent le même navigateur
    return await oauth.google.authorize_redirect(
        request, 
        redirect_uri,
        prompt='select_account'  # Force l'affichage du sélecteur de compte Google
    )


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
        
        # Préparer les données utilisateur complètes
        user_data = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'sub': user_info.get('sub'),
            'email_verified': user_info.get('email_verified')
        }
        
        # Sauvegarder les données complètes en base de données
        save_user_to_db(user_data)
        
        # Créer un JWT contenant uniquement le sub
        jwt_token = create_jwt_token(user_data['sub'])
        
        # Rediriger vers la page d'accueil avec le JWT dans un cookie sécurisé
        response = RedirectResponse(url='/')
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,  # Protection XSS : JavaScript ne peut pas accéder au cookie
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"  # Protection CSRF partielle + UX optimale
                           # Lax : bloque POST/PUT/DELETE cross-site (attaques CSRF)
                           # tout en autorisant la navigation GET légitime (OAuth callback)
                           # Alternative : "strict" (plus sûr mais casse OAuth/UX)
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
async def get_user(request: Request, user: dict = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur connecté (protégé par JWT)"""
    user_json = json.dumps(user, indent=2, ensure_ascii=False)
    return templates.TemplateResponse("user.html", {
        "request": request,
        "user_json": user_json
    })


@app.get("/api/protected")
async def protected_route(request: Request, user: dict = Depends(get_current_user)):
    """Exemple de route protégée nécessitant un JWT valide"""
    data = {
        "message": "Accès autorisé à cette ressource protégée",
        "user_email": user.get('email'),
        "token_expires_at": datetime.fromtimestamp(user.get('exp')).isoformat()
    }
    data_json = json.dumps(data, indent=2, ensure_ascii=False)
    return templates.TemplateResponse("protected.html", {
        "request": request,
        "data_json": data_json
    })


@app.get("/health")
async def health_check(request: Request):
    """Endpoint de vérification de santé"""
    data = {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    data_json = json.dumps(data, indent=2, ensure_ascii=False)
    return templates.TemplateResponse("health.html", {
        "request": request,
        "data_json": data_json
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
