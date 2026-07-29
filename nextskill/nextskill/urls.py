"""
URL configuration for nextskill project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings  # accès à DEBUG et MEDIA_URL/MEDIA_ROOT
from django.conf.urls.static import static  # génère les routes pour servir les fichiers médias en développement
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),  # interface d'administration Django native
    path('', include('accounts.urls')),  # connexion, inscription, déconnexion
    path('', include('courses.urls')),  # catalogue, détail cours, leçons, dashboards formateur/admin
    path('', include('orders.urls')),  # panier et paiement fictif
    path('', include('enrollments.urls')),  # tableau de bord étudiant ("Mon apprentissage")
    path('', include('quizzes.urls')),  # passage des quiz
    path('', include('pages.urls')),  # pages publiques (accueil, services, à propos, contact)
]

if settings.DEBUG:
    # sert les fichiers uploadés (photos de couverture, vidéos/pdf de leçons) directement via runserver ;
    # en production, ce serait le serveur web (nginx, etc.) qui s'en chargerait, pas Django
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
