# OpenID Connect avec Google et FastAPI

Cette application implémente l'authentification OpenID Connect en utilisant Google comme fournisseur d'identité avec Python FastAPI et JWT (JSON Web Tokens).

## Caractéristiques

- 🔐 Authentification OpenID Connect avec Google OAuth2
- 🎫 JWT pour la gestion des sessions sécurisées
- 🎨 Interface web moderne avec Jinja2 templates
- 🔒 Routes API protégées avec vérification JWT
- 📝 Documentation API interactive (Swagger/ReDoc)
- ✅ Cookie HttpOnly pour stocker le JWT (protection XSS)

## Prérequis

- Python 3.8+
- Un projet Google Cloud Platform avec OAuth 2.0 configuré

## Configuration Google Cloud Platform

### 1. Créer un projet Google Cloud
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant

### 2. Activer l'API Google+ 
1. Dans le menu, allez à **APIs & Services** > **Library**
2. Recherchez "Google+ API" et activez-la

### 3. Configurer l'écran de consentement OAuth
1. Allez à **APIs & Services** > **OAuth consent screen**
2. Choisissez "External" (ou "Internal" si vous êtes dans Google Workspace)
3. Remplissez les informations requises :
   - Nom de l'application
   - Email de support utilisateur
   - Domaines autorisés (optionnel pour le développement local)
4. Ajoutez les scopes : `openid`, `email`, `profile`
5. Sauvegardez

### 4. Créer des identifiants OAuth 2.0
1. Allez à **APIs & Services** > **Credentials**
2. Cliquez sur **Create Credentials** > **OAuth client ID**
3. Choisissez "Web application"
4. Configurez :
   - **Nom** : Votre nom d'application
   - **URIs de redirection autorisés** : 
     ```
     http://localhost:8000/auth/callback
     ```
   - **Origines JavaScript autorisées** (optionnel) :
     ```
     http://localhost:8000
     ```
5. Cliquez sur **Create**
6. Copiez le **Client ID** et le **Client Secret**

## Installation

### 1. Créer un environnement virtuel (recommandé)

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
.\venv\Scripts\Activate.ps1

# Activer l'environnement (Linux/Mac)
source venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et remplacez par vos valeurs :

```env
GOOGLE_CLIENT_ID=votre-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=votre-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
SECRET_KEY=generez-une-cle-secrete-longue-et-aleatoire
APP_HOST=0.0.0.0
APP_PORT=8000
```

**Important** : Pour générer une clé secrète sécurisée :

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Lancement de l'application

```bash
# Méthode 1 : avec uvicorn directement
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Méthode 2 : avec le script Python
python main.py
```

L'application sera accessible sur : http://localhost:8000

## Endpoints disponibles

### Endpoints publics

- **GET /** : Page d'accueil avec interface web moderne
- **GET /auth/login** : Initie le flux d'authentification Google
- **GET /auth/callback** : Callback OAuth2 (utilisé par Google)
- **GET /auth/logout** : Déconnexion et suppression du JWT
- **GET /health** : Vérification de santé de l'application

### Endpoints protégés (JWT requis)

- **GET /api/user** : Récupère les informations de l'utilisateur depuis le JWT
- **GET /api/protected** : Exemple de route protégée avec vérification JWT

**Note** : Les routes protégées lisent le JWT depuis le cookie `access_token` (HttpOnly).

## Flux d'authentification avec JWT

1. L'utilisateur clique sur "Se connecter avec Google" (`/auth/login`)
2. Redirection vers la page de connexion Google
3. L'utilisateur s'authentifie et accepte les permissions
4. Google redirige vers `/auth/callback` avec un code d'autorisation
5. FastAPI échange le code contre un token d'accès (serveur à serveur)
6. FastAPI récupère les informations utilisateur via OpenID Connect
7. **FastAPI crée un JWT** contenant les données utilisateur (email, nom, photo)
8. Le JWT est stocké dans un **cookie HttpOnly** (protection XSS)
9. L'utilisateur est redirigé vers la page d'accueil
10. Les requêtes suivantes incluent automatiquement le cookie JWT

## Tester l'application

### 1. Tester avec un navigateur

1. Ouvrez http://localhost:8000
2. Cliquez sur le lien de connexion ou allez sur http://localhost:8000/auth/login
3. Connectez-vous avec votre compte Google
4. Vous serez redirigé et verrez vos informations utilisateur

### 2. Tester avec curl

```bash
# Page d'accueil
curl http://localhost:8000/

# Vérifier le statut
curl http://localhost:8000/health

# Essayer d'accéder à une route protégée (devrait retourner 401)
curl http://localhost:8000/api/protected
```

### 3. Documentation interactive

FastAPI génère automatiquement une documentation interactive :

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## Structure du code

```
OpenID_Python/
├── main.py              # Application FastAPI avec gestion JWT
├── templates/
│   └── home.html        # Template Jinja2 pour l'interface web
├── requirements.txt     # Dépendances Python
├── .env                 # Configuration (à créer, non commité)
├── .env.example         # Template de configuration
├── .gitignore           # Fichiers à ignorer par git
└── README.md            # Ce fichier
```

## Architecture de sécurité

### JWT (JSON Web Tokens)

L'application utilise des JWT pour gérer l'authentification :

- **Algorithme** : HS256 (HMAC avec SHA-256)
- **Stockage** : Cookie HttpOnly (protection contre XSS)
- **Expiration** : 60 minutes configurable
- **Contenu** : email, name, picture, sub, email_verified, exp, iat

**Avantages du JWT** :
- ✅ Stateless : Pas besoin de stockage serveur des sessions
- ✅ Signature cryptographique : Impossible de modifier sans la clé
- ✅ Auto-expirant : Sécurité renforcée
- ✅ Portable : Peut être utilisé avec des microservices

## Sécurité

### Bonnes pratiques implémentées :

- ✅ Utilisation d'OpenID Connect (OAuth 2.0 + authentification)
- ✅ JWT avec signature HMAC-SHA256
- ✅ Cookies HttpOnly (protection XSS)
- ✅ SameSite=Lax (protection CSRF partielle)
- ✅ Variables d'environnement pour les secrets
- ✅ Validation des tokens côté serveur
- ✅ Expiration automatique des JWT
- ✅ Templates Jinja2 avec échappement automatique
- ✅ HTTPS fortement recommandé en production

### Pour la production :

1. **Utilisez HTTPS** :
   - Configurez un certificat SSL/TLS (Let's Encrypt)
   - Mettez à jour `GOOGLE_REDIRECT_URI` avec HTTPS
   - Ajoutez `secure=True` aux cookies en production

2. **Sécurisez votre SECRET_KEY** :
   - Utilisez un gestionnaire de secrets (AWS Secrets Manager, Azure Key Vault, etc.)
   - Ne committez JAMAIS le fichier `.env`
   - Rotation régulière de la clé

3. **Désactivez /docs en production** :
   ```python
   app = FastAPI(docs_url=None, redoc_url=None)  # Désactive la doc
   ```

4. **Configurez CORS** si nécessaire :
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://votredomaine.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

5. **Ajoutez des limites de taux (rate limiting)** pour prévenir les abus

6. **Whitelisting de domaines** (optionnel) :
   - Limiter l'authentification à certains domaines email
   - Exemple : `@votreentreprise.com` uniquement

7. **Monitoring et logging** :
   - Loggez les tentatives d'authentification
   - Surveillez les JWT expirés/invalides
   - Alertes sur les comportements suspects

## Informations utilisateur disponibles

Après authentification, le JWT contient les informations suivantes :

```json
{
  "email": "utilisateur@example.com",
  "name": "Nom Complet",
  "picture": "https://lh3.googleusercontent.com/...",
  "sub": "103159421008563748606",
  "email_verified": true,
  "exp": 1736789123,
  "iat": 1736785523
}
```

**Champs du JWT** :
- `email` : Adresse email de l'utilisateur
- `name` : Nom complet
- `picture` : URL de la photo de profil
- `sub` : Subject - Identifiant unique Google (immuable)
- `email_verified` : Email vérifié par Google
- `exp` : Expiration timestamp (60 minutes par défaut)
- `iat` : Issued at timestamp (date de création)

## Débogage

Si vous rencontrez des problèmes :

1. Vérifiez que les variables d'environnement sont correctement définies
2. Assurez-vous que l'URI de redirection dans Google Cloud correspond exactement à celle dans `.env`
3. Vérifiez les logs de l'application pour les erreurs
4. Testez avec `http://localhost:8000` (pas `http://127.0.0.1:8000`) pour éviter les problèmes de redirection

## Ressources

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Authlib](https://docs.authlib.org/)
- [OpenID Connect](https://openid.net/connect/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

## Licence

MIT
