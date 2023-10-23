import multiprocessing

# Le chemin du répertoire racine de votre projet Django
chdir = '/home/toto/GRJOJ'

# Nom du fichier WSGI de votre projet
module = 'GRJOJ.wsgi:application'

# Nombre de travailleurs Gunicorn
workers = multiprocessing.cpu_count() * 2 + 1

# Adresse IP et port sur lequel Gunicorn écoutera les requêtes
bind = '127.0.0.1:8000'  # Vous pouvez personnaliser l'adresse et le port

# Fichier de journalisation
errorlog = '/var/log/gunicorn/error.log'
accesslog = '/var/log/gunicorn/access.log'

# Démarrer Gunicorn en arrière-plan
daemon = True
