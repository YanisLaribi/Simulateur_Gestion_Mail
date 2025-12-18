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

