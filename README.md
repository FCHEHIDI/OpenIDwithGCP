# OpenID Connect avec Google et FastAPI

Cette application implémente l'authentification OpenID Connect en utilisant Google comme fournisseur d'identité avec Python FastAPI.

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

### 1. Cloner et installer les dépendances

```bash
# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

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

- **GET /** : Page d'accueil, affiche le statut de connexion
- **GET /auth/login** : Initie le flux d'authentification Google
- **GET /auth/callback** : Callback OAuth2 (utilisé par Google)
- **GET /auth/logout** : Déconnexion de l'utilisateur
- **GET /health** : Vérification de santé de l'application

### Endpoints protégés (authentification requise)

- **GET /api/user** : Récupère les informations de l'utilisateur connecté
- **GET /api/protected** : Exemple de route protégée

## Flux d'authentification

1. L'utilisateur visite `/auth/login`
2. Il est redirigé vers la page de connexion Google
3. Après authentification, Google redirige vers `/auth/callback`
4. L'application échange le code d'autorisation contre un token
5. Les informations utilisateur sont stockées dans la session
6. L'utilisateur est redirigé vers la page d'accueil

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
├── main.py              # Application FastAPI principale
├── requirements.txt     # Dépendances Python
├── .env                 # Configuration (à créer)
├── .env.example         # Template de configuration
└── README.md           # Ce fichier
```

## Sécurité

### Bonnes pratiques implémentées :

- ✅ Utilisation d'OpenID Connect (OAuth 2.0 + authentification)
- ✅ Sessions sécurisées avec middleware de session
- ✅ Variables d'environnement pour les secrets
- ✅ Validation des tokens côté serveur
- ✅ HTTPS recommandé en production

### Pour la production :

1. **Utilisez HTTPS** :
   - Configurez un certificat SSL/TLS
   - Mettez à jour `GOOGLE_REDIRECT_URI` avec HTTPS

2. **Sécurisez votre SECRET_KEY** :
   - Utilisez un gestionnaire de secrets (AWS Secrets Manager, etc.)
   - Ne committez JAMAIS le fichier `.env`

3. **Configurez CORS** si nécessaire :
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

4. **Ajoutez des limites de taux (rate limiting)**

5. **Utilisez une base de données** pour stocker les sessions au lieu de la mémoire

## Informations utilisateur disponibles

Après authentification, les informations suivantes sont disponibles :

```json
{
  "email": "utilisateur@example.com",
  "name": "Nom Complet",
  "picture": "https://lh3.googleusercontent.com/...",
  "sub": "identifiant-unique-google",
  "email_verified": true
}
```

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
