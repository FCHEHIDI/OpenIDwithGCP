from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer

# Charger les variables d'environnement
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
SECRET_KEY = os.getenv("SECRET_KEY", "changez-cette-cle-secrete")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET doivent être définis dans .env")

# Créer l'application FastAPI
app = FastAPI(
    title="OpenID Connect avec Google",
    description="Authentification OpenID Connect utilisant Google OAuth2",
    version="1.0.0"
)

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

# Serializer pour générer des tokens sécurisés
serializer = URLSafeTimedSerializer(SECRET_KEY)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil avec interface HTML"""
    user = request.session.get('user')
    
    if user:
        user_info = f"""
        <div class="user-info">
            <img src="{user.get('picture')}" alt="Profile" style="border-radius: 50%; width: 50px; height: 50px;">
            <div>
                <strong>{user.get('name')}</strong>
                <p style="margin: 0; color: #666;">{user.get('email')}</p>
            </div>
        </div>
        """
        auth_button = '<a href="/auth/logout" class="btn btn-danger">Se déconnecter</a>'
    else:
        user_info = '<p class="text-muted">Non connecté</p>'
        auth_button = '<a href="/auth/login" class="btn btn-primary">Se connecter avec Google</a>'
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenID Connect - FastAPI</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .navbar {{
                background: white;
                padding: 1rem 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
            }}
            .navbar h1 {{ 
                color: #667eea; 
                font-size: 1.5rem;
            }}
            .nav-links {{ 
                display: flex; 
                gap: 1rem; 
                align-items: center;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .card {{
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }}
            .user-info {{
                display: flex;
                gap: 1rem;
                align-items: center;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 1rem;
            }}
            .endpoints {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }}
            .endpoint {{
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .endpoint h3 {{
                color: #667eea;
                margin-bottom: 0.5rem;
                font-size: 1rem;
            }}
            .endpoint p {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }}
            .endpoint code {{
                background: #e9ecef;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-size: 0.85rem;
            }}
            .btn {{
                padding: 0.6rem 1.2rem;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s;
                display: inline-block;
            }}
            .btn-primary {{
                background: #667eea;
                color: white;
            }}
            .btn-primary:hover {{
                background: #5568d3;
                transform: translateY(-2px);
            }}
            .btn-danger {{
                background: #dc3545;
                color: white;
            }}
            .btn-danger:hover {{
                background: #c82333;
            }}
            .btn-secondary {{
                background: #6c757d;
                color: white;
                font-size: 0.85rem;
                padding: 0.4rem 0.8rem;
            }}
            .text-muted {{ color: #6c757d; }}
            .badge {{
                background: #28a745;
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
            }}
            .badge-warning {{
                background: #ffc107;
                color: #000;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <nav class="navbar">
                <h1>🔐 OpenID Connect - FastAPI</h1>
                <div class="nav-links">
                    <a href="/docs" class="btn btn-secondary">📚 API Docs</a>
                    {auth_button}
                </div>
            </nav>
            
            <div class="card">
                <h2 style="margin-bottom: 1rem;">État de connexion</h2>
                {user_info}
            </div>
            
            <div class="card">
                <h2 style="margin-bottom: 1rem;">Endpoints disponibles</h2>
                <div class="endpoints">
                    <div class="endpoint">
                        <h3>🏠 Accueil</h3>
                        <p>Page d'accueil avec interface</p>
                        <code>GET /</code>
                    </div>
                    
                    <div class="endpoint">
                        <h3>🔑 Connexion</h3>
                        <p>Initier l'authentification Google</p>
                        <code>GET /auth/login</code>
                        <br><br>
                        <a href="/auth/login" class="btn btn-secondary">Tester</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3>🚪 Déconnexion</h3>
                        <p>Se déconnecter de la session</p>
                        <code>GET /auth/logout</code>
                        {'<br><br><a href="/auth/logout" class="btn btn-secondary">Tester</a>' if user else ''}
                    </div>
                    
                    <div class="endpoint">
                        <h3>👤 Infos utilisateur</h3>
                        <p>Récupérer les données de l'utilisateur</p>
                        <code>GET /api/user</code>
                        {'<span class="badge">Authentifié</span>' if user else '<span class="badge badge-warning">Auth requise</span>'}
                        <br><br>
                        <a href="/api/user" class="btn btn-secondary">Tester</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3>🔒 Route protégée</h3>
                        <p>Exemple de ressource protégée</p>
                        <code>GET /api/protected</code>
                        {'<span class="badge">Authentifié</span>' if user else '<span class="badge badge-warning">Auth requise</span>'}
                        <br><br>
                        <a href="/api/protected" class="btn btn-secondary">Tester</a>
                    </div>
                    
                    <div class="endpoint">
                        <h3>❤️ Health Check</h3>
                        <p>Vérifier l'état du serveur</p>
                        <code>GET /health</code>
                        <br><br>
                        <a href="/health" class="btn btn-secondary">Tester</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/auth/login")
async def login(request: Request):
    """Initier le flux d'authentification OpenID Connect avec Google"""
    redirect_uri = GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """
    Callback après authentification Google.
    Récupère le token et les informations utilisateur.
    """
    try:
        # Échanger le code d'autorisation contre un token
        token = await oauth.google.authorize_access_token(request)
        
        # Récupérer les informations utilisateur via OpenID Connect
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Impossible de récupérer les informations utilisateur")
        
        # Stocker les informations utilisateur dans la session
        request.session['user'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'sub': user_info.get('sub'),  # Subject identifier (ID unique Google)
            'email_verified': user_info.get('email_verified')
        }
        
        # Rediriger vers la page d'accueil
        return RedirectResponse(url='/')
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'authentification: {str(e)}")


@app.get("/auth/logout")
async def logout(request: Request):
    """Déconnecter l'utilisateur"""
    request.session.clear()
    return JSONResponse({
        "message": "Déconnexion réussie",
        "authenticated": False
    })


@app.get("/api/user")
async def get_user(request: Request):
    """Récupérer les informations de l'utilisateur connecté"""
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")
    return user


@app.get("/api/protected")
async def protected_route(request: Request):
    """Exemple de route protégée nécessitant une authentification"""
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Authentification requise")
    
    return {
        "message": "Accès autorisé à cette ressource protégée",
        "user_email": user.get('email')
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
