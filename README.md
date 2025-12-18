# 📧 Simulateur de gestion de courriels — TP4 (GLO-2000)

Ce projet consiste en l’implémentation d’un **système de courriel client-serveur** simulant un service interne de messagerie (`@glo2000.ca`).  
Il a été réalisé dans le cadre du **TP4 du cours GLO-2000 – Réseaux pour ingénieurs** à l’Université Laval.

Le système repose sur une architecture **client / serveur TCP (IPv4)** et permet :
- la création de comptes utilisateurs,
- l’authentification sécurisée,
- l’envoi et la réception de courriels internes,
- la consultation des messages et des statistiques,
- la gestion simultanée de plusieurs clients.

---

## 🏫 Contexte académique

- **Cours** : GLO-2000 – Réseaux pour ingénieurs  
- **Université** : Université Laval  
- **Session** : Automne 2025  
- **Travail pratique** : TP4 – Serveur de courriels  

---

## ⚙️ Fonctionnalités principales

### 👤 Gestion des utilisateurs
- Création de comptes avec validation stricte :
  - nom d’utilisateur valide (`a-z`, `A-Z`, `0-9`, `.`, `_`, `-`)
  - unicité insensible à la casse
  - mot de passe sécurisé (≥ 10 caractères, majuscule, minuscule, chiffre)
- Authentification sécurisée avec mot de passe haché (`SHA3-512`)
- Déconnexion propre et gestion des sessions

### 📬 Gestion des courriels
- Envoi de courriels internes (`@glo2000.ca`)
- Consultation de la boîte de réception
- Lecture détaillée d’un courriel
- Stockage persistant des messages en format JSON
- Gestion des courriels perdus (destinataire inexistant)

### 📊 Statistiques
- Nombre total de messages
- Taille du dossier utilisateur (en octets)

### 🔌 Réseau
- Communication **TCP / IPv4**
- Gestion de plusieurs clients simultanément via `select`
- Protocole de communication basé sur `glosocket` et `gloutils`

---

## 🗂️ Structure du projet

```text
Simulateur_Gestion_Mail/
│
├── Client.py        # Client de messagerie
├── Server.py        # Serveur de courriels
├── glosocket.py         # Module réseau fourni (obligatoire)
├── gloutils.py          # Constantes, gabarits et structures
│
├── server_data/         # Données persistantes du serveur
│   ├── lost/            # Courriels non livrés
│   └── <utilisateurs>/ # Dossiers utilisateurs
│
└── README.md
```
---

## ▶️ Exécution du projet

### 1️⃣ Lancer le serveur
```bash
python TP4_server.py
```

### 2️⃣ Lancer un client
```bash
python TP4_client.py -d 127.0.0.1
```

---

## 🧭 Menus disponibles

### Menu de connexion
- Créer un compte
- Se connecter
- Quitter

### Menu principal
- Consultation de courriels
- Envoi de courriels
- Statistiques
- Se déconnecter

---

## 🔐 Sécurité et bonnes pratiques

- Hachage sécurisé des mots de passe (`hashlib.sha3_512`)
- Comparaison sécurisée (`hmac.compare_digest`)
- Aucune utilisation de `except:` générique
- Validation stricte des entrées utilisateur
- Séparation claire client / serveur

---

## 🛠️ Technologies utilisées

- **Langage** : Python 3
- **Réseau** : sockets TCP (IPv4)
- **Modules standards** :
  - `socket`, `select`
  - `hashlib`, `hmac`
  - `json`, `os`, `pathlib`
  - `getpass`
- **Modules fournis** :
  - `glosocket`
  - `gloutils`

---

## ⚠️ Contraintes importantes

- Le projet est conçu pour fonctionner **dans la machine virtuelle du cours**
- Les modules `glosocket` et `gloutils` **ne doivent pas être modifiés**
- Le format des messages doit être respecté strictement
- Toute fonctionnalité non fonctionnelle dans la VM est considérée comme absente

---

## 👨‍💻 Auteur

- **Yanis Laribi**  
- Étudiant en génie logiciel  
- Université Laval  

---

## 📄 Licence

Projet académique réalisé à des fins pédagogiques dans le cadre du cours **GLO-2000**.  
Toute réutilisation doit respecter les règles et politiques académiques associées.
