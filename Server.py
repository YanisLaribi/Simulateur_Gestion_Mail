"""\
GLO-2000 Travail pratique 4 - Serveur 2025
Noms et numéros étudiants: Yanis (537243471), Tiavintsoa (537067249), Felix (537298959)
-
-
-
"""
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import re

import select
import socket
import sys

import glosocket
import gloutils


class Server:
    """Serveur mail @glo2000.ca 2025."""

    def __init__(self) -> None:
        """
        Prépare le socket du serveur `_server_socket`
        et le met en mode écoute.

        Prépare les attributs suivants:
        - `_client_socs` une liste des sockets clients.
        - `_logged_users` un dictionnaire associant chaque
            socket client à un nom d'utilisateur.

        S'assure que les dossiers de données du serveur existent.
        """
        # self._server_socket
        # self._client_socs
        # self._logged_users
        # ...

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind(("localhost", gloutils.APP_PORT))
            self._server_socket.listen()
        except glosocket.GLOSocketError:
            sys.exit(1)

        self._client_socs = []
        self._logged_users = dict()

        dossier = pathlib.Path(gloutils.SERVER_DATA_DIR, gloutils.SERVER_LOST_DIR)
        if not dossier.exists():
            os.mkdir(gloutils.SERVER_DATA_DIR)
            os.mkdir(dossier)

    def cleanup(self) -> None:
        """Ferme toutes les connexions résiduelles."""
        for client_soc in self._client_socs:
            client_soc.close()
        self._server_socket.close()

    def _accept_client(self) -> None:
        """Accepte un nouveau client."""
        (client_socket, _) = self._server_socket.accept()
        self._client_socs.append(client_socket)

    def _remove_client(self, client_soc: socket.socket) -> None:
        """Retire le client des structures de données et ferme sa connexion."""
        if client_soc in self._client_socs:
            self._client_socs.remove(client_soc)
        if client_soc in self._logged_users:
            self._logged_users.pop(client_soc, None)
        client_soc.close()


    def _create_account(
        self, client_soc: socket.socket, payload: gloutils.AuthPayload
    ) -> gloutils.GloMessage:
        """
        Crée un compte à partir des données du payload.

        Si les identifiants sont valides, créee le dossier de l'utilisateur,
        associe le socket au nouvel utilisateur et retourne un succès,
        sinon retourne un message d'erreur.
        """

        user_name = payload.get("username").lower()
        psw = payload.get("password")

        # Vérification du nom d'utilisateur
        if not re.search(r"^[\w.-]+$", user_name):
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message="ERREUR : nom d'utilisateur non valide\n"
                ),
            )
        else:
            print("Nom d'utilisateur est valide")

        # Chemin du dossier parent
        chemin_parent = pathlib.Path(gloutils.SERVER_DATA_DIR)
        chemin_parent.mkdir(parents=True, exist_ok=True)

        # Vérifier si l'utilisateur existe déjà
        for element in chemin_parent.iterdir():
            if element.name.lower() == user_name.lower():
                return gloutils.GloMessage(
                    header=gloutils.Headers.ERROR,
                    payload=gloutils.ErrorPayload(
                        error_message="Erreur: l'utilisateur existe déjà\n"
                    ),
                )

        # Vérification du mot de passe (IMPORTANT : avant création du dossier)
        if (
            not re.search(r"[a-z]", psw)     # minuscule
            or not re.search(r"[A-Z]", psw) # majuscule
            or not re.search(r"[0-9]", psw) # chiffre
            or len(psw) < 10
        ):
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message=(
                        "Erreur: le mot de passe doit avoir :\n"
                        "  -au moins 1 minuscule\n"
                        "  -au moins 1 majuscule\n"
                        "  -au moins 1 chiffre\n"
                        "  -une taille >= 10\n"
                    )
                ),
            )

        # Créer le dossier utilisateur APRÈS TOUTES LES VALIDATIONS
        chemin_client = chemin_parent / user_name
        chemin_client.mkdir()
        print("Dossier créé avec succès !")
        # Créer le dossier emails pour l'utilisateur
        (chemin_client / "emails").mkdir()


        # Hachage et ajout du mot de passe
        psw_hashed = hashlib.sha3_512(psw.encode("utf-8")).hexdigest()
        password_file = chemin_client / gloutils.PASSWORD_FILENAME

        with open(password_file, "w", encoding="utf-8") as fi:
            fi.write(psw_hashed)

        # Associer user/socket
        self._logged_users[client_soc] = user_name

        return gloutils.GloMessage(header=gloutils.Headers.OK)


    def _login(
            self, client_soc: socket.socket, payload: gloutils.AuthPayload
    ) -> gloutils.GloMessage:
        """
        Vérifie que les données fournies correspondent à un compte existant.

        Si les identifiants sont valides, associe le socket à l'utilisateur et
        retourne un succès, sinon un message d'erreur.
        """

        # Récupérer le nom d'utilisateur et le mot de passe
        user = payload.get("username")
        pwd = payload.get("password")

        path = pathlib.Path(gloutils.SERVER_DATA_DIR)

        # Vérifier si le dossier utilisateur existe
        bool = False
        for dossier in path.iterdir():
            if dossier.is_dir() and dossier.name.lower() == user.lower():
                user = dossier.name
                bool = True
                break

        if not bool:
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message="Erreur: L'utilisateur n'existe pas\n"
                ),
            )

        # Hachage du mot de passe fourni
        psw_hashed = hashlib.sha3_512(pwd.encode("utf-8")).hexdigest()

        # Fichier contenant le mot de passe enregistré
        p = pathlib.Path(gloutils.SERVER_DATA_DIR, user, gloutils.PASSWORD_FILENAME)

        # Vérifier si le fichier mot de passe existe (sécurité)
        if not p.exists():
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message="Erreur: compte corrompu (fichier mdp manquant)\n"
                ),
            )

        # Vérifier le mot de passe
        with open(p, "r", encoding="utf-8") as f:
            stored_hash = f.read().strip()

            if not hmac.compare_digest(stored_hash, psw_hashed):
                return gloutils.GloMessage(
                    header=gloutils.Headers.ERROR,
                    payload=gloutils.ErrorPayload(
                        error_message="Erreur: mot de passe incorrect\n"
                    ),
                )

        # Associer l'utilisateur au socket
        self._logged_users[client_soc] = user

        return gloutils.GloMessage(header=gloutils.Headers.OK)

    def _logout(self, client_soc: socket.socket) -> None:
        """Déconnecte un utilisateur."""
        self._logged_users.pop(client_soc)

    def _get_email_list(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère la liste des courriels de l'utilisateur associé au socket.
        Les éléments de la liste sont construits à l'aide du gabarit
        SUBJECT_DISPLAY et sont ordonnés du plus récent au plus ancien.



        Une absence de courriel n'est pas une erreur, mais une liste vide.
        """

        nom = self._logged_users[client_soc]
        dossier_mail = pathlib.Path(gloutils.SERVER_DATA_DIR, nom, "emails")

        # Si aucun dossier, aucun mail
        if not dossier_mail.exists():
            return gloutils.GloMessage(
                header=gloutils.Headers.OK,
                payload=gloutils.EmailListPayload(email_list=[]),
            )

        Liste_mail = []

        # Lire tous les fichiers dans "emails/"
        for fichier in dossier_mail.iterdir():
            if fichier.is_file():
                with open(fichier, "r", encoding="utf-8") as f:
                    contenu = f.read()
                    if contenu:
                        Liste_mail.append(json.loads(contenu))

        # Pas de courriel = liste vide (pas une erreur)
        if len(Liste_mail) == 0:
            return gloutils.GloMessage(
                header=gloutils.Headers.OK,
                payload=gloutils.EmailListPayload(email_list=[]),
            )

        Liste_mail = sorted(
            Liste_mail,
            key=lambda e: datetime.datetime.strptime(
                e.get("date"), "%a, %d %b %Y %H:%M:%S %z"
            ),
        reverse = True
        )

        compteur = 1
        Liste_mail_formate = []
        for i in Liste_mail:

            Liste_mail_formate.append(
                gloutils.SUBJECT_DISPLAY.format(
                number= compteur,
                sender=i.get("sender"),
                subject=i.get("subject"),
                date=i.get("date"),
            )
            )
            compteur += 1

        return gloutils.GloMessage(
            header=gloutils.Headers.OK,
            payload=gloutils.EmailListPayload(email_list=Liste_mail_formate))

    def _get_email(
        self, client_soc: socket.socket, payload: gloutils.EmailChoicePayload
    ) -> gloutils.GloMessage:
        """
        Récupère le contenu de l'email dans le dossier de l'utilisateur associé
        au socket.
        """


        # Récupérer le numéro choisi
        choice = int(payload.get("choice"))

        # Récupérer le nom utilisateur
        user = self._logged_users[client_soc]
        dossier = pathlib.Path(gloutils.SERVER_DATA_DIR, user, "emails")

        # Charger tous les emails (un fichier par email)
        emails = []
        for fichier in dossier.iterdir():
            if fichier.is_file():
                with open(fichier, "r", encoding="utf-8") as f:
                    emails.append(json.loads(f.read()))

        # S'il n'y a aucun email
        if not emails:
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(error_message="Aucun courriel.\n")
            )

        # Trier du plus récent au plus ancien
        emails = sorted(
            emails,
            key=lambda e: datetime.datetime.strptime(
                e["date"], "%a, %d %b %Y %H:%M:%S %z"
            ),
            reverse=True
        )



        if choice < 1 or choice > len(emails):
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(error_message="Numéro invalide.\n")
            )

        email = emails[choice - 1]

        # Construire EmailContentPayload CORRECT selon gloutils
        payload_email: gloutils.EmailContentPayload = {
            "sender": email["sender"],
            "destination": email["destination"],
            "subject": email["subject"],
            "date": email["date"],
            "content": email["content"],  # ← attention : DOIT s’appeler "content"
        }

        # Retourner le message final
        return gloutils.GloMessage(
            header=gloutils.Headers.OK,
            payload=payload_email
        )

    def _get_stats(self, client_soc: socket.socket) -> gloutils.GloMessage:
        """
        Récupère le nombre de courriels et la taille du dossier et des fichiers
        de l'utilisateur associé au socket.
        """

        user = self._logged_users[client_soc]
        path = pathlib.Path(gloutils.SERVER_DATA_DIR, user, "emails")

        # Aucun dossier donc aucun courriel
        if not path.exists():
            return gloutils.GloMessage(
                header=gloutils.Headers.OK,
                payload=gloutils.StatsPayload(count=0, size=0)
            )

        total_size = 0
        count = 0

        # Parcourir uniquement les fichiers (chaque email)
        for entry in os.scandir(path):
            if entry.is_file():
                count += 1
                total_size += entry.stat().st_size  # taille du fichier

        # Construire le payload
        stats_payload: gloutils.StatsPayload = {
            "count": count,
            "size": total_size
        }

        return gloutils.GloMessage(
            header=gloutils.Headers.OK,
            payload=stats_payload
        )

    def _send_email(self, payload: gloutils.EmailContentPayload) -> gloutils.GloMessage:
        """
        Détermine si l'envoi est interne ou externe et:
        - Si l'envoi est interne, écris le message tel quel dans le dossier
        du destinataire.
        - Si le destinataire n'existe pas, place le message dans le dossier
        SERVER_LOST_DIR et considère l'envoi comme un échec.
        - Si le destinataire est externe, considère l'envoi comme un échec.

        Retourne un messange indiquant le succès ou l'échec de l'opération.
        """
        # split l'email
        destInfos = payload.get("destination").split("@")

        # nom de l'user = la partie avant "."
        destUser = destInfos[0].split(".")[0].lower()

        # chemin vers le dossier emails du destinataire
        destDir = pathlib.Path(
            gloutils.SERVER_DATA_DIR, destUser, "emails"
        )

        # DESTINATAIRE EXTERNE
        if destInfos[-1] != gloutils.SERVER_DOMAIN:
            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message="Erreur: Le destinataire est externe\n"
                ),
            )

        # DESTINATAIRE INTERNE MAIS N’EXISTE PAS
        if not destDir.exists():
            lostDir = pathlib.Path(gloutils.SERVER_DATA_DIR, gloutils.SERVER_LOST_DIR)
            lostDir.mkdir(exist_ok=True)

            lost_file = lostDir / "lost_emails"
            with open(lost_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")

            return gloutils.GloMessage(
                header=gloutils.Headers.ERROR,
                payload=gloutils.ErrorPayload(
                    error_message="Erreur: destinataire introuvable\n"
                ),
            )

        # DESTINATAIRE INTERNE VALIDÉ
        destDir.mkdir(exist_ok=True)

        # écrire dans le fichier emails (chaque ligne = un email JSON)
        email_file = destDir / f"email_{datetime.datetime.utcnow().timestamp()}.json"
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload))


        return gloutils.GloMessage(header=gloutils.Headers.OK)

    def run(self):
        """Point d'entrée du serveur."""
        waiters = []
        while True:
            # Select readable sockets
            result = select.select(self._client_socs + [self._server_socket],
                                   [],
                                   [])
            waiters = result[0]
            for waiter in waiters:
                if waiter == self._server_socket:

                    self._accept_client()
                    print("New client accepted!")
                else:
                    data = str()
                    try:
                        data = glosocket.recv_mesg(waiter)
                        if data:
                            packet = json.loads(data)
                            print(packet)
                            match packet:
                                case {"header": gloutils.Headers.AUTH_REGISTER}:
                                    glosocket.send_mesg(
                                        waiter,
                                        json.dumps(self._create_account(waiter, packet['payload']))
                                    )
                                    continue
                                case {"header": gloutils.Headers.AUTH_LOGIN}:
                                    glosocket.send_mesg(
                                        waiter, json.dumps(self._login(waiter, packet['payload']))
                                    )
                                    continue
                                case {"header": gloutils.Headers.AUTH_LOGOUT}:
                                    self._logout(waiter)
                                    continue
                                case {"header": gloutils.Headers.BYE}:
                                    self._remove_client(waiter)
                                    continue
                                case {"header": gloutils.Headers.INBOX_READING_CHOICE}:
                                    glosocket.send_mesg(
                                        waiter, json.dumps(self._get_email(waiter, packet['payload']))
                                    )
                                    continue
                                case {"header": gloutils.Headers.INBOX_READING_REQUEST}:
                                    glosocket.send_mesg(
                                        waiter, json.dumps(self._get_email_list(waiter))
                                    )
                                    continue
                                case {"header": gloutils.Headers.EMAIL_SENDING}:
                                    glosocket.send_mesg(
                                        waiter, json.dumps(self._send_email(packet['payload']))
                                    )
                                    continue
                                case {"header": gloutils.Headers.STATS_REQUEST}:
                                    glosocket.send_mesg(
                                        waiter, json.dumps(self._get_stats(waiter))
                                    )
                                    continue
                    except glosocket.GLOSocketError as err:
                        print(err)
                        self._remove_client(waiter)


# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT


def _main() -> int:
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
